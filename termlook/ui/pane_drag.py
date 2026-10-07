"""Pane drag affordances, live thumbnails and target feedback."""
from .gtk import Gdk, GLib, Gtk
from gi.repository import GdkPixbuf


class PaneDrag:
    def __init__(self, grid):
        self.grid = grid
        self.source = None
        self.target = None
        self.timer = None
        self.grips = {}

    def attach(self, grip, header, pane_id):
        self.grips[pane_id] = grip
        grip.pane_grid = self.grid
        grip.pane_id = pane_id
        grip.get_style_context().add_class('pane-grip')
        grip.connect('realize', lambda widget: self.cursor(widget, 'grab'))
        grip.connect('drag-begin', self.begin, pane_id)
        grip.connect('drag-end', self.end)
        header.connect('drag-motion', self.motion, pane_id)
        header.connect('drag-leave', self.leave)

    def cursor(self, widget, name):
        if widget.get_window():
            widget.get_window().set_cursor(Gdk.Cursor.new_from_name(widget.get_display(), name))

    def begin(self, grip, context, pane_id):
        self.clear()
        self.source = pane_id
        cell = self.grid.cells[pane_id]
        # Capture before fading the source, so the floating preview stays crisp.
        top = cell.get_toplevel()
        position = cell.translate_coordinates(top, 0, 0)
        if position and top.get_window():
            width, height = cell.get_allocated_width(), cell.get_allocated_height()
            snapshot = Gdk.pixbuf_get_from_window(top.get_window(), position[0], position[1], width, height)
            if snapshot:
                scale = min(280 / width, 180 / height, 1)
                thumbnail = snapshot.scale_simple(max(1, int(width * scale)), max(1, int(height * scale)), GdkPixbuf.InterpType.BILINEAR)
                Gtk.drag_set_icon_pixbuf(context, thumbnail, 24, 16)
        cell.get_style_context().add_class('drag-source')
        self.cursor(grip, 'grabbing')
        for pid, (header, label) in self.grid.headers.items():
            if pid != pane_id:
                header.get_style_context().add_class('drop-ready')
                label.set_text('⠿  Drop here to swap')

    def motion(self, _header, context, _x, _y, time, pane_id):
        source_widget = Gtk.drag_get_source_widget(context)
        valid = (source_widget is not None and getattr(source_widget, 'pane_grid', None) is self.grid
                 and source_widget.pane_id != pane_id)
        self.clear_target()
        if valid:
            self.target = pane_id
            self.grid.cells[pane_id].get_style_context().add_class('drop-target')
            self.grid.headers[pane_id][1].set_text('↔  Release to swap')
        Gdk.drag_status(context, Gdk.DragAction.MOVE if valid else Gdk.DragAction(0), time)
        return True

    def clear_target(self):
        if self.target in self.grid.cells:
            self.grid.cells[self.target].get_style_context().remove_class('drop-target')
            self.grid.headers[self.target][1].set_text('⠿  Drop here to swap')
        self.target = None

    def leave(self, *_):
        self.clear_target()

    def end(self, grip, _context):
        self.cursor(grip, 'grab')
        self.clear()

    def clear(self):
        self.clear_target()
        self.source = None
        for index, pane in enumerate(self.grid.tab.panes):
            if pane.id in self.grid.cells:
                self.grid.cells[pane.id].get_style_context().remove_class('drag-source')
                header, label = self.grid.headers[pane.id]
                header.get_style_context().remove_class('drop-ready')
                label.set_text(f'⠿  Pane {index + 1}')

    def landed(self, source, target):
        self.clear_flash()
        for pid in (source, target):
            if pid in self.grid.cells:
                self.grid.cells[pid].get_style_context().add_class('pane-landed')
        self.timer = GLib.timeout_add(450, self.clear_flash)

    def clear_flash(self):
        if self.timer:
            GLib.source_remove(self.timer)
            self.timer = None
        for cell in self.grid.cells.values():
            cell.get_style_context().remove_class('pane-landed')
        return False

    def close(self):
        self.clear_flash()
        self.grips.clear()
