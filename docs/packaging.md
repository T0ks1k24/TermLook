# Packaging and Windows support

## Debian package (Ubuntu 24.04)

Build from the repository root without sudo:

```bash
/usr/bin/python3 scripts/build_deb.py
sudo apt install ./dist/termlook_0.1.1_all.deb
termlook
```

The version comes from `VERSION`. The package includes the Python application,
launcher, desktop entry, icon, and MIT license. GTK, VTE, and Python are system
package dependencies installed by APT. The optional tray backend is recommended.
No isolated runtime is used: shells run directly in the host environment.

CI builds the package and tests installation, desktop-file validity, GUI startup,
host shell commands, working directory, environment, and application shutdown on
Ubuntu 24.04 amd64. The package is `Architecture: all` because it contains Python
sources; other distributions and architectures still need validation.

Install an updated package using the same `apt install ./...deb` command.
`sudo apt remove termlook` removes the application while preserving user settings.
No automatic-update APT repository is configured.

For installed-package testing with `xvfb`, `xauth`, `xdotool`, and `dbus-x11` installed:

```bash
G_DEBUG=fatal-criticals GSETTINGS_BACKEND=memory NO_AT_BRIDGE=1 \
  timeout 90s dbus-run-session -- xvfb-run -a /usr/bin/python3 tests/smoke_deb.py
```

## Windows: run the current application with WSLg

The current implementation uses Linux shell paths, VTE PTYs, and AppIndicator. There is no supported native Windows build in this repository.

On a Windows version supporting WSLg (Windows 11, or Windows 10 build 19044 or later), run in an elevated PowerShell:

```powershell
wsl --install -d Ubuntu
wsl --update
```

Restart Windows if prompted. Open Ubuntu and install dependencies:

```bash
sudo apt update
sudo apt install python3 python3-gi librsvg2-common gir1.2-gtk-3.0 gir1.2-vte-2.91
cd /path/to/TermLook
/usr/bin/python3 -m termlook
```

Place or clone the project inside Ubuntu, or access an existing Windows checkout through `/mnt/c/...`. WSLg displays the Linux window on the Windows desktop. This runs Linux shells, not a native PowerShell terminal. The Ubuntu tray integration is not a Windows notification-area implementation; disable “Close window to tray” in Settings if needed.

Microsoft's guide: [Run Linux GUI apps with WSL](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps).

## Native Windows installer: a separate port

Before producing an `.exe` or `.msi`, implement and test:

1. A Windows terminal backend using ConPTY and a compatible terminal renderer, in place of VTE's Unix PTY integration.
2. Windows-compatible GUI dependencies (or a cross-platform frontend), clipboard, and notification-area integration.
3. PowerShell/cmd startup, process cleanup, resizing, Unicode, and ANSI output.
4. Platform-specific configuration paths and packaging of all assets and native libraries.
5. A build on Windows, followed by installer creation and signing as appropriate.

`core/` can largely be reused; `services/terminal.py`, `services/tray.py`, and the GTK/VTE-dependent UI need adaptation. Running PyInstaller against the current Linux application does not provide that port. Windows builds should be produced and tested on Windows.

Microsoft's backend reference: [Pseudoconsoles (ConPTY)](https://learn.microsoft.com/en-us/windows/console/pseudoconsoles).
