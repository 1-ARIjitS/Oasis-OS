import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("desktopenv.agent")


def agent_action(func):
    func.is_agent_action = True
    return func


class ACI:
    def __init__(self, top_app_only: bool = True, ocr: bool = False):
        self.top_app_only = top_app_only
        self.ocr = ocr
        self.index_out_of_range_flag = False
        self.notes: List[str] = []
        self.clipboard = ""
        self.nodes: List[Any] = []

    def get_active_apps(self, obs: Dict) -> List[str]:
        """Get list of currently active applications"""
        raise NotImplementedError("Subclasses must implement get_active_apps() method")

    def get_top_app(self, obs: Dict):
        """Get the topmost application window"""
        raise NotImplementedError("Subclasses must implement get_top_app() method")

    def preserve_nodes(self, tree: Any, exclude_roles: Optional[set] = None) -> List[Dict]:
        """Preserve and filter accessibility tree nodes"""
        if exclude_roles is None:
            exclude_roles = set()
        raise NotImplementedError("Subclasses must implement preserve_nodes() method")

    def linearize_and_annotate_tree(
        self, obs: Dict, show_all_elements: bool = False
    ) -> str:
        """Convert accessibility tree to linearized text format"""
        raise NotImplementedError("Subclasses must implement linearize_and_annotate_tree() method")

    def find_element(self, element_id: int) -> Dict:
        """Find UI element by ID"""
        raise NotImplementedError("Subclasses must implement find_element() method")
