"""Exercise the installed snap, its GUI, and a real host shell under Xvfb.

Run in a fresh D-Bus session, with snap installed and xdotool available.
The temporary settings and shell probe never modify the user's configuration.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time


def wait_for(check, process, description):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f'Snap exited before {description}: {process.returncode}')
        result = check()
        if result:
            return result
        time.sleep(0.1)
    raise AssertionError(f'Timed out waiting for {description}')


def window_id():
    result = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', '^TermLook$'],
                            capture_output=True, text=True)
    return result.stdout.splitlines()[0] if result.returncode == 0 else None


parser = argparse.ArgumentParser()
parser.add_argument('--deb', action='store_true', help='Test the installed Debian package')
args = parser.parse_args()
command_to_run = ['/usr/bin/termlook'] if args.deb else ['snap', 'run', 'termlook']

with tempfile.TemporaryDirectory(prefix='termlook-package-test-') as directory:
    root = Path(directory)
    config = root / 'config' / 'termlook'
    config.mkdir(parents=True)
    (config / 'settings.json').write_text(json.dumps({'shell': '/bin/bash', 'close_to_tray': False}))
    (config / 'layout.json').write_text(json.dumps([
        {'name': 'Snap test', 'tabs': [{'name': 'host shell', 'cwd': directory}]}]))
    marker = root / 'host-shell.json'
    # /tmp and /usr/bin/python3 deliberately refer to the host filesystem.
    probe = ('import json,os; from pathlib import Path; '
             f'Path({str(marker)!r}).write_text(json.dumps(dict('
             'home=os.environ.get("HOME"),cwd=os.getcwd(),'
             'snap=os.environ.get("SNAP"),ld=os.environ.get("LD_LIBRARY_PATH"))))')
    command = '/usr/bin/python3 -c ' + shlex.quote(probe)
    env = dict(os.environ, XDG_CONFIG_HOME=str(root / 'config'), SHELL='/bin/bash')
    process = subprocess.Popen(command_to_run, env=env, cwd=directory)
    try:
        window = wait_for(window_id, process, 'the packaged GUI')
        subprocess.run(['xdotool', 'windowfocus', '--sync', window], check=True)
        # Typing before shell startup is safe: VTE queues input for the PTY.
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '2', command], check=True)
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'Return'], check=True)
        wait_for(marker.exists, process, 'a host command in the terminal')
        data = json.loads(marker.read_text())
        assert data['home'] == os.environ['HOME'], data
        assert data['cwd'] == directory, data
        assert data['snap'] is None, data
        assert data['ld'] == os.environ.get('LD_LIBRARY_PATH'), data
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+shift+q'], check=True)
        assert process.wait(timeout=10) == 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
print('Installed package passed: GUI, host bash, host command, HOME, cwd, clean environment, quit')
