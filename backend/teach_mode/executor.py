import pyautogui
import time
import json
import os
import pygetwindow as gw
import keyboard
from datetime import datetime

class WorkflowExecutor:
    def __init__(self, workflow_file):
        self.workflow_file = workflow_file
        with open(workflow_file, 'r') as f:
            self.workflow_data = json.load(f)
        
        # Handle different workflow formats
        if isinstance(self.workflow_data, list):
            self.steps = self.workflow_data
        elif 'steps' in self.workflow_data:
            self.steps = self.workflow_data['steps']
        else:
            self.steps = []
            
        self.current_window = None
        self.stop_requested = False
        self.browser_state = {"active_tab": 1, "tab_count": 1}
        self.excel_state = {"workbook_open": False}
        self.browser_prepared = False
        keyboard.on_press_key("esc", self._emergency_stop)
    
    def _emergency_stop(self, _event):
        print("\n🛑 EMERGENCY STOP TRIGGERED!")
        self.stop_requested = True
        
    def execute(self):
        if not self.steps:
            print("⚠️ No steps found in workflow")
            return None
            
        # Save original failsafe setting and disable temporarily
        original_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        
        try:
            extracted_data = {}
            
            print(f"🚀 Starting execution of {len(self.steps)} steps...")
            print("Press ESC at any time to stop execution immediately")
            time.sleep(3)  # Give user time to position windows
            
            # Reset application states
            self.browser_state = {"active_tab": 1, "tab_count": 1}
            self.excel_state = {"workbook_open": False}
            self.browser_prepared = False
            
            for step_index, step in enumerate(self.steps):
                if self.stop_requested:
                    print("🚫 Execution stopped by user")
                    return None
                
                step_name = step.get('name', f'Step {step_index+1}')
                step_desc = step.get('description', 'No description')
                
                print(f"\n🔹 Step {step_index+1}/{len(self.steps)}: {step_name}")
                print(f"   📝 Description: {step_desc}")
                
                # Check application state before executing step
                self.check_application_state(step_desc)
                
                actions = step.get('actions', [])
                if not actions:
                    print("   ⚠️ No actions in this step, skipping")
                    continue
                    
                print(f"   ⚙️ Executing {len(actions)} actions...")
                
                for action_index, action in enumerate(actions):
                    if self.stop_requested:
                        print("🚫 Execution stopped by user")
                        return None
                    
                    action_type = action.get('type', '')
                    
                    # Log the action
                    print(f"      🔧 Action {action_index+1}: {action_type}")
                    
                    # Add delay between actions
                    time.sleep(0.5)
                    
                    try:
                        # Handle browser tabs intelligently
                        if "browser" in step_desc.lower() and action_type == 'click':
                            self.handle_browser_tab_click(action, step_desc)
                        elif action_type == 'key_press':
                            self.handle_key_press(action)
                        elif action_type == 'type':
                            self.handle_typing(action, step_desc)
                        elif action_type == 'click':
                            self.handle_click(action)
                        elif action_type == 'copy':
                            self.handle_copy()
                        elif action_type == 'paste':
                            self.handle_paste()
                        elif action_type == 'hotkey':
                            self.handle_hotkey(action)
                        elif action_type == 'extract_field':
                            extracted_data.update(self.handle_extraction(action))
                    
                    except Exception as e:
                        print(f"   ⚠️ Action failed: {str(e)}")
                        if self.smart_error_recovery(e, action, step_desc):
                            print("   🔄 Retrying action after recovery...")
                            # Retry the failed action once
                            if action_type == 'key_press':
                                self.handle_key_press(action)
                            elif action_type == 'type':
                                self.handle_typing(action, step_desc)
                            elif action_type == 'click':
                                self.handle_click(action)
            
            return extracted_data
        
        finally:
            # Restore original failsafe setting
            pyautogui.FAILSAFE = original_failsafe
            print("\n✅ Execution completed")

    # ================== ENHANCED METHODS ================== #
    
    def prepare_browser_environment(self):
        """Prepare browser for automation without closing existing tabs"""
        print("   🌐 Preparing browser environment...")
        try:
            # Activate Chrome without closing anything
            self.activate_window("Chrome")
            time.sleep(1)
            
            # Create new window for automation (Ctrl+Shift+N for incognito or Ctrl+N for regular)
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(2)
            
            # Update browser state
            self.browser_state = {
                "active_tab": 1, 
                "tab_count": 1,
                "automation_window": True
            }
            print("   ✅ Created new window for automation")
            return True
        
        except Exception as e:
            print(f"   ⚠️ Browser preparation failed: {str(e)}")
            # Fallback to regular activation
            return self.activate_window("Chrome")
    
    def handle_browser_tab_click(self, action, step_desc):
        """Handle browser tab clicks intelligently using relative positioning"""
        # Get current tab count
        current_tabs = self.browser_state["tab_count"]
        
        # Calculate which tab we should be clicking based on description
        target_tab = 1
        if "second" in step_desc.lower():
            target_tab = 2
        elif "third" in step_desc.lower():
            target_tab = 3
        elif "fourth" in step_desc.lower():
            target_tab = 4
            
        # Switch to correct tab if needed
        if target_tab != self.browser_state["active_tab"]:
            print(f"      ↪️ Switching to tab {target_tab}")
            pyautogui.hotkey('ctrl', str(target_tab))
            time.sleep(0.5)
            self.browser_state["active_tab"] = target_tab
        
        # Perform the click action
        self.handle_click(action)
        
        # Check if we opened a new tab
        if "open new tab" in step_desc.lower() or "new tab" in step_desc.lower():
            self.browser_state["tab_count"] += 1
            print(f"      ➕ New tab opened (total: {self.browser_state['tab_count']})")
    
    def check_application_state(self, step_description):
        """Ensure required applications are in correct state before steps"""
        # For Excel-related steps
        if "excel" in step_description.lower():
            if not self.excel_state["workbook_open"]:
                print("   📂 Opening new Excel workbook...")
                self.activate_window("Excel")
                time.sleep(1)
                pyautogui.hotkey('ctrl', 'n')  # New workbook
                time.sleep(1)
                self.excel_state["workbook_open"] = True
            else:
                self.activate_window("Excel")
            
            # Handle common Excel popups
            self.handle_excel_popups()
        
        # For browser-related steps
        if any(word in step_description.lower() for word in ["chrome", "browser", "search", "web"]):
            # Prepare browser if not already done
            if not self.browser_prepared:
                self.prepare_browser_environment()
                self.browser_prepared = True
            else:
                self.activate_window("Chrome")
            time.sleep(1)
    
    def handle_excel_popups(self):
        """Automatically close common Excel popups with multiple attempts"""
        popup_handlers = [
            {"title": "Save", "action": lambda: pyautogui.press('n')},
            {"title": "Document Recovery", "action": lambda: pyautogui.click(50, 50)},
            {"title": "Security Warning", "action": lambda: pyautogui.press('enter')},
            {"title": "Microsoft Excel", "action": lambda: pyautogui.press('esc')},
            {"title": "Update Links", "action": lambda: pyautogui.press('esc')}
        ]
        
        for handler in popup_handlers:
            try:
                windows = gw.getWindowsWithTitle(handler["title"])
                if windows:
                    windows[0].activate()
                    time.sleep(0.5)
                    handler["action"]()
                    print(f"   ⚠️ Closed '{handler['title']}' popup")
                    time.sleep(1)
            except Exception:
                pass
    
    def dynamic_filename(self, original_name):
        """Generate smart filenames with timestamps including seconds"""
        # Get current date/time components
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        # Handle common file types
        if "report" in original_name.lower():
            return f"Report_{timestamp}.xlsx"
        elif "data" in original_name.lower():
            return f"Data_{timestamp}.csv"
        elif "export" in original_name.lower():
            return f"Export_{timestamp}.xlsx"
        
        # Default: append timestamp
        name, ext = os.path.splitext(original_name)
        return f"{name}_{timestamp}{ext}"
    
    def smart_error_recovery(self, error, action, step_description):
        """Advanced error recovery with context awareness"""
        error_msg = str(error).lower()
        
        # File already exists error
        if "file already exists" in error_msg:
            print("   ⚠️ File conflict detected!")
            if action.get('type') == 'type':
                new_name = self.dynamic_filename(action.get('text', ''))
                print(f"   🔄 Changing filename to: {new_name}")
                pyautogui.typewrite(new_name)
                return True
        
        # Browser tab not available
        if "tab" in error_msg or "browser" in error_msg:
            print("   ⚠️ Browser issue! Creating new tab...")
            pyautogui.hotkey('ctrl', 't')
            time.sleep(1)
            self.browser_state["tab_count"] += 1
            self.browser_state["active_tab"] = self.browser_state["tab_count"]
            return True
        
        # Excel not responding
        if "excel" in error_msg:
            print("   ⚠️ Excel issue! Creating new workbook...")
            self.activate_window("Excel")
            pyautogui.hotkey('ctrl', 'n')
            time.sleep(1)
            self.excel_state["workbook_open"] = True
            return True
        
        return False
    
    # ================== ACTION HANDLERS ================== #
    
    def activate_window(self, window_title):
        """Reliable window activation with multiple fallbacks"""
        try:
            # Try to find window
            windows = gw.getWindowsWithTitle(window_title)
            if windows:
                win = windows[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(1)
                print(f"   🖥️ Activated window: {window_title}")
                return True
            
            # Launch application if not found
            app_launcher = {
                "Excel": "excel.exe",
                "Chrome": "chrome.exe"
            }
            if window_title in app_launcher:
                os.startfile(app_launcher[window_title])
                print(f"   ⚠️ Launched {window_title} because it wasn't open")
                time.sleep(3)
                return self.activate_window(window_title)  # Recursive retry
            
            return False
        except Exception as e:
            print(f"   ⚠️ Window activation failed: {str(e)}")
            return False

    def handle_key_press(self, action):
        key = action.get('key', '')
        # Map key names
        key_mapping = {
            'esc': 'escape',
            'del': 'delete',
            'backspace': 'backspace',
            'enter': 'enter'
        }
        key = key_mapping.get(key, key)
        
        if key in ['ctrl', 'alt', 'shift']:
            return  # Skip modifier-only presses
            
        if key:
            pyautogui.press(key)
            print(f"         ⌨️ Pressed key: {key}")
            time.sleep(0.5)

    def handle_typing(self, action, step_description):
        text = action.get('text', '')
        if text:
            # Use smart filenames for saving operations
            if "save" in step_description.lower() or "file" in step_description.lower():
                text = self.dynamic_filename(text)
            
            # Type with proper intervals
            pyautogui.write(text, interval=0.1)
            print(f"         ⌨️ Typed: {text[:50]}{'...' if len(text) > 50 else ''}")
            time.sleep(0.5)

    def handle_click(self, action):
        location = action.get('location', [])
        button = action.get('button', 'left').lower()
        
        # Normalize button names
        button_mapping = {
            'button.left': 'left',
            'button.right': 'right',
            'button.middle': 'middle',
            'left': 'left',
            'right': 'right',
            'middle': 'middle',
            'primary': 'left',
            'secondary': 'right'
        }
        button = button_mapping.get(button, 'left')
        
        if len(location) >= 2:
            x, y = location[0], location[1]
            # Move to location with visible motion
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.2)
            pyautogui.click(button=button)
            print(f"         🖱️ Clicked at ({x}, {y}) with {button} button")
            time.sleep(1)

    def handle_copy(self):
        pyautogui.hotkey('ctrl', 'c')
        print("         ⎘ Copied selection to clipboard")
        time.sleep(1)

    def handle_paste(self):
        pyautogui.hotkey('ctrl', 'v')
        print("         ⎘ Pasted from clipboard")
        time.sleep(1)

    def handle_hotkey(self, action):
        keys = action.get('keys', [])
        if len(keys) >= 2:
            # Map keys for PyAutoGUI compatibility
            mapped_keys = []
            for key in keys:
                if key == 'cmd':
                    mapped_keys.append('command')  # PyAutoGUI expects 'command' on macOS
                else:
                    mapped_keys.append(key)
            
            pyautogui.hotkey(*mapped_keys)
            print(f"         ⌨️ Hotkey pressed: {'+'.join(mapped_keys)}")
            time.sleep(1)