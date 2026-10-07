"""Compose views and own their lifecycle; model/actions live in core/."""
from pathlib import Path
from .gtk import GLib, Gtk, Gdk
from .dialogs import ask
from .guide import Guide
from .settings import SettingsDialog
from termlook.services.tray import Tray
from .navigation import Navigation
from .panes import PaneGrid
from .shortcuts import handle_key
from .widgets import button
from termlook.services.terminal import TerminalSession

ASSETS = Path(__file__).resolve().parents[1] / 'assets'


class Window(Gtk.ApplicationWindow):
    def __init__(self, application, controller, settings, save_settings):
        super().__init__(application=application, title='TermLook')
        self.settings = settings
        self.save_settings = save_settings
        self.settings_dialog = None
        self.preferences_css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.preferences_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        self.controller = controller
        controller.view = self
        self.closed = False
        self.sources = set()
        self.sessions = {}
        self.pane_grids = {}
        self.guide = Guide(self)
        self.set_default_size(1120, 740)
        self.set_icon_from_file(str(ASSETS / 'io.termlook.TermLook.svg'))
        self.set_wmclass('termlook', 'TermLook')
        self.get_style_context().add_class('main-window')
        # The top row is the window's title bar: GTK moves the window when its empty space
        # is dragged and maximizes it on double-click, following the desktop's settings.
        titlebar = Gtk.Box()
        self.set_titlebar(titlebar)
        heading = Gtk.Box()
        heading.set_name('heading')
        label = Gtk.Label(label='spaces', xalign=0)
        label.set_name('brand')
        label.set_margin_start(12)
        heading.pack_start(label, True, True, 0)
        heading.pack_end(button('+', 'New workspace · Ctrl+Shift+N', lambda *_: self.dispatch(controller.new_workspace)), False, False, 0)
        titlebar.pack_start(heading, False, False, 0)
        tabbar = Gtk.Box(spacing=4)
        tabbar.set_name('tabbar')
        titlebar.pack_start(tabbar, True, True, 0)
        tabscroll = Gtk.ScrolledWindow()
        tabscroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        tabscroll.set_min_content_height(38)
        self.tabs = Gtk.Box()
        tabscroll.add(self.tabs)
        tabbar.pack_start(tabscroll, True, True, 0)
        # Same as the former title bar close button: hide to the tray or close, per Settings.
        self.hide_button = button('×', '', lambda *_: self.close())
        tabbar.pack_end(self.hide_button, False, False, 0)
        tabbar.pack_end(button('+', 'New tab · Ctrl+Shift+T', lambda *_: self.dispatch(controller.new_tab)), False, False, 0)
        self.split_button = button('◫', 'Split left / right · Ctrl+Shift+E', lambda *_: self.dispatch(controller.split_pane))
        tabbar.pack_end(self.split_button, False, False, 0)
        self.split_down_button = button('⬒', 'Split top / bottom · Ctrl+Shift+D', lambda *_: self.dispatch(lambda: controller.split_pane('vertical')))
        tabbar.pack_end(self.split_down_button, False, False, 0)
        tabbar.pack_end(button('⊞', 'Four panes', lambda *_: self.dispatch(controller.four_panes)), False, False, 0)
        self.zoom_button = button('□', 'Focus pane / show all · Ctrl+Shift+Return', lambda *_: self.dispatch(controller.toggle_zoom))
        tabbar.pack_end(self.zoom_button, False, False, 0)
        root = Gtk.Box()
        self.add(root)
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        sidebar.set_name('sidebar')
        self.sidebar = sidebar
        sidebar.set_size_request(settings.sidebar_width, -1)
        root.pack_start(sidebar, False, False, 0)
        # Keep the title bar's "spaces" column aligned with the sidebar below it.
        self.sidebar_columns = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        self.sidebar_columns.add_widget(heading)
        self.sidebar_columns.add_widget(sidebar)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.list = Gtk.ListBox()
        scroll.add(self.list)
        sidebar.pack_start(scroll, True, True, 0)
        footer = Gtk.Box()
        footer.pack_start(button('⚙', 'Settings · Ctrl+,', lambda *_: self.dispatch(self.show_settings)), False, False, 0)
        footer.pack_start(button('⌘', 'Keybinds', lambda *_: self.guide.show_guide(0)), False, False, 0)
        footer.pack_end(button('?', 'Help · F1', lambda *_: self.guide.show_guide(1)), False, False, 0)
        sidebar.pack_start(footer, False, False, 0)
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        body.set_name('surface')
        root.pack_start(body, True, True, 0)
        self.stack = Gtk.Stack()
        body.pack_start(self.stack, True, True, 0)
        self.status = Gtk.Label(xalign=0)
        self.status.set_name('status')
        self.status.set_no_show_all(True)
        body.pack_start(self.status, False, False, 0)
        self.navigation = Navigation(self.list, self.tabs, controller, self.dispatch)
        self.connect('key-press-event', lambda _, event: handle_key(self, event))
        self.connect('delete-event', self._delete)
        self.connect('destroy', self._destroy)
        self.tray = Tray(ASSETS / 'io.termlook.TermLook.svg', self.dispatch, self.restore, self.show_settings, self.destroy, self.restore_if_hidden)
        self.update_preferences_style()
        self.update_hide_button()
        self.render(controller.layout)
        self.show_all()

    def dispatch(self, action):
        """Leave GTK's current event handler before mutating/destroying widgets."""
        if self.closed:
            return
        def run():
            self.sources.discard(source)
            if not self.closed:
                action()
            return GLib.SOURCE_REMOVE
        source = GLib.idle_add(run)
        self.sources.add(source)

    @property
    def active_session(self):
        return self.sessions[self.controller.layout.selected.selected.active_pane.id]

    def render(self, layout):
        if self.closed:
            return
        tabs = {tab.id: tab for workspace in layout.workspaces for tab in workspace.tabs}
        live = {pane.id: pane for tab in tabs.values() for pane in tab.panes}
        # Move focus away from a terminal before disposing it.
        if any(tid not in live for tid in self.sessions):
            self.set_focus(None)
        for tid in list(self.sessions):
            if tid not in live:
                self.sessions.pop(tid).close()
        for tid in list(self.pane_grids):
            if tid not in tabs:
                self.pane_grids.pop(tid).dispose()
        # Restored tabs stay as model data until first selected: no VTE or shell.
        selected = layout.selected.selected
        for pane in selected.panes:
            tid = pane.id
            if tid not in self.sessions:
                session = TerminalSession(pane, lambda: self.dispatch(self.controller.persist), self.settings)
                self.sessions[tid] = session
                session.widget.connect('focus-in-event', self._pane_focused, tid)
                session.widget.show()
                session.start()
        if selected.id not in self.pane_grids:
            grid = PaneGrid(selected, self.controller, self.dispatch)
            self.pane_grids[selected.id] = grid
            self.stack.add_named(grid, selected.id)
        # Existing background sessions keep their PTYs and output; only the
        # selected grid needs layout work when switching tabs or changing panes.
        self.pane_grids[selected.id].render(self.sessions)
        self.navigation.render(layout)
        self.split_button.set_sensitive(len(selected.panes) < 4)
        self.split_down_button.set_sensitive(len(selected.panes) < 4)
        self.zoom_button.set_sensitive(len(selected.panes) > 1)
        self.zoom_button.set_label('▦' if selected.zoomed else '□')
        self.stack.set_visible_child(self.pane_grids[selected.id])
        self.active_session.widget.grab_focus()

    def _pane_focused(self, _widget, _event, pane_id):
        if self.closed:
            return False
        tab = self.controller.layout.selected.selected
        if any(p.id == pane_id for p in tab.panes):
            tab.active_pane_id = pane_id
            self.pane_grids[tab.id].highlight()
        return False

    def ask(self, title, initial):
        return ask(self, title, initial)

    def show_error(self, message):
        if message:
            self.status.set_text(message)
            self.status.show()
        else:
            self.status.hide()

    def show_settings(self):
        self.restore()
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
            self.settings_dialog.connect('destroy', self._settings_closed)
        self.settings_dialog.present()

    def _settings_closed(self, *_):
        self.settings_dialog = None

    def apply_settings(self, settings):
        self.save_settings(settings)
        self.settings = settings
        self.sidebar.set_size_request(settings.sidebar_width, -1)
        self.update_preferences_style()
        self.update_hide_button()
        for session in self.sessions.values():
            session.apply_settings(settings)

    def update_preferences_style(self):
        self.preferences_css.load_from_data(('#surface, #tabbar { background: ' + self.settings.background + '; }').encode())

    def update_hide_button(self):
        self.hide_button.set_tooltip_text('Hide to tray' if self.settings.close_to_tray else 'Close window')

    def restore(self):
        if not self.closed:
            self.show()
            self.deiconify()
            self.present()

    def restore_if_hidden(self):
        if not self.closed and not self.get_visible():
            self.dispatch(self.restore)

    def _delete(self, *_):
        self.dispatch(self.close_requested)
        return True

    def close_requested(self):
        if not self.settings.close_to_tray:
            self.destroy()
        elif self.tray.available:
            self.controller.persist()
            if self.guide.guide:
                self.guide.guide.hide()
            self.hide()
        else:
            # Never make a live terminal unreachable when no tray host exists.
            self.iconify()


    def _destroy(self, *_):
        if self.closed:
            return
        self.tray.close()
        if self.settings_dialog:
            self.settings_dialog.destroy()
        Gtk.StyleContext.remove_provider_for_screen(Gdk.Screen.get_default(), self.preferences_css)
        self.controller.shutdown()
        self.closed = True
        for source in self.sources:
            GLib.source_remove(source)
        self.sources.clear()
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()
        for grid in self.pane_grids.values():
            grid.dispose()
        self.pane_grids.clear()
