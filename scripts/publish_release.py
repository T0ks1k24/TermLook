#!/usr/bin/python3
"""Publish the tested artifact for VERSION; never overwrite a published release."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def api(path):
    result = subprocess.run(['gh', 'api', path], capture_output=True, text=True)
    if result.returncode:
        if '(HTTP 404)' in result.stderr:
            return None
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def main():
    version = Path('VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise SystemExit('VERSION must contain a numeric major.minor.patch version')
    repo = os.environ['GITHUB_REPOSITORY']
    commit = os.environ['GITHUB_SHA']
    tag = 'v' + version
    base = f'repos/{repo}'
    release = api(f'{base}/releases/tags/{tag}')
    if release and not release['draft']:
        print(f'{tag} already published; keeping its existing assets unchanged')
        return
    ref = api(f'{base}/git/ref/tags/{tag}')
    if ref:
        obj = ref['object']
        while obj['type'] == 'tag':
            obj = api(f"{base}/git/tags/{obj['sha']}")['object']
        if obj['type'] != 'commit' or obj['sha'] != commit:
            raise SystemExit(f'{tag} points to another commit; refusing to replace it')
    package = Path('dist') / f'termlook_{version}_all.deb'
    files = list(Path('dist').glob('*.deb'))
    if files != [package]:
        raise SystemExit('Expected exactly the Debian package matching VERSION')
    actual = subprocess.check_output(['dpkg-deb', '-f', str(package), 'Version'], text=True).strip()
    if actual != version:
        raise SystemExit('Package version does not match VERSION')
    checksum = Path('dist/SHA256SUMS')
    checksum.write_text(f'{hashlib.sha256(package.read_bytes()).hexdigest()}  {package.name}\n')
    notes = Path('dist/release-notes.md')
    notes.write_text(f'''Native Debian package, tested on Ubuntu 24.04 amd64.

Install or upgrade:

```bash
sudo apt install ./{package.name}
```

Verify the download with `sha256sum -c SHA256SUMS`.
Version 0.x releases are marked as pre-releases. APT dependencies are installed
from your configured repositories; this download does not enable automatic updates.
''')
    if not release:
        subprocess.run(['gh', 'release', 'create', tag, '--repo', repo, '--target', commit,
                        '--title', f'TermLook {version}', '--draft', '--notes-file', str(notes)], check=True)
    # Keep the release hidden until both assets have been uploaded successfully.
    subprocess.run(['gh', 'release', 'upload', tag, str(package), str(checksum),
                    '--repo', repo, '--clobber'], check=True)
    subprocess.run(['gh', 'release', 'edit', tag, '--repo', repo, '--draft=false',
                    '--prerelease=' + str(version.startswith('0.')).lower()], check=True)
    print(f'Published {tag}')


if __name__ == '__main__':
    main()
