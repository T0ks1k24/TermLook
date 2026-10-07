"""Own each VTE session and cancel pending work before disposing its widget."""
import os
import pwd
from pathlib import Path
from urllib.parse import unquote, urlparse
from termlook.ui.gtk import Gio, GLib, Gtk, Pango, Vte
from termlook.ui.widgets import color


def user_shell(configured=''):
    """Return the configured shell, then $SHELL, then the login shell from passwd."""
    candidates = [configured, os.environ.get('SHELL', '')]
    try:
        candidates.append(pwd.getpwuid(os.getuid()).pw_shell)
    except KeyError:
        pass
    for shell in candidates + ['/bin/bash']:
        if shell and os.path.isfile(shell) and os.access(shell, os.X_OK):
            return shell
    return '/bin/sh'


def shell_environment(environ):
    """Return the shell's environment from KEY=VALUE strings, without snap launcher changes.

    The classic snap launcher lists the variables it overrides in TERMLOOK_SNAP_RESTORE and
    keeps each original value in TERMLOOK_SNAP_ORIG_<NAME>; a missing original means unset.
    """
    env = dict(item.split('=', 1) for item in environ if '=' in item)
    restore = env.pop('TERMLOOK_SNAP_RESTORE', None)
    if restore is not None:
        for name in restore.split():
            original = env.pop('TERMLOOK_SNAP_ORIG_' + name, None)
            if original is None:
                env.pop(name, None)
            else:
                env[name] = original
        for name in [name for name in env if name == 'SNAP' or name.startswith('SNAP_')]:
            del env[name]
    env['TERM'] = 'xterm-256color'
    return [name + '=' + value for name, value in env.items()]


class TerminalSession:
    def __init__(self, tab, on_directory, settings):
        self.settings = settings
        self.tab = tab
        self.on_directory = on_directory
        self.closed = False
        self.exited = False
        self.pending = True
        self.cancellable = Gio.Cancellable()
        self.menu = None
        self.widget = Vte.Terminal()
        terminal = self.widget
        terminal.set_mouse_autohide(True)
        self.apply_settings(settings)
        self.handlers = [terminal.connect('child-exited', self._exited),
                         terminal.connect('notify::current-directory-uri', self._directory),
                         terminal.connect('button-press-event', self._menu)]

    def apply_settings(self, settings):
        self.settings = settings
        if self.closed:
            return
        terminal = self.widget
        terminal.set_font(Pango.FontDescription(settings.font))
        terminal.set_scrollback_lines(settings.scrollback)
        terminal.set_colors(color(settings.foreground), color(settings.background), [color(c) for c in
            ['#454158', '#ef8199', '#a9d794', '#edd49a', '#8eb9ee', '#c4a0ed', '#80d8cb', '#d8d6eb',
             '#77718c', '#f5a1b5', '#c0e7ad', '#f5dfb1', '#afd0ff', '#d7bdf6', '#a1ebe0', '#ffffff']])
        terminal.set_cursor_shape({'block': Vte.CursorShape.BLOCK, 'ibeam': Vte.CursorShape.IBEAM,
                                   'underline': Vte.CursorShape.UNDERLINE}[settings.cursor])
        terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON if settings.blink else Vte.CursorBlinkMode.OFF)
        terminal.set_audible_bell(settings.audible_bell)
        terminal.set_scroll_on_output(settings.scroll_on_output)
        terminal.set_scroll_on_keystroke(settings.scroll_on_keystroke)
        for edge in ('start', 'top', 'end', 'bottom'):
            getattr(terminal, 'set_margin_' + edge)(settings.padding)

    def start(self):
        shell = user_shell(self.settings.shell)
        cwd = self.tab.cwd if Path(self.tab.cwd).is_dir() else str(Path.home())
        # Pass the complete environment so variables removed by shell_environment stay removed.
        # GLib.get_environ() also reflects variables GTK has unset, unlike os.environ.
        self.widget.spawn_async(Vte.PtyFlags.DEFAULT, cwd, [shell], shell_environment(GLib.get_environ()),
                                GLib.SpawnFlags(Vte.SPAWN_NO_PARENT_ENVV), None, None, -1,
                                self.cancellable, self._spawned, None)

    def _spawned(self, terminal, pid, error, _data):
        self.pending = False
        if self.closed:
            self._destroy()
            return
        if error:
            self.exited = True
            terminal.feed(('Could not start shell: ' + str(error) + '\r\n').encode())

    def _exited(self, terminal, status):
        self.exited = True
        if not self.closed:
            terminal.feed(b'\r\n[Session ended. Ctrl+Shift+T: new terminal.]\r\n')

    def _directory(self, terminal, _param):
        if self.closed:
            return
        uri = terminal.get_current_directory_uri()
        if uri:
            cwd = unquote(urlparse(uri).path)
            if Path(cwd).is_dir():
                self.tab.cwd = cwd
                self.on_directory()

    def _menu(self, terminal, event):
        if event.button != 3 or self.closed:
            return False
        if self.menu:
            self.menu.destroy()
        self.menu = Gtk.Menu()
        self.menu.attach_to_widget(terminal, None)
        for title, callback in [('Copy', self.copy), ('Paste', self.paste)]:
            item = Gtk.MenuItem(label=title)
            item.connect('activate', lambda _, action=callback: action())
            self.menu.append(item)
        self.menu.show_all()
        self.menu.popup_at_pointer(event)
        return True

    def copy(self):
        if not self.closed:
            self.widget.copy_clipboard_format(Vte.Format.TEXT)

    def paste(self):
        if not self.closed:
            self.widget.paste_clipboard()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.on_directory = lambda: None
        self.cancellable.cancel()
        for handler in self.handlers:
            self.widget.disconnect(handler)
        self.handlers.clear()
        if self.menu:
            self.menu.destroy()
            self.menu = None
        # Retain the widget until spawn_async completes, even after detachment.
        parent = self.widget.get_parent()
        if parent:
            parent.remove(self.widget)
        if not self.pending:
            self._destroy()

    def _destroy(self):
        if self.widget is not None:
            self.widget.destroy()
            self.widget = None
