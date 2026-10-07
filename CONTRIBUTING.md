# Contributing to TermLook

Bug reports, fixes, documentation, and improvements are welcome. For larger changes,
open an issue first to discuss the problem and proposed approach.

## Development setup

Fork the repository, clone your fork, and create a branch for your change.
On Ubuntu, install the runtime and test dependencies:

```bash
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91 gir1.2-ayatanaappindicator3-0.1 xvfb xauth dbus-x11
/usr/bin/python3 -m termlook
```

Use system Python so it can load the GTK and VTE packages installed through apt.
See the [README](README.md) for application behavior and the code structure, and
[packaging documentation](docs/packaging.md) for local Snap builds.

## Making changes

- Keep each pull request focused on one change and follow the surrounding style.
- Keep `termlook/core` independent of GTK. Put shell and system integrations in
  `termlook/services`, and UI changes in `termlook/ui`.
- Add or update regression tests for changed behavior and bug fixes.
- Update user documentation when controls or behavior change.
- Do not commit generated Snap packages, Python caches, or credentials.

## Checking your changes

Run these commands from the repository root:

```bash
/usr/bin/python3 -m unittest discover -s tests -v
/usr/bin/python3 -m compileall -q termlook scripts tests
sh -n scripts/snap_launch.sh
G_DEBUG=fatal-criticals GSETTINGS_BACKEND=memory NO_AT_BRIDGE=1 \
  timeout 90s dbus-run-session -- xvfb-run -a /usr/bin/python3 tests/smoke_gui.py
G_DEBUG=fatal-criticals GSETTINGS_BACKEND=memory NO_AT_BRIDGE=1 \
  timeout 90s dbus-run-session -- xvfb-run -a /usr/bin/python3 tests/smoke_lazy.py
```

For UI or terminal changes, also test the affected behavior in a real desktop
session. Include your Ubuntu version and whether you used X11 or Wayland when
reporting desktop-specific behavior.

## Submitting a pull request

Target `main`. Explain the problem, what changed, and how you tested it. Link any
related issue and include screenshots when they help explain a visible change.
Use descriptive commit messages. The maintainer, @T0ks1k24, reviews contributions
and decides whether to merge them.

For bug reports, include steps to reproduce, expected and actual behavior, and
whether you ran from source or a Snap. Remove private terminal output and paths
from logs before sharing them.

Contributions are made under the project's [MIT license](LICENSE).
