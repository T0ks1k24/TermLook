import tempfile
import unittest
from pathlib import Path
from termlook.core.settings import Settings
from termlook.services.preferences import load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def test_validate_untrusted_preferences(self):
        settings = Settings.from_data({'padding': 999, 'background': 'red; }', 'close_to_tray': 'yes',
                                       'cursor': 'oops', 'font': '', 'scrollback': -1, 'sidebar_width': True})
        self.assertEqual(settings.padding, 40)
        self.assertEqual(settings.background, '#202127')
        self.assertTrue(settings.close_to_tray)
        self.assertEqual(settings.cursor, 'block')
        self.assertEqual(settings.scrollback, 100)
        self.assertEqual(settings.sidebar_width, 182)

    def test_save_load_and_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'settings.json'
            self.assertEqual(load_settings(path), Settings())
            settings = Settings(font='Monospace 14', padding=20, close_to_tray=False)
            save_settings(path, settings)
            self.assertEqual(load_settings(path), settings)
            path.write_text('{')
            self.assertEqual(load_settings(path), Settings())
