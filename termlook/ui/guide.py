"""Searchable keyboard reference and task-oriented help."""
from .gtk import Gdk, Gtk
from .shortcuts import SHORTCUTS
from .preferences_widgets import PreferenceBrowser, card, row, add_row, label


class Guide:
    def __init__(self, parent):
        self.parent = parent
        self.guide = None

    def show_guide(self, page=0):
        if self.guide is not None:
            self.browser.stack.set_visible_child_name('Keybinds' if page == 0 else 'Help')
            self.guide.show()
            self.guide.present()
            return
        self.guide = Gtk.Window(title='TermLook · Guide', transient_for=self.parent)
        self.guide.get_style_context().add_class('preferences-window')
        self.guide.set_default_size(780, 680)
        self.guide.set_destroy_with_parent(True)
        self.guide.connect('destroy', self.guide_closed)
        self.guide.connect('key-press-event', self.guide_keypress)
        self.browser = PreferenceBrowser()
        self.guide.add(self.browser)
        content = self.browser.add_page('Keybinds', 'A little less clicking.', 'Find a shortcut and keep your hands on the keyboard.')
        search = Gtk.SearchEntry(placeholder_text='Search actions or keys…')
        content.pack_start(search, False, False, 0)
        self.shortcut_sections = []
        groups = [
            ('Workspaces & tabs', ['New workspace', 'New tab', 'Close tab', 'Next tab', 'Previous tab', 'Rename tab']),
            ('Split panes', ['Split left / right', 'Split top / bottom', 'Close pane', 'Focus pane / show all']),
            ('Clipboard', ['Copy', 'Paste']),
            ('Application', ['Settings', 'Help', 'Quit']),
        ]
        shortcuts = dict(SHORTCUTS)
        for title, actions in groups:
            section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
            section.pack_start(label(title.upper(), 'pref-section'), False, False, 0)
            group = card()
            section.pack_start(group, False, False, 0)
            entries = []
            for action in actions:
                keys = shortcuts[action]
                keycaps = Gtk.Box(spacing=4)
                for key in keys.split('+'):
                    keycaps.pack_start(label('Enter' if key == 'Return' else key, 'keycap'), False, False, 0)
                item = row(action, None, keycaps)
                # Individual rows allow search without orphaned separators.
                item.get_style_context().add_class('shortcut-row')
                group.pack_start(item, False, False, 0)
                entries.append((item, (action + ' ' + keys).lower()))
            content.pack_start(section, False, False, 0)
            self.shortcut_sections.append((section, entries))
        self.empty = label('No shortcuts found. Try “pane”, “copy”, or “Ctrl”.', 'pref-muted', True)
        self.empty.set_no_show_all(True)
        content.pack_start(self.empty, False, False, 0)
        content.pack_start(label('Ctrl+C interrupts a command. Use Ctrl+Shift+C to copy selected text.', 'pref-note', True), False, False, 0)
        search.connect('search-changed', self.filter_shortcuts)

        help_page = self.browser.add_page('Help', 'Feel at home.', 'A quick guide to your workspaces, terminals, and panes.')
        for title, description in [
            ('01  Organize your work', 'Spaces live on the left; their tabs run across the top. Use + beside spaces for a new workspace, or + above the terminal for a new tab. Double-click a name to rename it.'),
            ('02  Build your layout', '◫ splits the focused pane left/right. ⬒ splits it top/bottom. For one above two below, split top/bottom, then split the bottom pane left/right. You can have up to four panes.'),
            ('03  Move things around', 'Drag the ⠿ Pane handle onto another pane header to swap terminals. A preview follows your pointer; release over the highlighted header. Drag dividers to resize panes.'),
            ('04  Focus or see everything', 'Click a terminal to focus it. □ expands that pane without stopping the others; click again to restore the layout. ⊞ arranges four panes in a grid.'),
            ('05  Close a pane, or take a break', '× on a pane or tab ends its session immediately. × at the right end of the tab bar hides TermLook in the tray by default, keeping sessions running. The tab bar is also the title bar: drag its empty space to move the window, double-click it to maximize. Choose Quit from the tray menu to exit completely.'),
            ('06  Make it yours', 'Open Settings with ⚙ or Ctrl+,. Choose fonts, colors, cursor style, spacing, and shell behavior. Apply changes saves your preferences; Cancel leaves them unchanged.'),
            ('What gets saved?', 'Workspaces, tabs, pane layouts, divider sizes, and settings are saved automatically. Restarting opens fresh shells; running processes and terminal output are not restored. Working directories update when your shell supports OSC 7.'),
        ]:
            group = card()
            group.pack_start(row(title, description), False, False, 0)
            help_page.pack_start(group, False, False, 0)
        self.guide.show_all()
        self.browser.stack.set_visible_child_name('Keybinds' if page == 0 else 'Help')

    def filter_shortcuts(self, search):
        words = search.get_text().lower().strip().split()
        any_visible = False
        for section, entries in self.shortcut_sections:
            matches = False
            for item, text in entries:
                visible = all(word in text.replace('return', 'return enter') for word in words)
                item.set_visible(visible)
                matches |= visible
            section.set_visible(matches)
            any_visible |= matches
        self.empty.set_visible(not any_visible)

    def guide_closed(self, *_):
        self.guide = None

    def guide_keypress(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.parent.dispatch(widget.destroy)
            return True
        return False
