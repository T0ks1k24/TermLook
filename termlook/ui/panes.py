"""Up to four live terminals per tab, with a reversible focus mode."""
from .gtk import Gtk, Gdk, GLib
from .widgets import button
from .pane_drag import PaneDrag


class PaneGrid(Gtk.Box):
    def __init__(self, tab, controller, dispatch):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.save_source = None
        self.tab = tab
        self.controller = controller
        self.dispatch = dispatch
        self.cells = {}
        self.headers = {}
        self.signature = None
        self.drag = PaneDrag(self)

    def render(self, sessions):
        panes = self.tab.panes
        live = {p.id for p in panes}
        for pid in list(self.cells):
            if pid not in live:
                self.cells.pop(pid).destroy()
                self.headers.pop(pid)
                self.drag.grips.pop(pid, None)
        for index, pane in enumerate(panes):
            if pane.id not in self.cells:
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                box.get_style_context().add_class('terminal-pane')
                header = Gtk.Box()
                header.set_no_show_all(True)
                header.get_style_context().add_class('pane-header')
                label = Gtk.Label(xalign=0)
                label.set_margin_start(10)
                grip = Gtk.EventBox()
                grip.add(label)
                grip.set_tooltip_text('Drag onto another pane header to swap terminals')
                targets = [Gtk.TargetEntry.new('application/x-termlook-pane', Gtk.TargetFlags.SAME_APP, 0)]
                grip.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, targets, Gdk.DragAction.MOVE)
                grip.connect('drag-data-get', self._drag_data, pane.id)
                header.drag_dest_set(Gtk.DestDefaults.ALL, targets, Gdk.DragAction.MOVE)
                header.connect('drag-data-received', self._drop, pane.id)
                self.drag.attach(grip, header, pane.id)
                header.pack_start(grip, True, True, 0)
                header.pack_end(button('×', 'Close pane', lambda _, pid=pane.id:
                    self.dispatch(lambda: self.controller.close_pane(pid))), False, False, 0)
                box.pack_start(header, False, False, 0)
                box.pack_start(sessions[pane.id].widget, True, True, 0)
                self.cells[pane.id] = box
                self.headers[pane.id] = (header, label)
            self.headers[pane.id][1].set_text(f'⠿  Pane {index + 1}')
        tree = self.tab.active_pane.id if self.tab.zoomed else self.tab.tree()
        signature = (id(self.tab.split_tree), self._topology(tree))
        if signature != self.signature:
            # Detach live terminals before disposing old split containers.
            for cell in self.cells.values():
                parent = cell.get_parent()
                if parent:
                    parent.remove(cell)
            for child in self.get_children():
                child.destroy()
            self.pack_start(self._build(tree), True, True, 0)
            self.signature = signature
        self.show_all()
        for header, _label in self.headers.values():
            header.set_no_show_all(False)
            header.show_all()
            header.set_no_show_all(True)
            header.set_visible(len(panes) > 1)
        self.highlight()

    def _topology(self, tree):
        if isinstance(tree, str):
            return tree
        return (tree['axis'], self._topology(tree['first']), self._topology(tree['second']))

    def _build(self, tree):
        if isinstance(tree, str):
            return self.cells[tree]
        horizontal = tree['axis'] == 'horizontal'
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL if horizontal else Gtk.Orientation.VERTICAL)
        paned.set_wide_handle(True)
        paned.pack1(self._build(tree['first']), True, True)
        paned.pack2(self._build(tree['second']), True, True)
        paned.resizing = False
        def pressed(_widget, event):
            if event.button == 1:
                paned.resizing = True
            return False
        def released(_widget, event):
            if event.button == 1:
                paned.resizing = False
            return False
        paned.connect('button-press-event', pressed)
        paned.connect('button-release-event', released)
        applying = [False]
        last_size = [0]

        def allocated(widget, allocation):
            size = (allocation.width if horizontal else allocation.height) - 6
            if size > 0 and size != last_size[0]:
                last_size[0] = size
                applying[0] = True
                widget.set_position(round(size * tree['ratio']))
                applying[0] = False

        def moved(widget, _param):
            if applying[0] or not widget.resizing or last_size[0] <= 0 or not widget.get_mapped():
                return
            tree['ratio'] = max(0.05, min(0.95, widget.get_position() / last_size[0]))
            if self.save_source:
                GLib.source_remove(self.save_source)
            self.save_source = GLib.timeout_add(250, self._save)

        paned.connect('size-allocate', allocated)
        paned.connect('notify::position', moved)
        return paned

    def _save(self):
        self.save_source = None
        self.dispatch(self.controller.persist)
        return False

    def _drag_data(self, _widget, _context, selection, _info, _time, pane_id):
        selection.set(selection.get_target(), 8, (self.tab.id + ':' + pane_id).encode())

    def _drop(self, _widget, context, _x, _y, selection, _info, time, target):
        try:
            tab_id, source = bytes(selection.get_data()).decode().split(':', 1)
            valid = tab_id == self.tab.id and source in self.cells and target in self.cells
        except (ValueError, TypeError, UnicodeError):
            valid = False
        valid = valid and source != target
        self.drag.clear()
        if valid:
            def swap():
                self.controller.swap_panes(tab_id, source, target)
                self.drag.landed(source, target)
            self.dispatch(swap)
        Gtk.drag_finish(context, valid, False, time)

    def highlight(self):
        for pid, cell in self.cells.items():
            context = cell.get_style_context()
            if pid == self.tab.active_pane.id and len(self.cells) > 1:
                context.add_class('focused')
            else:
                context.remove_class('focused')

    def dispose(self):
        self.drag.close()
        if self.save_source:
            GLib.source_remove(self.save_source)
            self.save_source = None
        # Hidden zoomed cells are detached from this grid but still owned here.
        for cell in self.cells.values():
            cell.destroy()
        self.cells.clear()
        self.headers.clear()
        self.destroy()
