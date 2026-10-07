"""Settings stored separately from the workspace layout."""
import json
from termlook.core.settings import Settings
from .storage import save_layout


def load_settings(path):
    try:
        return Settings.from_data(json.loads(path.read_text()))
    except (OSError, ValueError):
        return Settings()


def save_settings(path, settings):
    save_layout(path, settings.to_data())
