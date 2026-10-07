import tempfile
import unittest
from pathlib import Path
from termlook.core.models import Layout, Tab, Workspace
from termlook.services.storage import load_layout, save_layout


class PaneTests(unittest.TestCase):
    def test_limit_and_close_primary(self):
        tab = Tab()
        for _ in range(10):
            tab.split()
        self.assertEqual(len(tab.panes), 4)
        first = tab.panes[0]
        survivor = tab.panes[1]
        self.assertTrue(tab.close_pane(first.id))
        self.assertIs(tab.panes[0], survivor)
        self.assertFalse(tab.close_pane(first.id))
        while len(tab.panes) > 1:
            tab.close_pane(tab.active_pane.id)
        self.assertFalse(tab.close_pane(tab.active_pane.id))

    def test_roundtrip_and_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            tab = Tab(cwd=directory)
            for _ in range(3):
                tab.split()
            layout = Layout([Workspace(tabs=[tab])])
            path = Path(directory) / 'layout.json'
            save_layout(path, layout.to_data())
            restored = Layout.from_data(load_layout(path))
            self.assertEqual(len(restored.selected.selected.panes), 4)
            self.assertEqual(restored.to_data(), layout.to_data())
            old = Layout.from_data([{'name': 'work', 'tabs': [{'name': 'main', 'cwd': directory}]}])
            self.assertEqual(len(old.selected.selected.panes), 1)

    def test_top_with_two_below_and_swapping(self):
        from termlook.core.splits import leaves, encode
        tab = Tab()
        top = tab.active_pane.id
        tab.split('vertical')
        bottom_left = tab.active_pane.id
        tab.split('horizontal')
        bottom_right = tab.active_pane.id
        self.assertEqual(tab.tree()['axis'], 'vertical')
        self.assertEqual(tab.tree()['first'], top)
        self.assertEqual(tab.tree()['second']['axis'], 'horizontal')
        tab.tree()['ratio'] = 0.35
        tab.swap_panes(top, bottom_right)
        self.assertEqual(leaves(tab.tree()), [bottom_right, bottom_left, top])
        layout = Layout([Workspace(tabs=[tab])])
        restored = Layout.from_data(layout.to_data()).selected.selected
        self.assertEqual(encode(restored.tree(), [p.id for p in restored.panes]),
                         encode(tab.tree(), [p.id for p in tab.panes]))
        tab.close_pane(bottom_left)
        self.assertEqual(len(leaves(tab.tree())), 2)

    def test_invalid_tree_falls_back(self):
        from termlook.core.splits import decode, leaves
        ids = ['a', 'b']
        for data in [None, {'axis': 'vertical', 'first': 0, 'second': 0},
                     {'axis': 'horizontal', 'first': 0, 'second': 1, 'ratio': float('nan')}]:
            self.assertEqual(leaves(decode(data, ids)), ids)
