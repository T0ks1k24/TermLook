"""Application actions coordinating a pure model, persistence and a view."""
from .models import Tab, Workspace


class Controller:
    def __init__(self, layout, save):
        self.layout = layout
        self.save = save
        self.view = None
        self.closed = False
        self.saved_data = None

    def refresh(self):
        if not self.closed:
            self.view.render(self.layout)
            self.persist()

    def persist(self):
        if self.closed:
            return
        try:
            data = self.layout.to_data()
            if data != self.saved_data:
                self.save(data)
                self.saved_data = data
            self.view.show_error(None)
        except OSError as error:
            self.view.show_error(f'Could not save layout: {error}')

    def select_workspace(self, workspace_id):
        if any(w.id == workspace_id for w in self.layout.workspaces):
            self.layout.selected_id = workspace_id
            self.view.render(self.layout)

    def select_tab(self, tab_id):
        workspace, tab = self.layout.find_tab(tab_id)
        if tab:
            self.layout.selected_id = workspace.id
            workspace.selected_id = tab.id
            self.view.render(self.layout)

    def new_workspace(self):
        name = self.view.ask('New workspace', 'project')
        if name and not self.closed:
            workspace = Workspace(name=name)
            self.layout.workspaces.append(workspace)
            self.layout.selected_id = workspace.id
            self.refresh()

    def new_tab(self):
        workspace = self.layout.selected
        names = {t.name for t in workspace.tabs}
        number = 1
        while f'terminal {number}' in names:
            number += 1
        tab = Tab(name=f'terminal {number}', cwd=workspace.selected.active_pane.cwd)
        workspace.tabs.append(tab)
        workspace.selected_id = tab.id
        self.refresh()

    def rename_tab(self, tab_id=None):
        _, tab = self.layout.find_tab(tab_id or self.layout.selected.selected.id)
        if tab:
            name = self.view.ask('Tab name', tab.name)
            if name and not self.closed:
                tab.name = name
                self.refresh()

    def rename_workspace(self, workspace_id):
        workspace = next((w for w in self.layout.workspaces if w.id == workspace_id), None)
        if workspace:
            name = self.view.ask('Workspace name', workspace.name)
            if name and not self.closed:
                workspace.name = name
                self.refresh()

    def close_tab(self, tab_id=None):
        self.layout.close_tab(tab_id or self.layout.selected.selected.id)
        self.refresh()

    def remove_workspace(self, workspace_id):
        self.layout.remove_workspace(workspace_id)
        self.refresh()

    def cycle_tab(self, step):
        workspace = self.layout.selected
        index = workspace.tabs.index(workspace.selected)
        self.select_tab(workspace.tabs[(index + step) % len(workspace.tabs)].id)

    def split_pane(self, axis='horizontal'):
        self.layout.selected.selected.split(axis)
        self.refresh()

    def four_panes(self):
        tab = self.layout.selected.selected
        while len(tab.panes) < 4:
            tab.split()
        from .splits import default_tree
        tab.split_tree = default_tree([p.id for p in tab.panes])
        tab.zoomed = False
        self.refresh()

    def swap_panes(self, tab_id, source, target):
        _, tab = self.layout.find_tab(tab_id)
        if tab:
            tab.swap_panes(source, target)
            self.refresh()

    def close_pane(self, pane_id=None):
        tab = self.layout.selected.selected
        pane_id = pane_id or tab.active_pane.id
        if len(tab.panes) == 1:
            self.close_tab(tab.id)
        elif tab.close_pane(pane_id):
            self.refresh()

    def toggle_zoom(self):
        tab = self.layout.selected.selected
        if len(tab.panes) > 1:
            tab.zoomed = not tab.zoomed
            self.view.render(self.layout)

    def shutdown(self):
        if not self.closed:
            self.persist()
            self.closed = True
