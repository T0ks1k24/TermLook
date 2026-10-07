"""Real GTK/VTE lifecycle regression. Run with G_DEBUG=fatal-criticals."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from termlook.app import create_window, install_theme
from termlook.ui.gtk import GLib, Gtk

errors = []
def exception_hook(kind, value, traceback):
    errors.append(value)
    sys.__excepthook__(kind, value, traceback)
sys.excepthook = exception_hook

with tempfile.TemporaryDirectory() as directory:
    app = Gtk.Application(application_id='io.termlook.SmokeTest')
    app.register(None)
    install_theme()
    window = create_window(app, Path(directory) / 'layout.json')
    controller = window.controller
    window.ask = lambda *_: 'renamed'
    old = []
    counter = [0]

    def step():
        try:
            if counter[0] == 0:
                assert window.active_session.widget.get_pty() is not None
                window.show_settings()
                dialog = window.settings_dialog
                dialog.controls['padding'].set_value(20)
                dialog.controls['scrollback'].set_value(5000)
                dialog.controls['cursor'].set_active_id('underline')
                window.apply_settings(dialog.values())
                assert window.active_session.widget.get_margin_start() == 20
                assert window.active_session.widget.get_scrollback_lines() == 5000
                assert (Path(directory) / 'settings.json').exists()
                dialog.destroy()
                # Simulated tray host: close hides without destroying live PTYs.
                availability = window.tray.available
                window.tray.available = True
                session = window.active_session
                window.close_requested()
                assert not window.get_visible() and not session.closed
                window.restore()
                assert window.get_visible() and window.active_session is session
                window.tray.available = False
                window.close_requested()
                assert window.get_visible() and not window.closed
                window.restore()
                window.tray.available = availability
                tab = controller.layout.selected.selected
                original_session = window.active_session
                controller.four_panes()
                assert len(tab.panes) == 4
                controller.split_pane()
                assert len(tab.panes) == 4
                pane_sessions = [window.sessions[p.id] for p in tab.panes]
                grid = window.pane_grids[tab.id]
                assert len(grid.cells) == 4
                assert all(header.get_children()[-1].get_visible() for header, _ in grid.headers.values())
                controller.toggle_zoom()
                assert len(grid.get_children()) == 1
                assert all(not s.closed for s in pane_sessions)
                controller.toggle_zoom()
                assert len(grid.cells) == 4
                controller.close_pane(tab.panes[0].id)
                assert original_session.closed
                assert len(grid.cells) == 3
                while len(tab.panes) > 1:
                    controller.close_pane(tab.active_pane.id)
                assert len(grid.get_children()) == 1
                assert not window.active_session.closed
                first = controller.layout.selected
                controller.new_tab()
                selected = first.selected.id
                controller.new_workspace()
                second = controller.layout.selected
                controller.select_workspace(first.id)
                assert first.selected.id == selected
                assert len(window.navigation.headers) == 2
                controller.rename_tab()
                assert first.selected.name == 'renamed'
                controller.remove_workspace(second.id)
                window.guide.show_guide(0)
                window.guide.show_guide(1)
                window.guide.guide.destroy()
                assert window.get_icon() is not None
            if counter[0] < 30:
                controller.new_tab()
                session = window.active_session
                old.append(session)
                # Simulate actual close-button activation. It must stay alive
                # until GTK leaves the signal handler and dispatches idle work.
                header = window.navigation.headers[session.tab.id]
                close = header.get_children()[-1]
                close.clicked()
                assert not session.closed
                counter[0] += 1
                return True
            assert all(s.closed and not s.pending and s.widget is None for s in old)
            controller.remove_workspace(controller.layout.selected.id)
            assert len(controller.layout.workspaces) == 1
            assert len(controller.layout.selected.tabs) == 1
            # Close while another asynchronous spawn is still in flight.
            controller.new_tab()
            old.extend(window.sessions.values())
            window.destroy()
            GLib.timeout_add(500, finish)
        except BaseException as error:
            errors.append(error)
            window.destroy()
            Gtk.main_quit()
        return False

    def finish():
        try:
            assert all(s.closed and not s.pending and s.widget is None for s in old)
        except BaseException as error:
            errors.append(error)
        Gtk.main_quit()
        return False

    def start():
        GLib.timeout_add(40, step)
        return False
    GLib.timeout_add(500, start)
    Gtk.main()
if errors:
    raise errors[0]
print('GUI regression passed: 30 close-button cycles, pending spawns, spaces, rename, help, icon, shutdown')
