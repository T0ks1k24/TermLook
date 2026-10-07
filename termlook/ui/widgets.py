"""Small reusable UI helpers."""
from .gtk import Gdk, Gtk

def color(value):
    result = Gdk.RGBA()
    result.parse(value)
    return result


def button(text, tooltip, callback):
    widget = Gtk.Button(label=text)
    widget.set_tooltip_text(tooltip)
    widget.connect("clicked", callback)
    return widget
