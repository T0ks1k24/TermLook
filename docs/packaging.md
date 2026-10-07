# Packaging and Windows support

## Status

The repository includes an initial **development Snap recipe**, not a verified release artifact. Build it on Ubuntu and test it before distributing it. Snapcraft packages Python and native dependencies; it does not convert the application into a native executable.

## Build a development Snap

Install Snapcraft and its build environment on Ubuntu:

```bash
sudo snap install snapcraft --classic
sudo snap install lxd
sudo lxd init --auto
sudo usermod -aG lxd "$USER"
```

If LXD is already configured, keep its existing configuration. After adding yourself to the group, log out and back in. LXD group membership grants powerful access to the host.

From the project root:

```bash
snapcraft --use-lxd
```

The recipe is `snapcraft.yaml` and uses Ubuntu's `core24` base with **classic confinement**. It bundles Python 3.12, PyGObject, GTK, VTE, and Ayatana AppIndicator. A typical x86-64 build produces `termlook_0.1.1_amd64.snap`.

Install the actual file produced by your build:

```bash
sudo snap install ./termlook_0.1.1_amd64.snap --dangerous --classic
snap run termlook
```

`--dangerous` allows a local package without a Store signature. `--classic` accepts the confinement the recipe requires. If an older strict or devmode build is installed, remove it first with `sudo snap remove termlook`; snapd keeps a snapshot of its data. Install a newer local build the same way.

Test shell startup, host commands, working directories, all split layouts, clipboard, settings persistence, and tray behavior on both X11 and Wayland. The desktop must provide an AppIndicator host for the tray icon.

### Why classic confinement

A strict or devmode snap runs in its own mount namespace with `core24` as the root filesystem and `~/snap/termlook/<revision>` as `$HOME`. Host shells such as `/usr/bin/zsh`, their configuration, and host commands are not visible there, so a confined build can only offer the base system's bash. Classic confinement runs TermLook on the host filesystem: tabs start the user's login shell with the real `$HOME`, and settings are shared with a source checkout in `~/.config/termlook`.

The GNOME extension does not support classic snaps, so the recipe bundles the GTK stack itself. `enable-patchelf` points the bundled binaries at this snap's libraries and the `core24` dynamic linker. `scripts/snap_launch.sh` sets the library, typelib, schema, GIO module, pixbuf loader, and input method paths, and records each original value in `TERMLOOK_SNAP_ORIG_<NAME>`. Before spawning a shell, `termlook.services.terminal.shell_environment()` restores those values and removes `SNAP*` variables, so shells and programs started from TermLook see the user's environment rather than the bundled runtime. Host themes, icons, fonts, and GNOME settings remain visible.

### Before a public release

This recipe is `grade: devel`. The classic build has been tested only on Ubuntu 24.04; test other distributions and desktops before distributing it. Store publication of a classic snap requires manual approval. The Store name must also be registered and available.

Packaging copies only runtime sources, excluding repository metadata and existing Snap artifacts.

Official references: [GNOME extension](https://ubuntu.com/docs/snapcraft/9/reference/extensions/gnome-extension/), [confinement](https://snapcraft.io/docs/explanation/security/snap-confinement/), [classic review criteria](https://snapcraft.io/docs/reference/administration/reviewing-classic-confinement-snaps/).

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
