import unittest
from termlook.core.models import Layout, Tab, Workspace


class LayoutTests(unittest.TestCase):
    def test_close_inactive_preserves_selection(self):
        first, second, third = Tab(), Tab(), Tab()
        workspace = Workspace(tabs=[first, second, third], selected_id=second.id)
        layout = Layout([workspace])
        layout.close_tab(first.id)
        self.assertIs(workspace.selected, second)
        layout.close_tab(second.id)
        self.assertIs(workspace.selected, third)

    def test_close_last_creates_fresh_tab(self):
        workspace = Workspace()
        original = workspace.selected
        layout = Layout([workspace])
        layout.close_tab(original.id)
        self.assertNotEqual(workspace.selected.id, original.id)
        self.assertEqual(workspace.selected.cwd, original.cwd)
        layout.close_tab(original.id)  # Repeated stale click is harmless.
        self.assertEqual(len(workspace.tabs), 1)

    def test_remove_workspace_keeps_other_selection(self):
        first, second = Workspace(), Workspace()
        layout = Layout([first, second], selected_id=second.id)
        layout.remove_workspace(first.id)
        self.assertIs(layout.selected, second)
        layout.remove_workspace(second.id)
        self.assertEqual(len(layout.workspaces), 1)
        self.assertNotEqual(layout.selected.id, second.id)
