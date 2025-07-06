import json
import os
import time
from typing import List, Dict

from pynput import mouse, keyboard


class EventRecorder:
    """Light-weight recorder for mouse & keyboard events using *pynput*.
    Saved events are a list of dicts so they can later be replayed or summarised
    by the LLM.
    """

    def __init__(self):
        self.events: List[Dict] = []
        self._start_time = None

    # ---------------------------------------------------------------------
    # Internal callbacks ---------------------------------------------------
    # ---------------------------------------------------------------------
    def _store(self, etype: str, info: Dict):
        if self._start_time is None:
            return
        self.events.append({
            "t": time.time() - self._start_time,
            "type": etype,
            "info": info,
        })

    # Mouse callbacks
    def _on_move(self, x, y):
        self._store("move", {"x": x, "y": y})

    def _on_click(self, x, y, button, pressed):
        self._store("click", {"x": x, "y": y, "button": str(button), "pressed": pressed})

    def _on_scroll(self, x, y, dx, dy):
        self._store("scroll", {"x": x, "y": y, "dx": dx, "dy": dy})

    # Keyboard callbacks
    def _on_press(self, key):
        self._store("key_press", {"key": str(key)})

    def _on_release(self, key):
        self._store("key_release", {"key": str(key)})

    # ------------------------------------------------------------------
    def start(self):
        """Begin recording in background threads."""
        self._start_time = time.time()
        self._m_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._k_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._m_listener.start()
        self._k_listener.start()

    def stop(self):
        """Stop listeners and return captured event list."""
        self._m_listener.stop()
        self._k_listener.stop()
        return self.events


# -------------------------------------------------------------------------
# Persistence helpers -----------------------------------------------------
# -------------------------------------------------------------------------

def _events_to_summary(events: List[Dict]) -> str:
    """Convert the raw events list into a concise, human-readable markdown summary.

    This is *very* heuristic but good enough to give the LLM an idea of what
    happened during the demonstration without parsing every coordinate.
    """

    lines = ["### Summary of Manual Demonstration\n"]
    for idx, ev in enumerate(events, 1):
        etype = ev.get("type", "event")
        info = ev.get("info", {})
        # Create a compact description string
        if etype in {"click", "move", "scroll"}:
            desc = f"{etype} at ({info.get('x')},{info.get('y')})"
        elif etype.startswith("key_"):
            desc = f"{etype} {info.get('key')}"
        else:
            desc = f"{etype} {info}"
        lines.append(f"{idx}. {desc}")
    return "\n".join(lines)


def save_demonstration(instruction: str, events: List[Dict], kb_root: str, platform: str):
    """Save a manual demonstration so that it integrates with the agent's
    episodic memory.

    The demo is stored under
      ``kb_root/<platform>/episodic_manual/demo_<ts>.json``
    and contains both the *raw* events and a *summary* string that mimics the
    structure of built-in episodic memory entries, making retrieval seamless.
    """

    folder = os.path.join(kb_root, platform, "episodic_manual")
    os.makedirs(folder, exist_ok=True)

    summary = _events_to_summary(events)

    ts = int(time.time())
    path = os.path.join(folder, f"demo_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "instruction": instruction,
            "summary": summary,
            "events": events,
        }, f, indent=2)

    return path 