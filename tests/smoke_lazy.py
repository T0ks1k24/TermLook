"""Check lazy restoration, background commands, and shell cleanup with real VTE."""
import json
import shlex
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from termlook.app import create_window, install_theme
from termlook.ui.gtk import GLib, Gtk

errors = []
def exception_hook(kind, value, traceback):
    errors.append(value)
    sys.__excepthook__(kind, value, traceback)
sys.excepthook = exception_hook

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    tabs = [{'name': f'tab {i}', 'cwd': directory} for i in range(32)]
    tabs[-1]['panes'] = [{'cwd': directory}, {'cwd': directory}]
    path = root / 'layout.json'
    path.write_text(json.dumps([{'name': 'work', 'tabs': tabs},
                                {'name': 'later', 'tabs': tabs[:8]}]))
    (root / 'settings.json').write_text(json.dumps({'shell': '/bin/sh'}))
    app = Gtk.Application(application_id='io.termlook.LazyTest')
    app.register(None)
    install_theme()
    window = create_window(app, path)
    controller = window.controller
    first = window.active_session
    first_tab = controller.layout.selected.selected
    marker = root / 'background-finished'
    phase = [0]
    old = []
    shell_pid = [None]

    def stop(error=None):
        if error is not None:
            errors.append(error)
        window.destroy()
        GLib.timeout_add(300, Gtk.main_quit)
        return False

    def step():
        try:
            if phase[0] == 0:
                assert len(window.sessions) == len(window.pane_grids) == 1
                if first.pending:
                    return True
                assert first.pid and not first.exited
                shell_pid[0] = first.pid
                # Repeated start requests cannot create orphan shells.
                first.start()
                assert first.pid == shell_pid[0] and not first.pending
                first.widget.feed_child(('sleep 0.2; printf done > ' + shlex.quote(str(marker)) + '\n').encode())
                workspace = controller.layout.selected
                # Closing an unopened restored tab must never start its shell.
                controller.close_tab(workspace.tabs[1].id)
                assert len(window.sessions) == 1
                first_grid = window.pane_grids[first_tab.id]
                with patch.object(first_grid, 'render', wraps=first_grid.render) as render:
                    controller.select_tab(workspace.tabs[-1].id)
                    render.assert_not_called()
                assert len(window.sessions) == 4
                assert len(window.pane_grids) == 2
                assert window.sessions[first.tab.id] is first and not first.closed
                phase[0] = 1
            elif phase[0] == 1:
                if not marker.exists() or any(s.pending for s in window.sessions.values()):
                    return True
                assert marker.read_text() == 'done'
                controller.select_tab(first_tab.id)
                assert window.active_session is first and first.pid == shell_pid[0]
                assert len(window.sessions) == 4
                controller.close_tab(first_tab.id)
                assert first.closed and first.widget is None
                phase[0] = 2
            elif phase[0] == 2:
                if Path(f'/proc/{shell_pid[0]}').exists():
                    return True
                # Removing an unopened workspace creates no terminals.
                count = len(window.sessions)
                controller.remove_workspace(controller.layout.workspaces[-1].id)
                assert len(window.sessions) == count
                old.extend(window.sessions.values())
                window.destroy()
                phase[0] = 3
            else:
                if any(s.pending for s in old):
                    return True
                assert all(s.closed and s.widget is None for s in old)
                Gtk.main_quit()
                return False
            return True
        except BaseException as error:
            return stop(error)

    watchdog = GLib.timeout_add_seconds(15, lambda: stop(AssertionError('Lazy regression timed out')))
    GLib.timeout_add(25, step)
    Gtk.main()
    GLib.source_remove(watchdog)
if errors:
    raise errors[0]
print('Lazy regression passed: 40 restored tabs, background command, reuse, dormant close, shell cleanup')
