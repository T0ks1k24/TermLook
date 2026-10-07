"""Application state without GTK objects or process handles."""
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4
from . import splits


def identity():
    return uuid4().hex


@dataclass
class Pane:
    name: str = 'main'
    cwd: str = field(default_factory=lambda: str(Path.home()))
    id: str = field(default_factory=identity)


@dataclass
class Tab(Pane):
    extra_panes: list[Pane] = field(default_factory=list)
    primary_pane: Pane | None = None
    active_pane_id: str | None = None
    zoomed: bool = False
    split_tree: object = None

    @property
    def panes(self):
        if self.primary_pane is None:
            self.primary_pane = Pane(name='pane 1', cwd=self.cwd, id=self.id)
        return [self.primary_pane] + self.extra_panes

    @property
    def active_pane(self):
        return next((p for p in self.panes if p.id == self.active_pane_id), self.panes[0])

    def tree(self):
        ids = [p.id for p in self.panes]
        if self.split_tree is None:
            self.split_tree = splits.default_tree(ids)
        return self.split_tree

    def swap_panes(self, source, target):
        ids = [p.id for p in self.panes]
        if source not in ids or target not in ids or source == target:
            return
        tree = splits.replace(self.tree(), source, '__swap__')
        tree = splits.replace(tree, target, source)
        self.split_tree = splits.replace(tree, '__swap__', target)

    def split(self, axis='horizontal'):
        if len(self.panes) >= 4:
            return
        tree = self.tree()
        active = self.active_pane.id
        pane = Pane(name=f'pane {len(self.panes) + 1}', cwd=self.active_pane.cwd)
        self.extra_panes.append(pane)
        self.split_tree = splits.replace(tree, active, splits.branch(axis, active, pane.id))
        self.active_pane_id = pane.id
        self.zoomed = False

    def close_pane(self, pane_id):
        if len(self.panes) == 1:
            return False
        pane = next((p for p in self.panes if p.id == pane_id), None)
        if pane is None:
            return False
        self.split_tree = splits.remove(self.tree(), pane_id)
        if pane is self.primary_pane:
            self.primary_pane = self.extra_panes.pop(0)
        else:
            self.extra_panes.remove(pane)
        self.cwd = self.primary_pane.cwd
        if self.active_pane_id == pane_id:
            self.active_pane_id = self.primary_pane.id
        if len(self.panes) == 1:
            self.zoomed = False
        return True


@dataclass
class Workspace:
    name: str = 'work'
    tabs: list[Tab] = field(default_factory=lambda: [Tab()])
    id: str = field(default_factory=identity)
    selected_id: str | None = None

    @property
    def selected(self):
        return next((t for t in self.tabs if t.id == self.selected_id), self.tabs[0])


@dataclass
class Layout:
    workspaces: list[Workspace]
    selected_id: str | None = None

    @classmethod
    def from_data(cls, data):
        workspaces = []
        for item in data:
            tabs = []
            for entry in item['tabs']:
                tab = Tab(name=entry['name'], cwd=entry['cwd'])
                tab.extra_panes = [Pane(name=f'pane {i + 2}', cwd=p['cwd'])
                                   for i, p in enumerate(entry.get('panes', [])[:3])]
                if 'split' in entry:
                    tab.split_tree = splits.decode(entry['split'], [p.id for p in tab.panes])
                tabs.append(tab)
            workspaces.append(Workspace(name=item['name'], tabs=tabs))
        return cls(workspaces)

    @property
    def selected(self):
        return next((w for w in self.workspaces if w.id == self.selected_id), self.workspaces[0])

    def find_tab(self, tab_id):
        for workspace in self.workspaces:
            for tab in workspace.tabs:
                if tab.id == tab_id:
                    return workspace, tab
        return None, None

    def to_data(self):
        result = []
        for workspace in self.workspaces:
            tabs = []
            for tab in workspace.tabs:
                entry = {'name': tab.name, 'cwd': tab.panes[0].cwd}
                if tab.extra_panes:
                    entry['panes'] = [{'cwd': p.cwd} for p in tab.extra_panes]
                    entry['split'] = splits.encode(tab.tree(), [p.id for p in tab.panes])
                tabs.append(entry)
            result.append({'name': workspace.name, 'tabs': tabs})
        return result

    def close_tab(self, tab_id):
        workspace, tab = self.find_tab(tab_id)
        if tab is None:
            return
        index = workspace.tabs.index(tab)
        selected = workspace.selected
        workspace.tabs.remove(tab)
        if not workspace.tabs:
            workspace.tabs.append(Tab(cwd=tab.cwd))
        if selected is tab:
            workspace.selected_id = workspace.tabs[min(index, len(workspace.tabs) - 1)].id

    def remove_workspace(self, workspace_id):
        workspace = next((w for w in self.workspaces if w.id == workspace_id), None)
        if workspace is None:
            return
        index = self.workspaces.index(workspace)
        selected = self.selected
        self.workspaces.remove(workspace)
        if not self.workspaces:
            self.workspaces.append(Workspace())
        if selected is workspace:
            self.selected_id = self.workspaces[min(index, len(self.workspaces) - 1)].id
