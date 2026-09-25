"""Build and smoke-test on macOS or Windows, then create a download archive."""
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform not in ('darwin', 'win32'):
        raise SystemExit('Build on macOS or Windows using that platform\'s Python.')
    # Keep the PyInstaller cache within this workspace.
    env = dict(os.environ, PYINSTALLER_CONFIG_DIR=str(ROOT / 'build' / 'pyinstaller-cache'))
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm',
                    '--distpath', str(ROOT / 'dist'), '--workpath', str(ROOT / 'build'),
                    str(ROOT / 'packaging' / 'ledger.spec')], cwd=ROOT, env=env, check=True)
    dist = ROOT / 'dist'
    executable = (dist / 'Ledger.app/Contents/MacOS/Ledger' if sys.platform == 'darwin'
                  else dist / 'Ledger/Ledger.exe')
    subprocess.run([str(executable), '--smoke-test'], check=True)
    if sys.platform == 'darwin':
        archive = dist / f'Ledger-macOS-{platform.machine()}.zip'
        subprocess.run(['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent',
                        str(dist / 'Ledger.app'), str(archive)], check=True)
    else:
        archive = shutil.make_archive(str(dist / 'Ledger-Windows-x64'), 'zip',
                                      root_dir=dist, base_dir='Ledger')
    print(f'Download ready: {archive}')


if __name__ == '__main__':
    main()
