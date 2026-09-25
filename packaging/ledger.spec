# Build on the target OS; never bundle the project root or user databases.
import sys
from pathlib import Path

root = Path(SPECPATH).parent
assets = [(str(root / 'templates'), 'templates')]
assets += [(str(root / 'static' / name), 'static')
           for name in ('app.js', 'style.css', 'favicon.svg', 'sample.csv')]
if (root / 'static' / 'icons').is_dir():
    assets.append((str(root / 'static' / 'icons'), 'static/icons'))
icon = root / 'packaging' / ('ledger.icns' if sys.platform == 'darwin' else 'ledger.ico')
icon = str(icon) if icon.exists() else None

a = Analysis([str(root / 'desktop.py')], pathex=[str(root)], datas=assets,
             hiddenimports=['sqlalchemy.dialects.sqlite', 'webview'],
             excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'pymysql', 'gunicorn'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Ledger',
          console=False, icon=icon)
collection = COLLECT(exe, a.binaries, a.datas, name='Ledger')
if sys.platform == 'darwin':
    app = BUNDLE(collection, name='Ledger.app', icon=icon,
                 bundle_identifier='com.travisrace.ledger',
                 info_plist={'CFBundleShortVersionString': '0.1.0',
                             'NSHighResolutionCapable': True})
