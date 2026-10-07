import tempfile
import unittest
from pathlib import Path

from termlook.services.storage import default_layout, load_layout, save_layout


class LayoutTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config/layout.json"
            layout = [{"name": "проєкт", "tabs": [{"name": "shell", "cwd": directory}]}]
            save_layout(path, layout)
            self.assertEqual(load_layout(path), layout)

    def test_invalid_and_missing_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "layout.json"
            self.assertEqual(load_layout(path), default_layout())
            for content in ['oops', '{}', '[{"name": 2, "tabs": []}]', 'null']:
                path.write_text(content)
                self.assertEqual(load_layout(path), default_layout())

    def test_missing_directory_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "layout.json"
            save_layout(path, [{"name": "work", "tabs": [{"name": "main", "cwd": directory + "/missing"}]}])
            self.assertEqual(load_layout(path)[0]["tabs"][0]["cwd"], str(Path.home()))
