"""Shared visual building blocks for settings and help."""
from .gtk import Gtk


def label(text, style=None, wrap=False):
    widget = Gtk.Label(label=text, xalign=0)
    if style:
        widget.get_style_context().add_class(style)
    if wrap:
        widget.set_line_wrap(True)
        widget.set_max_width_chars(48)
    return widget


def page(title, subtitle):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18, margin=28)
    heading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
    heading.pack_start(label(title, 'pref-title'), False, False, 0)
    heading.pack_start(label(subtitle, 'pref-muted', True), False, False, 0)
    box.pack_start(heading, False, False, 0)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.add(box)
    return scroll, box


def card():
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.get_style_context().add_class('pref-card')
    return box


def row(title, description, control=None):
    box = Gtk.Box(spacing=20, margin=14)
    text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
    text.pack_start(label(title, 'pref-row-title'), False, False, 0)
    if description:
        text.pack_start(label(description, 'pref-muted', True), False, False, 0)
    box.pack_start(text, True, True, 0)
    if control:
        control.set_valign(Gtk.Align.CENTER)
        box.pack_end(control, False, False, 0)
    return box


def add_row(container, widget):
    if container.get_children():
        container.pack_start(Gtk.Separator(), False, False, 0)
    container.pack_start(widget, False, False, 0)


class PreferenceBrowser(Gtk.Box):
    def __init__(self):
        super().__init__()
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, transition_duration=140)
        sidebar = Gtk.StackSidebar(stack=self.stack)
        sidebar.set_size_request(155, -1)
        sidebar.get_style_context().add_class('pref-sidebar')
        self.pack_start(sidebar, False, False, 0)
        self.pack_start(self.stack, True, True, 0)

    def add_page(self, name, title, subtitle):
        scroll, content = page(title, subtitle)
        self.stack.add_titled(scroll, name, name)
        return content
