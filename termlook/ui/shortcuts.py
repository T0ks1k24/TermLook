"""Keyboard bindings and their reference labels."""
from .gtk import Gdk, Vte

SHORTCUTS = [
    ("Split left / right", "Ctrl+Shift+E"),
    ("Split top / bottom", "Ctrl+Shift+D"),
    ("Close pane", "Ctrl+Shift+X"),
    ("Focus pane / show all", "Ctrl+Shift+Return"),
    ("New tab", "Ctrl+Shift+T"),
    ("New workspace", "Ctrl+Shift+N"),
    ("Close tab", "Ctrl+Shift+W"),
    ("Next tab", "Ctrl+Tab"),
    ("Previous tab", "Ctrl+Shift+Tab"),
    ("Copy", "Ctrl+Shift+C"),
    ("Paste", "Ctrl+Shift+V"),
    ("Rename tab", "F2"),
    ("Help", "F1"),
    ("Settings", "Ctrl+,"),
    ("Quit", "Ctrl+Shift+Q"),
]


def handle_key(window, event):
    controller = window.controller
    key = (Gdk.keyval_name(event.keyval) or '').lower()
    ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
    shift = event.state & Gdk.ModifierType.SHIFT_MASK
    action = None
    if ctrl and key == 'comma':
        action = window.show_settings
    elif event.keyval == Gdk.KEY_F1:
        action = lambda: window.guide.show_guide(1)
    elif event.keyval == Gdk.KEY_F2:
        action = controller.rename_tab
    elif ctrl and key in ('tab', 'iso_left_tab'):
        action = lambda: controller.cycle_tab(-1 if shift else 1)
    elif ctrl and shift:
        action = {'t': controller.new_tab, 'n': controller.new_workspace,
                  'd': lambda: controller.split_pane('vertical'), 'e': controller.split_pane, 'x': controller.close_pane,
                  'return': controller.toggle_zoom, 'w': controller.close_tab, 'q': window.destroy, 'c': lambda: window.active_session.copy(),
                  'v': lambda: window.active_session.paste()}.get(key)
    if action:
        window.dispatch(action)
        return True
    return False
