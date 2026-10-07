"""Small, atomically written workspace layout (never shell history)."""
import json
import os
from pathlib import Path


def default_layout():
    return [{"name": "work", "tabs": [{"name": "main", "cwd": str(Path.home())}]}]


def load_layout(path):
    try:
        data = json.loads(path.read_text())
        result = []
        for workspace in data[:50]:
            tabs = []
            for tab in workspace["tabs"][:50]:
                cwd = tab["cwd"]
                if not isinstance(cwd, str) or not isinstance(tab["name"], str):
                    raise ValueError("Invalid tab")
                entry = {"name": tab["name"][:80], "cwd": cwd if Path(cwd).is_dir() else str(Path.home())}
                if 'panes' in tab:
                    panes = tab['panes']
                    if not isinstance(panes, list):
                        raise ValueError('Invalid panes')
                    entry['panes'] = []
                    for pane in panes[:3]:
                        directory = pane['cwd']
                        if not isinstance(directory, str):
                            raise ValueError('Invalid pane directory')
                        entry['panes'].append({'cwd': directory if Path(directory).is_dir() else str(Path.home())})
                if 'split' in tab:
                    entry['split'] = tab['split']
                tabs.append(entry)
            if not isinstance(workspace["name"], str):
                raise ValueError("Invalid workspace")
            result.append({"name": workspace["name"][:80], "tabs": tabs or default_layout()[0]["tabs"]})
        return result or default_layout()
    except (OSError, ValueError, TypeError, KeyError):
        return default_layout()


def save_layout(path, layout):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(layout, indent=2) + "\n")
    os.replace(temporary, path)
