"""Preferences editor. Apply commits once; Cancel leaves live sessions intact."""
import os
from termlook.core.settings import Settings
from .gtk import Gtk
from .widgets import color
from .preferences_widgets import PreferenceBrowser, card, row, add_row, label


class SettingsDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title='Settings', transient_for=parent, modal=True)
        self.parent = parent
        self.set_default_size(820, 680)
        self.get_style_context().add_class('preferences-window')
        self.add_buttons('Cancel', Gtk.ResponseType.CANCEL, 'Apply changes', Gtk.ResponseType.APPLY)
        self.get_widget_for_response(Gtk.ResponseType.APPLY).get_style_context().add_class('pref-primary')
        self.controls = {}
        browser = PreferenceBrowser()
        self.browser = browser
        self.get_content_area().pack_start(browser, True, True, 0)
        descriptions = {
            'font': 'Typeface and size for every terminal.',
            'foreground': 'Default terminal text.', 'background': 'The surface behind your terminal.',
            'cursor': 'Choose the shape of the text cursor.', 'blink': 'Animate the active cursor.',
            'padding': 'Space around terminal content, in pixels.', 'sidebar_width': 'Workspace sidebar width, in pixels.',
            'shell': 'Executable path. Leave empty for your default shell.',
            'scrollback': 'Number of output lines to keep in memory.',
            'audible_bell': 'Play a sound when a program rings the bell.',
            'scroll_on_output': 'Follow new output automatically.',
            'scroll_on_keystroke': 'Return to the latest output when typing.',
            'close_to_tray': 'Keep your shells running when you close the window.',
        }
        subtitles = {'Appearance': 'Make this space your own.',
                     'Terminal': 'Choose how your shell and output behave.',
                     'Behavior': 'Decide what happens when you step away.'}
        settings = parent.settings
        for title, fields in [
            ('Appearance', [('font', 'Font'), ('foreground', 'Text color'), ('background', 'Terminal background'),
                        ('cursor', 'Cursor'), ('blink', 'Blink cursor'), ('padding', 'Padding'), ('sidebar_width', 'Sidebar width')]),
            ('Terminal', [('shell', 'Shell'), ('scrollback', 'Scrollback lines'), ('audible_bell', 'Audible bell'),
                         ('scroll_on_output', 'Scroll on output'), ('scroll_on_keystroke', 'Scroll on keystroke')]),
            ('Behavior', [('close_to_tray', 'Close window to tray')]),
        ]:
            content = browser.add_page(title, title, subtitles[title])
            group = card()
            content.pack_start(group, False, False, 0)
            for name, caption in fields:
                value = getattr(settings, name)
                if name == 'font':
                    widget = Gtk.FontButton(font=value)
                elif name in ('foreground', 'background'):
                    widget = Gtk.ColorButton(rgba=color(value))
                elif name == 'cursor':
                    widget = Gtk.ComboBoxText()
                    for key, text in [('block', 'Block'), ('ibeam', 'Beam'), ('underline', 'Underline')]:
                        widget.append(key, text)
                    widget.set_active_id(value)
                elif type(value) is bool:
                    widget = Gtk.Switch(active=value)
                    widget.set_halign(Gtk.Align.END)
                elif type(value) is int:
                    low, high, step = {'scrollback': (100, 1000000, 1000), 'padding': (0, 40, 1), 'sidebar_width': (140, 320, 10)}[name]
                    widget = Gtk.SpinButton.new_with_range(low, high, step)
                    widget.set_value(value)
                else:
                    widget = Gtk.Entry(text=value)
                    widget.set_placeholder_text('Automatic, e.g. /bin/bash')
                if name == 'shell':
                    shell_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=14)
                    shell_row.pack_start(label(caption, 'pref-row-title'), False, False, 0)
                    shell_row.pack_start(label(descriptions[name], 'pref-muted', True), False, False, 0)
                    shell_row.pack_start(widget, False, False, 0)
                    add_row(group, shell_row)
                else:
                    add_row(group, row(caption, descriptions[name], widget))
                self.controls[name] = widget
            if title == 'Terminal':
                note = 'Shell changes apply to new tabs. Enter an executable path without arguments.'
            elif title == 'Behavior':
                note = 'Sessions keep running in the background. Choose Quit from the tray menu to exit.\n'
                note += 'Tray indicator is available.' if parent.tray.available else 'Tray indicator is unavailable: the window will minimize instead. Ubuntu requires AppIndicator support.'
            else:
                note = 'Appearance changes apply to existing and new terminals.'
            content.pack_start(label(note, 'pref-note', True), False, False, 0)
        self.error = Gtk.Label(xalign=0, margin=12)
        self.error.set_line_wrap(True)
        self.error.get_style_context().add_class('pref-error')
        self.error.set_no_show_all(True)
        self.get_content_area().pack_start(self.error, False, False, 0)
        self.connect('response', self._response)
        self.show_all()

    def values(self):
        data = {}
        for name, widget in self.controls.items():
            if name == 'font':
                data[name] = widget.get_font_name()
            elif name in ('foreground', 'background'):
                c = widget.get_rgba()
                data[name] = '#{:02x}{:02x}{:02x}'.format(round(c.red * 255), round(c.green * 255), round(c.blue * 255))
            elif name == 'cursor':
                data[name] = widget.get_active_id()
            elif isinstance(widget, Gtk.Switch):
                data[name] = widget.get_active()
            elif isinstance(widget, Gtk.SpinButton):
                data[name] = widget.get_value_as_int()
            else:
                data[name] = widget.get_text().strip()
        shell = data['shell']
        if shell and (not os.path.isabs(shell) or not os.path.isfile(shell) or not os.access(shell, os.X_OK)):
            raise ValueError('Shell must be an absolute path to an executable file.')
        return Settings.from_data(data)

    def _response(self, _dialog, response):
        if response == Gtk.ResponseType.APPLY:
            try:
                self.parent.apply_settings(self.values())
            except (OSError, ValueError) as error:
                self.error.set_text(str(error))
                self.error.show()
                return
        self.parent.dispatch(self.destroy)
