#!/usr/bin/python3
"""Install this checkout's launcher and icon for the current Linux user."""
import os
from pathlib import Path
import shutil


def desktop_quote(value):
    # Desktop Exec quoting is not shell quoting. Literal % is escaped as %%.
    value = str(value).replace('%', '%%')
    for character in ('\\', '"', '`', '$'):
        value = value.replace(character, '\\' + character)
    return '"' + value + '"'


def install(data_home=None):
    root = Path(__file__).resolve().parents[1]
    data = Path(data_home or os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    applications = data / 'applications'
    icons = data / 'icons/hicolor/scalable/apps'
    applications.mkdir(parents=True, exist_ok=True)
    icons.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / 'termlook/assets/io.termlook.TermLook.svg', icons / 'io.termlook.TermLook.svg')
    desktop = applications / 'io.termlook.TermLook.desktop'
    desktop.write_text('\n'.join([
        '[Desktop Entry]', 'Type=Application', 'Version=1.0', 'Name=TermLook',
        'Comment=Minimal workspace terminal',
        'Exec=/usr/bin/python3 ' + desktop_quote(root / 'scripts/run.py'),
        'Icon=io.termlook.TermLook', 'Terminal=false', 'Categories=System;TerminalEmulator;',
        'StartupNotify=true', 'StartupWMClass=termlook', '',
    ]))
    return desktop


if __name__ == '__main__':
    print(install())
