"""Composition root: load state, wire controller/view, register application."""
import os
from pathlib import Path
from .core.controller import Controller
from .core.models import Layout
from .services.preferences import load_settings, save_settings
from .services.storage import load_layout, save_layout
from .ui.gtk import Gdk, Gio, GLib, Gtk
from .ui.theme import CSS
from .ui.window import ASSETS, Window


def create_window(application, path=None):
    if path is None:
        path = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'termlook/layout.json'
    controller = Controller(Layout.from_data(load_layout(path)), lambda data: save_layout(path, data))
    settings_path = path.with_name('settings.json')
    return Window(application, controller, load_settings(settings_path), lambda settings: save_settings(settings_path, settings))


def install_theme():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def main():
    GLib.set_prgname('io.termlook.TermLook')
    GLib.set_application_name('TermLook')
    Gtk.Window.set_default_icon_from_file(str(ASSETS / 'io.termlook.TermLook.svg'))
    app = Gtk.Application(application_id='io.termlook.TermLook', flags=Gio.ApplicationFlags.FLAGS_NONE)

    app.main_window = None

    def activate(application):
        window = application.main_window
        if window:
            window.restore()
        else:
            install_theme()
            application.main_window = create_window(application)
            application.main_window.connect('destroy', lambda *_: setattr(application, 'main_window', None))

    app.connect('activate', activate)
    app.run(None)
