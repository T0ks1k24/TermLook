"""Quiet charcoal palette and rounded browser-like surfaces."""
CSS = b"""
.preferences-window { background: #1c1d24; }
.pref-sidebar { background: #18191f; border-right: 1px solid #292b35; padding: 16px 8px; }
.pref-sidebar list { background: #18191f; }
.pref-sidebar row label { color: #a9adbd; }
.pref-sidebar row:selected label { color: #eef0f7; }
.preferences-window viewport { border: none; }
.pref-sidebar row { padding: 9px 12px; margin: 3px 0; }
.pref-title { font-size: 23px; font-weight: bold; color: #efeff5; }
.pref-muted { color: #9699aa; font-size: 12px; }
.pref-row-title { color: #dedfe9; font-size: 13px; font-weight: 500; }
.pref-card { background: #252730; border: 1px solid #30333e; border-radius: 12px; }
.pref-card separator { background: #323540; min-height: 1px; margin: 0 14px; }
.pref-note { color: #a6bdb7; font-size: 12px; }
.pref-section { color: #9399ae; font-size: 10px; font-weight: bold; letter-spacing: 1px; }
button.pref-primary { background: #a5c7c0; color: #182923; font-weight: bold; padding: 9px 18px; }
button.pref-primary:hover { background: #bddbd5; }
.pref-error { color: #efa5a5; }
.preferences-window switch { border-radius: 14px; background: #383c49; }
.preferences-window switch:checked { background: #7ba69b; }
.preferences-window switch slider { border-radius: 12px; background: #e4ece9; }
.preferences-window entry, .preferences-window spinbutton { background: #1e2028; color: #e1e3ed; border: 1px solid #3a3e4c; border-radius: 7px; }
.preferences-window .keycap { background: #353947; border: 1px solid #464c5d; border-bottom-width: 2px; border-bottom-color: #596174; border-radius: 5px; padding: 5px 7px; color: #e0e4f0; font-size: 11px; }

.terminal-pane { border: 1px solid transparent; border-radius: 6px; transition: border-color 160ms ease, opacity 160ms ease; }
.terminal-pane.drag-source { opacity: 0.48; }
.terminal-pane.drop-target, .terminal-pane.pane-landed { border-color: #a5c7c0; }
.pane-header { transition: background-color 160ms ease; border-radius: 5px; }
.pane-header.drop-ready { background: #2d3539; }
.drop-target .pane-header { background: #405653; color: #e0f5ef; }
.pane-grip { padding: 4px 8px; border-radius: 5px; }
.pane-grip:hover { background: #353945; color: #e0e4ee; }
.terminal-pane.focused { border-color: #626b83; }
paned > separator { min-width: 6px; min-height: 6px; background: #343744; transition: background-color 150ms ease; }
paned > separator:hover, paned > separator:active { background: #9ab8b3; }
.pane-header { color: #92949f; font-size: 10px; }
window { background: #191a20; color: #c6c6cd; }
headerbar { background: #191a20; border: none; box-shadow: none; min-height: 28px; }
headerbar .title { font-size: 11px; font-weight: normal; color: #777983; }
window.main-window { border-radius: 0; }
window.main-window decoration { border-radius: 0; box-shadow: 0 4px 16px 2px rgba(0, 0, 0, 0.45); }
window.main-window decoration:backdrop { box-shadow: 0 4px 16px 2px rgba(0, 0, 0, 0.25); }
window.main-window > .titlebar, window.main-window > .titlebar:backdrop { min-height: 0; padding: 0; background: #191a20; color: #c6c6cd; border: none; border-radius: 0; box-shadow: none; }
#heading { padding: 6px; }
button { background: transparent; color: #92949f; border: none; box-shadow: none; border-radius: 7px; min-height: 22px; padding: 3px 8px; }
button:hover { background: #2d2f38; color: #eeedf3; }
button:focus { outline-color: #8c92aa; }
#sidebar { padding: 6px; }
#brand { color: #777983; font-size: 11px; }
list { background: transparent; }
row { border-radius: 8px; margin: 2px 0; padding: 3px; }
row:selected { background: #2b2d36; }
row:selected label { color: #e3e3e9; }
#surface { background: #202127; }
#tabbar { background: #202127; padding: 6px; }
.terminal-tab { border-radius: 7px; margin-right: 4px; }
.terminal-tab.active { background: #32343e; }
.terminal-tab.active button { color: #ecebf3; }
.terminal-tab button { font-size: 12px; }
#status { color: #e3aa9b; padding: 6px 14px; font-size: 11px; }
entry { background: #2d2f38; color: #eeeef3; border-radius: 7px; border-color: #41434e; }
.keycap { background: #2d2f38; border-radius: 5px; padding: 5px 10px; font-family: monospace; }
.guide-title { font-size: 20px; font-weight: bold; color: #eeedf3; }
notebook header { background: #191a20; border-color: #30323a; }
notebook stack { background: #202127; }
notebook tab { padding: 10px 20px; }
notebook tab:checked { background: #30323a; }
"""

# Rounded corners only while the main window floats; maximized and tiled edges stay square.
FLOATING = b'window.main-window:not(.maximized):not(.fullscreen):not(.tiled)' \
    b':not(.tiled-top):not(.tiled-bottom):not(.tiled-left):not(.tiled-right)'
CSS += b'\n'.join(FLOATING + rule for rule in (
    b' decoration { border-radius: 12px; }',
    b'.csd { border-radius: 0 0 12px 12px; }',
    b' > .titlebar { border-radius: 12px 12px 0 0; }',
    b' #tabbar { border-top-right-radius: 12px; }',
    b' #surface { border-bottom-right-radius: 12px; }',
))
