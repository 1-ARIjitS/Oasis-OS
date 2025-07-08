import base64
import logging
import os
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import numpy as np
import requests
from gui_agents.s1.utils.common_utils import box_iou

logger = logging.getLogger("desktopenv.agent")


state_ns = "uri:deskat:state.at-spi.gnome.org"
component_ns = "uri:deskat:component.at-spi.gnome.org"


# Agent action decorator
def agent_action(func):
    func.is_agent_action = True
    return func


class GroundingAgent:
    def __init__(self, vm_version: str, top_app=None, top_app_only=True, ocr=True):
        self.vm_version = vm_version
        self.top_app = top_app
        self.top_app_only = top_app_only
        self.enable_ocr = ocr
        self.notes = []

        # Map of applications to ignore
        self.ignore_applications = {
            "kwin_x11",
            "kwin",
            "kscreenlocker_greet",
            "plasmashell",
            "kwin_wayland",
            "systemsettings",
            "kstart5",
        }

        # Preserve nodes for element lookup
        self.nodes = []
        # Handle potential error conditions
        self.index_out_of_range_flag = False

        # state of the system
        self.previous_obs = None

        # OCR
        self.similarity_threshold = 0.8
        self.all_elements_from_desktop = []
        self.all_elements_from_ocr = []

        # preserved elements for current round
        self.preserved_elements = []

        # text_linearization_length
        self.text_linearization_length = 3000

        # linearized_accessibility_tree
        self.linearized_accessibility_tree = ""

        # screenshot of current step
        self.screenshot = None

        # track if any applications opened/closed from previous round
        self.same_application_configuration = True

    def get_current_applications(self, obs):
        """Get list of current applications from the accessibility tree"""
        tree = obs.get("accessibility_tree")
        if tree is None:
            return []
        
        root = tree.getroot()
        if root is None:
            return []
            
        apps = []
        for item in root:
            app_name = item.get("name", "").replace("\\", "")
            if app_name:
                apps.append(app_name)
        return apps

    def check_new_apps(self, old_apps, new_apps):
        return set(old_apps) != set(new_apps)

    def find_active_applications(self, tree):
        # names of applications to keep TODO: soffice is a single application with all the isntances like impress, calc etc. being frames this will need to be dealt with separately
        if tree is None:
            return []
            
        root = tree.getroot()
        if root is None:
            return []
            
        to_keep = []
        for application in root:
            if (
                application.attrib.get("name", "") not in self.ignore_applications
                and application.attrib.get("name", "") != ""
            ):
                to_keep.append(application.attrib.get("name", ""))

        return to_keep

    def filter_active_app(self, tree):
        """Filter the tree to only keep the top app if top_app_only is True"""
        if not self.top_app_only or self.top_app is None or tree is None:
            return tree
            
        root = tree.getroot()
        if root is None:
            return tree
            
        # Remove all applications except the top app
        for application in list(root):
            if application.attrib.get("name", "") != self.top_app:
                root.remove(application)
        return tree

    def filter_nodes(self, tree, show_all=False):
        # created and populate a preserved nodes list which filters out unnecessary elements and keeps only those elements which are currently showing on the screen
        # TODO: include offscreen elements and then scroll to them before clicking
        if tree is None:
            return []
            
        root = tree.getroot()
        if root is None:
            return []
            
        preserved_nodes = []

        # TODO: a more optimal implementation
        for node in root.iter():
            # skip if the node doesn't have the necessary attributes
            if not all(
                key in node.attrib
                for key in [
                    f"{{{state_ns}}}enabled",
                    f"{{{component_ns}}}screencoord",
                    f"{{{component_ns}}}size",
                ]
            ):
                continue

            if show_all:
                if node.attrib.get(f"{{{state_ns}}}enabled") == "true":
                    screen_coords: Tuple[int, int] = eval(
                        node.get(
                            "{{{:}}}screencoord".format(component_ns), "(-1, -1)"
                        )
                    )
                    # TODO: double check the implementation
                    size: Tuple[int, int] = eval(
                        node.get("{{{:}}}size".format(component_ns), "(-1, -1)")
                    )

                    if (
                        screen_coords != (-1, -1)
                        and size != (-1, -1)
                        and screen_coords[0] >= 0
                        and screen_coords[1] >= 0
                        and size[0] > 0
                        and size[1] > 0
                        and screen_coords[0] + size[0] <= 1920
                        and screen_coords[1] + size[1] <= 1080
                    ):
                        preserved_nodes.append(node)
            else:
                # Check if the node is a clickable element (button, text field, etc.)
                if (
                    node.attrib.get(f"{{{state_ns}}}enabled") == "true"
                    and node.attrib.get(f"{{{state_ns}}}visible") == "true"
                    and node.attrib.get(f"{{{state_ns}}}showing") == "true"
                    and node.attrib.get("role") in clickable_roles
                ):
                    preserved_nodes.append(node)

        return preserved_nodes

    def linearize_tree(self, preserved_nodes):
        # TODO: Run an ablation to check if class and desc
        # linearized_accessibility_tree = ["id\ttag\tname\ttext\tclass\tdescription"]
        linearized_accessibility_tree = ["id\ttag\tname\ttext"]

        for idx, node in enumerate(preserved_nodes):
            # Extract node information
            role = node.attrib.get("role", "")
            name = node.attrib.get("name", "").replace("\n", " ").replace("\t", " ")
            text = node.text if node.text else ""
            text = text.replace("\n", " ").replace("\t", " ") if text else ""

            # class_name = node.attrib.get("class", "")
            # description = node.attrib.get("description", "")

            # Create linearized entry
            linearized_entry = f"{idx}\t{role}\t{name}\t{text}"
            linearized_accessibility_tree.append(linearized_entry)

        return "\n".join(linearized_accessibility_tree)

    def extract_elements_from_screenshot(self, screenshot) -> Dict:
        """Extract text elements from screenshot using OCR"""
        try:
            url = os.environ.get("OCR_SERVER_ADDRESS")
            
            if not url:
                print("Warning: OCR_SERVER_ADDRESS not set. OCR functionality will be disabled.")
                return {"error": "OCR SERVER ADDRESS NOT SET", "results": []}
                
            def send_image_to_ocr(screenshot) -> Dict:
                headers = {"Content-Type": "application/json"}
                data = {
                    "image": base64.b64encode(screenshot).decode("utf-8"),
                    "ocr_type": "paddle"
                }
                
                try:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.ConnectionError:
                    print(f"Error: Cannot connect to OCR server at {url}")
                    return {"error": "Cannot connect to OCR server", "results": []}
                except requests.exceptions.Timeout:
                    print("Error: OCR server request timed out after 30 seconds.")
                    return {"error": "OCR server request timed out", "results": []}
                except requests.exceptions.HTTPError as e:
                    print(f"Error: OCR server returned HTTP error: {e}")
                    return {"error": f"OCR server returned HTTP error: {e}", "results": []}
                except Exception as e:
                    print(f"Error: Unexpected error with OCR server: {e}")
                    return {"error": f"Unexpected error with OCR server: {e}", "results": []}

            return send_image_to_ocr(screenshot)
            
        except Exception as e:
            print(f"Error in extract_elements_from_screenshot: {e}")
            return {"error": str(e), "results": []}

    def add_ocr_elements(
        self, screenshot, linearized_accessibility_tree, preserved_nodes
    ):
        # Get the bounding boxes of the elements in the linearized accessibility tree
        if preserved_nodes:
            tree_bboxes = np.array(
                [
                    [
                        int(node.get(f"{{{component_ns}}}screencoord", "(0,0)").strip("()").split(",")[0]),
                        int(node.get(f"{{{component_ns}}}screencoord", "(0,0)").strip("()").split(",")[1]),
                        int(node.get(f"{{{component_ns}}}screencoord", "(0,0)").strip("()").split(",")[0]) + 
                        int(node.get(f"{{{component_ns}}}size", "(0,0)").strip("()").split(",")[0]),
                        int(node.get(f"{{{component_ns}}}screencoord", "(0,0)").strip("()").split(",")[1]) + 
                        int(node.get(f"{{{component_ns}}}size", "(0,0)").strip("()").split(",")[1])
                    ]
                    for node in preserved_nodes
                    if node.get(f"{{{component_ns}}}screencoord") and node.get(f"{{{component_ns}}}size")
                ],
                dtype=np.float32,
            )
        else:
            tree_bboxes = np.empty((0, 4), dtype=np.float32)

        try:
            ocr_results = self.extract_elements_from_screenshot(screenshot)
            if "error" in ocr_results:
                print(f"OCR Error: {ocr_results['error']}")
                return linearized_accessibility_tree.split("\n"), preserved_nodes
                
            if "results" not in ocr_results or not ocr_results["results"]:
                return linearized_accessibility_tree.split("\n"), preserved_nodes

            preserved_nodes_index = len(preserved_nodes)
            linearized_lines = linearized_accessibility_tree.split("\n")

            # Convert OCR boxes to numpy array
            ocr_boxes_array = np.array(
                [
                    [
                        int(box.get("left", 0)),
                        int(box.get("top", 0)),
                        int(box.get("right", 0)),
                        int(box.get("bottom", 0)),
                    ]
                    for _, _, box in ocr_results["results"]
                    if box and all(k in box for k in ["left", "top", "right", "bottom"])
                ],
                dtype=np.float32,
            )

            if len(ocr_boxes_array) == 0:
                return linearized_lines, preserved_nodes

            # Calculate max IOUs efficiently
            if len(tree_bboxes) > 0:
                max_ious = box_iou(tree_bboxes, ocr_boxes_array).max(axis=0)
            else:
                max_ious = np.zeros(len(ocr_boxes_array))

            # Process boxes with low IOU
            for idx, ((_, content, box), max_iou) in enumerate(
                zip(ocr_results["results"], max_ious)
            ):
                if max_iou < 0.1 and box and content:
                    x1 = int(box.get("left", 0))
                    y1 = int(box.get("top", 0))
                    x2 = int(box.get("right", 0))
                    y2 = int(box.get("bottom", 0))

                    linearized_lines.append(
                        f"{preserved_nodes_index}\tButton\t\t{content}"
                    )

                    # Create a pseudo-node for OCR elements
                    ocr_node = {
                        "position": (x1, y1),
                        "size": (x2 - x1, y2 - y1),
                        "role": "Button",
                        "name": "",
                        "text": content,
                    }
                    preserved_nodes.append(ocr_node)
                    preserved_nodes_index += 1

        except Exception as e:
            print(f"Error in add_ocr_elements: {e}")

        return linearized_lines, preserved_nodes

    def linearize_and_annotate_tree(self, obs, show_all=False):
        """Convert accessibility tree to linearized format with OCR elements"""
        tree = obs.get("accessibility_tree")
        if tree is None:
            self.nodes = []
            return ""

        # Filter to active applications
        to_keep = self.find_active_applications(tree)
        
        # Remove applications which are not included in the to_keep list
        if not show_all:
            root = tree.getroot()
            if root is not None:
                for application in list(root):
                    if application.attrib.get("name", "") not in to_keep:
                        root.remove(application)

        # Save tree for debugging
        # from datetime import datetime
        # ET.dump(tree.getroot())

        # Filter to top app if specified
        tree = self.filter_active_app(tree)

        # Get preserved nodes
        preserved_nodes = self.filter_nodes(tree, show_all)

        # Convert to linearized format
        linearized_tree = self.linearize_tree(preserved_nodes)

        # Add OCR elements if enabled
        if self.enable_ocr and "screenshot" in obs:
            linearized_lines, preserved_nodes = self.add_ocr_elements(
                obs["screenshot"], linearized_tree, preserved_nodes
            )
            linearized_tree = "\n".join(linearized_lines)

        # Store for element lookup
        self.nodes = preserved_nodes
        self.linearized_accessibility_tree = linearized_tree

        return linearized_tree

    def find_element(self, element_id):
        """Find element by ID from preserved nodes"""
        if not self.nodes:
            print("No elements found in the accessibility tree.")
            raise IndexError("No elements to select.")
        
        try:
            if isinstance(self.nodes[element_id], dict):
                # OCR element
                return self.nodes[element_id]
            else:
                # XML element - convert to dict format
                node = self.nodes[element_id]
                screen_coords_str = node.get(f"{{{component_ns}}}screencoord", "(0,0)")
                size_str = node.get(f"{{{component_ns}}}size", "(0,0)")
                
                try:
                    coords = eval(screen_coords_str)
                    size = eval(size_str)
                except:
                    coords = (0, 0)
                    size = (0, 0)
                
                return {
                    "position": coords,
                    "size": size,
                    "role": node.attrib.get("role", ""),
                    "name": node.attrib.get("name", ""),
                    "text": node.text if node.text else "",
                }
        except IndexError:
            print("The index of the selected element was out of range.")
            self.index_out_of_range_flag = True
            return self.find_element(0)

    @agent_action
    def click(
        self,
        element_id: int,
        num_clicks: int = 1,
        button_type: str = "left",
        hold_keys: List = [],
    ):
        """Click on the element
        Args:
            element_id:int, ID of the element to click on
            num_clicks:int, number of times to click the element
            button_type:str, which mouse button to press can be "left", "middle", or "right"
            hold_keys:List, list of keys to hold while clicking
        """
        element = self.find_element(element_id)
        coordinates = element["position"]
        size = element["size"]

        # Calculate the center of the element
        x = int(coordinates[0] + size[0] // 2)
        y = int(coordinates[1] + size[1] // 2)

        command = "import pyautogui; "

        # Add hold keys
        for k in hold_keys:
            command += f"pyautogui.keyDown({repr(k)}); "
        
        command += f"pyautogui.click({x}, {y}, clicks={num_clicks}, button={repr(button_type)}); "
        
        # Release hold keys
        for k in hold_keys:
            command += f"pyautogui.keyUp({repr(k)}); "
        
        return command

    @agent_action
    def switch_window(self):
        """Switch to the next window using Alt+Tab"""
        return "import pyautogui; pyautogui.hotkey('alt', 'tab')"

    @agent_action
    def type(
        self,
        text: str,
        element_id: Optional[int] = None,
        overwrite: bool = False,
        enter: bool = False,
    ):
        """Type text into the element
        Args:
            text:str the text to type
            element_id:int ID of the element to type into. If not provided, typing will start at the current cursor location.
            overwrite:bool Assign it to True if the text should overwrite the existing text, otherwise assign it to False. Using this argument clears all text in an element.
            enter:bool Assign it to True if the enter key should be pressed after typing the text, otherwise assign it to False.
        """
        command = "import pyautogui; "
        
        if element_id is not None:
            try:
                element = self.find_element(element_id)
                coordinates = element["position"]
                size = element["size"]
                
                x = int(coordinates[0] + size[0] // 2)
                y = int(coordinates[1] + size[1] // 2)
                
                command += f"pyautogui.click({x}, {y}); "
            except (IndexError, KeyError, AttributeError):
                pass  # Continue without clicking if element not found

        if overwrite:
            command += "pyautogui.hotkey('ctrl', 'a'); pyautogui.press('backspace'); "

        command += f"pyautogui.write({repr(text)}); "

        if enter:
            command += "pyautogui.press('enter'); "

        return command

    @agent_action
    def save_to_knowledge(self, text: List[str]):
        """Save facts, elements, texts, etc. to a long-term knowledge for reuse during this task. Can be used for copy-pasting text, saving elements, etc. Use this instead of ctrl+c, ctrl+v.
        Args:
            text:List[str] the text to save to the knowledge
        """
        self.notes.extend(text)
        return "WAIT"

    @agent_action
    def drag_and_drop(self, drag_from_id: int, drop_on_id: int, hold_keys: List = []):
        """Drag element1 and drop it on element2.
        Args:
            drag_from_id:int ID of element to drag
            drop_on_id:int ID of element to drop on
            hold_keys:List list of keys to hold while dragging
        """
        element1 = self.find_element(drag_from_id)
        element2 = self.find_element(drop_on_id)
        
        coords1 = element1["position"]
        size1 = element1["size"]
        coords2 = element2["position"]
        size2 = element2["size"]

        x1 = int(coords1[0] + size1[0] // 2)
        y1 = int(coords1[1] + size1[1] // 2)
        x2 = int(coords2[0] + size2[0] // 2)
        y2 = int(coords2[1] + size2[1] // 2)

        command = "import pyautogui; "
        command += f"pyautogui.moveTo({x1}, {y1}); "
        
        for k in hold_keys:
            command += f"pyautogui.keyDown({repr(k)}); "
        
        command += f"pyautogui.dragTo({x2}, {y2}, duration=1.0); pyautogui.mouseUp(); "
        
        for k in hold_keys:
            command += f"pyautogui.keyUp({repr(k)}); "

        return command

    @agent_action
    def scroll(self, element_id: int, clicks: int):
        """Scroll in the specified direction inside the specified element
        Args:
            element_id:int ID of the element to scroll in
            clicks:int the number of clicks to scroll can be positive (up) or negative (down).
        """
        try:
            element = self.find_element(element_id)
        except (IndexError, KeyError, AttributeError):
            element = self.find_element(0)

        coordinates = element["position"]
        size = element["size"]

        x = int(coordinates[0] + size[0] // 2)
        y = int(coordinates[1] + size[1] // 2)
        
        return f"import pyautogui; pyautogui.moveTo({x}, {y}); pyautogui.scroll({clicks})"

    @agent_action
    def hotkey(self, keys: List):
        """Press a hotkey combination
        Args:
            keys:List the keys to press in combination in a list format (e.g. ['shift', 'c'])
        """
        keys_str = [f"'{key}'" for key in keys]
        return f"import pyautogui; pyautogui.hotkey({', '.join(keys_str)}, interval=0.5)"

    @agent_action
    def hold_and_press(self, hold_keys: List, press_keys: List):
        """Hold a list of keys and press a list of keys
        Args:
            hold_keys:List, list of keys to hold
            press_keys:List, list of keys to press in a sequence
        """
        press_keys_str = "[" + ", ".join([f"'{key}'" for key in press_keys]) + "]"
        command = "import pyautogui; "
        
        for k in hold_keys:
            command += f"pyautogui.keyDown({repr(k)}); "
        
        command += f"pyautogui.press({press_keys_str}); "
        
        for k in hold_keys:
            command += f"pyautogui.keyUp({repr(k)}); "

        return command

    @agent_action
    def wait(self, time: float):
        """Wait for a specified amount of time
        Args:
            time:float the amount of time to wait in seconds
        """
        return f"import time; time.sleep({time})"

    @agent_action
    def done(self):
        """End the current task with a success"""
        return "DONE"

    @agent_action
    def fail(self):
        """End the current task with a failure"""
        return "FAIL"


# Define clickable roles that we want to preserve
clickable_roles = {
    "button",
    "text",
    "entry",
    "combo box",
    "list item",
    "menu item",
    "check box",
    "radio button",
    "link",
    "tab",
    "tree item",
    "table cell",
}
