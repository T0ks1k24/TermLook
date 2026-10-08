#!/usr/bin/python3
"""Build the architecture-independent Ubuntu package without root or pip."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build(output):
    version = (ROOT / 'VERSION').read_text().strip()
    subprocess.run(['dpkg', '--validate-version', version], check=True)
    output.mkdir(parents=True, exist_ok=True)
    destination = output.resolve() / f'termlook_{version}_all.deb'
    with tempfile.TemporaryDirectory(prefix='termlook-deb-') as directory:
        stage = Path(directory)
        app = stage / 'usr/share/termlook'
        shutil.copytree(ROOT / 'termlook', app / 'termlook',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo'))
        files = {
            'scripts/run.py': 'usr/share/termlook/scripts/run.py',
            'packaging/debian/termlook': 'usr/bin/termlook',
            'packaging/debian/termlook.desktop': 'usr/share/applications/io.termlook.TermLook.desktop',
            'termlook/assets/io.termlook.TermLook.svg': 'usr/share/icons/hicolor/scalable/apps/io.termlook.TermLook.svg',
            'LICENSE': 'usr/share/doc/termlook/copyright',
        }
        for source, target in files.items():
            path = stage / target
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source, path)
        (stage / 'DEBIAN').mkdir()
        control = (ROOT / 'packaging/debian/control').read_text().replace('@VERSION@', version)
        (stage / 'DEBIAN/control').write_text(control)
        for path in stage.rglob('*'):
            path.chmod(0o755 if path.is_dir() else 0o644)
        (stage / 'usr/bin/termlook').chmod(0o755)
        subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(destination)], check=True)
    print(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    build(parser.parse_args().output)
