# TermLook

A minimal dark terminal for Ubuntu, built with Python, GTK 3, and VTE. Workspaces appear on the left, with the selected workspace's terminal tabs across the top. Each tab runs its own shell.

In **0.1.1**, restored tabs start their terminals only when first selected. Unopened
tabs retain their names, directories, and split layouts without allocating terminal
widgets or starting shells. Once opened, sessions stay alive across tab and workspace
switches, including background commands and shell variables. Close a tab or pane to
end its session; idle sessions are not terminated automatically.

## Run on Ubuntu

```bash
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
cd /path/to/TermLook
/usr/bin/python3 -m termlook
```

Use the system Python: GTK and VTE are installed through apt, not pip.

## Application icon and launcher

```bash
/usr/bin/python3 scripts/install_desktop.py
```

Open **TermLook** from the application menu and optionally pin it to your dock. The launcher and icon are installed for the current user without sudo. The launcher points to this checkout; run the installer again if you move the project. The window also uses the bundled SVG icon when launched through Python.

## Settings and background mode

Click `⚙` or press `Ctrl+,` to open Settings. Use the Appearance, Terminal, and Behavior sections; each option includes a short explanation. You can configure:

- Font, text and background colors, cursor shape, and blinking.
- Terminal padding, sidebar width, and scrollback length.
- Audible bell and automatic scrolling.
- Shell executable path, applied to new tabs.
- Whether closing the window hides it in the tray.

**Apply** saves preferences to `~/.config/termlook/settings.json`, respecting `XDG_CONFIG_HOME`. Appearance changes apply immediately without restarting sessions. **Cancel** keeps the previous settings.

By default, the window's close button **hides the application** while commands keep running. The top-panel icon provides **Open TermLook / Settings / Quit**. Launching TermLook again also restores the main window. Choose **Quit** or press `Ctrl+Shift+Q` to exit completely. Tab close buttons still end their individual sessions.

For the tray indicator on Ubuntu:

```bash
sudo apt install gir1.2-ayatanaappindicator3-0.1 gnome-shell-extension-appindicator
```

Enable the Ubuntu AppIndicators extension in GNOME. The tab bar doubles as the title bar: drag its empty space, or the area beside “spaces”, to move the window, double-click it to maximize, and right-click it for the window menu. `×` at its right end, next to `+`, hides TermLook in the tray. If a tray host is unavailable, `×` minimizes the window so it remains accessible from the taskbar. If the tray host disappears while TermLook is hidden, the window reappears.

## Split terminals

Each tab supports **1–4 terminal panes** with independent shell sessions.

- `◫` or `Ctrl+Shift+E`: split the focused pane left/right (maximum four).
- `⬒` or `Ctrl+Shift+D`: split the focused pane top/bottom.
- Drag a divider to resize panes. Drag the `⠿ Pane` handle onto another pane header to swap terminals. A live thumbnail follows the pointer, the source fades, and valid targets highlight with “Release to swap”.
- `⊞`: create a four-pane 2×2 grid.
- Click a terminal to focus it; the active pane has a subtle border.
- `□` or `Ctrl+Shift+Return`: show only the focused pane; toggle again to restore the grid. Hidden panes keep running.
- `×` in a pane header or `Ctrl+Shift+X`: close that pane. Closing the last pane closes the tab.

Splits can be nested in either direction. For one terminal above two others, split top/bottom, focus the bottom terminal, then split left/right. Reverse the process or focus a different pane for other arrangements. Layouts, divider proportions, pane order, and directories are saved. Restarting creates fresh shells, just like regular tabs.

## Controls

| Action | Shortcut |
| --- | --- |
| Split left / right | Ctrl+Shift+E |
| Split top / bottom | Ctrl+Shift+D |
| Close pane | Ctrl+Shift+X |
| Focus pane / show all | Ctrl+Shift+Return |
| New tab | Ctrl+Shift+T |
| New workspace | Ctrl+Shift+N |
| Close tab | Ctrl+Shift+W |
| Next / previous tab | Ctrl+Tab / Ctrl+Shift+Tab |
| Copy / paste | Ctrl+Shift+C / Ctrl+Shift+V |
| Rename tab | F2 |
| Help | F1 |
| Settings | Ctrl+, |
| Quit | Ctrl+Shift+Q |

