import unittest
from unittest.mock import Mock

from termlook.core.controller import Controller
from termlook.core.models import Layout, Workspace


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.save = Mock()
        self.controller = Controller(Layout([Workspace()]), self.save)
        self.controller.view = Mock()

    def test_unchanged_layout_does_not_write_again(self):
        self.controller.persist()
        self.controller.persist()
        self.controller.shutdown()
        self.save.assert_called_once()

    def test_changed_layout_is_saved(self):
        self.controller.persist()
        self.controller.layout.selected.name = 'renamed'
        self.controller.persist()
        self.assertEqual(self.save.call_count, 2)
        self.assertEqual(self.save.call_args.args[0][0]['name'], 'renamed')

    def test_failed_write_is_retried(self):
        self.save.side_effect = [OSError('full'), None]
        self.controller.persist()
        self.controller.view.show_error.assert_called_with('Could not save layout: full')
        self.controller.persist()
        self.assertEqual(self.save.call_count, 2)
        self.controller.view.show_error.assert_called_with(None)
