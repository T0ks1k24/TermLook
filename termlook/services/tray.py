"""Optional Ubuntu StatusNotifier/AppIndicator integration."""
import importlib
import gi
from termlook.ui.gtk import Gio, Gtk


class Tray:
    def __init__(self, icon_path, dispatch, show, settings, quit_app, unavailable):
        self.indicator = None
        self.backend = None
        self.available = False
        self.watch = None
        self.unavailable = unavailable
        self.icon_path = icon_path
        self.dispatch = dispatch
        self.actions = [('Open TermLook', show), ('Settings', settings), ('Quit', quit_app)]
        for namespace in ('AyatanaAppIndicator3', 'AppIndicator3'):
            try:
                gi.require_version(namespace, '0.1')
                self.backend = importlib.import_module('gi.repository.' + namespace)
                break
            except (ValueError, ImportError):
                pass
        if self.backend is None:
            return
        # Create the indicator only when a host exists. Ayatana's legacy
        # GtkStatusIcon fallback can emit GTK criticals on a headless desktop.
        self.watch = Gio.bus_watch_name(Gio.BusType.SESSION, 'org.kde.StatusNotifierWatcher',
                                       Gio.BusNameWatcherFlags.NONE, self._appeared, self._vanished)

    def _create_indicator(self):
        self.indicator = self.backend.Indicator.new('termlook', str(self.icon_path), self.backend.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_title('TermLook')
        self.menu = Gtk.Menu()
        for label, action in self.actions:
            item = Gtk.MenuItem(label=label)
            item.connect('activate', lambda _, action=action: self.dispatch(action))
            self.menu.append(item)
        self.menu.show_all()
        self.indicator.set_menu(self.menu)

    def _appeared(self, *_):
        if self.indicator is None:
            self._create_indicator()
        self.indicator.set_status(self.backend.IndicatorStatus.ACTIVE)
        self.available = True

    def _vanished(self, *_):
        was_available = self.available
        self.available = False
        if self.indicator is not None:
            self.indicator.set_status(self.backend.IndicatorStatus.PASSIVE)
        if was_available:
            self.unavailable()

    def close(self):
        if self.watch is not None:
            Gio.bus_unwatch_name(self.watch)
            self.watch = None
        if self.indicator:
            self.indicator.set_status(self.backend.IndicatorStatus.PASSIVE)
            self.menu.destroy()
        self.available = False