Select a workspace on the left to show its terminal tabs at the top. The `+` beside spaces creates a workspace; the `+` in the top bar creates a terminal. Each workspace remembers its selected tab during the application session. Ctrl+Tab cycles through the current workspace's tabs.

Double-click a workspace or tab name to rename it; F2 renames the active terminal. `×` deletes a workspace or closes a tab **without confirmation**, ending its sessions. Closing the last tab creates a fresh `main` tab; deleting the last workspace creates `work`.

At the bottom, `⌘` opens **Keybinds** and `?` opens **Help**. Keybinds groups shortcuts by task and includes a search field for actions or keys. Help provides short guides to workspaces, split panes, dragging, and background mode. Escape closes the help window. Right-click in the terminal for copy and paste. Ctrl+C interrupts the current command. Hover over a tab to see its working directory.

The layout is saved to `~/.config/termlook/layout.json` (or `$XDG_CONFIG_HOME/termlook/layout.json`). Restarting opens fresh shell sessions; output and processes are not restored. The working directory updates when the shell sends OSC 7; otherwise the initial directory is retained.

## Verification

```bash
/usr/bin/python3 -m unittest discover -s tests
# For GUI testing without a display: sudo apt install xvfb
G_DEBUG=fatal-criticals xvfb-run -a /usr/bin/python3 tests/smoke_gui.py
G_DEBUG=fatal-criticals dbus-run-session -- xvfb-run -a /usr/bin/python3 tests/smoke_lazy.py
```

## Architecture

```text
termlook/
  app.py                 # Application setup and dependency wiring
  __main__.py            # python -m termlook
  core/
    models.py            # Tab, Workspace, Layout; no GTK dependencies
    splits.py            # Split tree operations and layout validation
    settings.py          # Typed and validated preferences
    controller.py        # User actions and model/view coordination
  services/
    storage.py           # JSON loading and atomic saving
    preferences.py       # Settings persistence
    tray.py              # AppIndicator and panel availability
    terminal.py          # VTE sessions: shell environment, startup, cancellation, disposal
  ui/
    window.py            # Window composition and widget lifecycle
    navigation.py        # Workspace sidebar and terminal tab widgets
    panes.py             # Terminal pane grid and focus mode
    shortcuts.py         # Keyboard bindings
    guide.py             # Help window
    settings.py          # Settings dialog
    dialogs.py           # Naming dialogs
    widgets.py           # Shared UI components
    theme.py             # CSS
    gtk.py               # GTK/VTE imports
  assets/
    io.termlook.TermLook.svg
scripts/
  run.py                 # Launch from any working directory
  install_desktop.py     # Install application icon and menu entry
  snap_launch.sh         # Classic snap entry point for the bundled GTK stack
tests/                  # Model, persistence, and GTK/VTE tests
```

`core` does not import GTK. The controller receives a save function and a view; `app.py` wires them together. Models contain data and stable IDs rather than widget references. The window owns the terminal sessions, and each session manages its signals and asynchronous startup. There are no mixin classes.

Add actions to `core/controller.py`, their buttons to `ui/`, and external integrations to `services/`. UI actions run through `Window.dispatch()`, so widget changes happen after the current GTK event finishes. Closing a session disconnects its signals and cancels startup; its widget is retained until the startup callback completes.

## Snap and Windows

See [Packaging and Windows support](docs/packaging.md) for the development Snap recipe, build commands, WSLg setup, and the work required for a native Windows port. The Snap recipe uses classic confinement so tabs run your own shell and configuration; it is a development build and has not yet been tested as a release.

## Contributing

See [Contributing](CONTRIBUTING.md) for development setup, checks, and pull requests.
Project authors are listed in [Contributors](CONTRIBUTORS.md).

## License

TermLook is licensed under the [MIT License](LICENSE).
