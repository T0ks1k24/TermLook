"""Naming dialog."""
from .gtk import Gtk

def ask(parent, title, initial=""):
    dialog = Gtk.Dialog(title=title, transient_for=parent, modal=True)
    dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
    entry = Gtk.Entry(text=initial, activates_default=True)
    entry.set_margin_top(16)
    entry.set_margin_bottom(16)
    entry.set_margin_start(16)
    entry.set_margin_end(16)
    dialog.get_content_area().add(entry)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.show_all()
    response = dialog.run()
    value = entry.get_text().strip()[:80]
    dialog.destroy()
    return value if response == Gtk.ResponseType.OK and value else None
