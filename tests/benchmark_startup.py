"""Linux startup sample with isolated settings and /bin/sh.

Run: timeout 90s dbus-run-session -- xvfb-run -a /usr/bin/python3 tests/benchmark_startup.py 24
ready_ms measures window creation and shell readiness after GTK/application setup.
rss_mib covers only the application process, not its child shells. Timing includes
100 ms polling granularity; compare repeated runs on the same machine and desktop.
"""
import json, os, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from termlook.app import create_window, install_theme
from termlook.ui.gtk import Gtk, GLib
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    count=int(sys.argv[1]) if len(sys.argv) > 1 else 24
    if not 1 <= count <= 1000:
        raise SystemExit("Choose between 1 and 1000 tabs")
    (root/'layout.json').write_text(json.dumps([{'name':'bench','tabs':[{'name':f'tab {i}','cwd':directory} for i in range(count)]}]))
    (root/'settings.json').write_text(json.dumps({'shell':'/bin/sh'}))
    app=Gtk.Application(application_id='io.termlook.Benchmark')
    app.register(None)
    install_theme()
    started=time.monotonic()
    window=create_window(app, root/'layout.json')
    def finish():
        if any(s.pending for s in window.sessions.values()):
            return True
        rss=int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')/1024/1024
        print(json.dumps({'tabs':count,'sessions':len(window.sessions),'grids':len(window.pane_grids),'ready_ms':round((time.monotonic()-started)*1000),'rss_mib':round(rss,1)}),flush=True)
        window.destroy()
        GLib.timeout_add(500, Gtk.main_quit)
        return False
    GLib.timeout_add(100,finish)
    Gtk.main()
