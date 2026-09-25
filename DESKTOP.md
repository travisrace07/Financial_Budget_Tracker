# Ledger for Mac and Windows

The desktop edition runs the full application locally: CSV imports, transaction
categories, budgets, and reports. It bundles Python and uses SQLite, so end users
do not install Python or MySQL. The public sample-data website stays separate.

## Installation

- **Mac:** unzip `Ledger-macOS-<architecture>.zip`, move `Ledger.app` to Applications,
  and open it. An arm64 build is for Apple silicon; an x86_64 build is for Intel.
- **Windows:** run `Ledger-Windows-Setup.exe`. Alternatively, extract the complete
  `Ledger-Windows-x64.zip` and open `Ledger/Ledger.exe`; keep its `_internal` folder.
  The desktop window requires Microsoft's [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).
  If it is missing, install the Evergreen Runtime first. It is not bundled in this installer.

The initial builds are unsigned. They are intended for local testing; public
distribution should use an Apple Developer ID signature and notarization on Mac,
and a publisher signing certificate on Windows. No signing credentials are included.
Each download supports the architecture of the machine that built it.

## Data and backups

Ledger creates `ledger.sqlite3` automatically in:

- Mac: `~/Library/Application Support/Ledger/`
- Windows: `%LOCALAPPDATA%\Ledger\`

Close Ledger before copying that file for a backup. To restore, close Ledger and
replace the file with the backup. Updates and the Windows uninstaller leave this
folder intact. The desktop edition starts with an empty database; it does not
automatically migrate an existing MySQL database or development `preview.db`.
Startup errors are recorded in `desktop.log` in the same folder.

## Run from source

Use Python 3.12 and a dedicated virtual environment.

Mac:

```sh
python3 -m venv .venv-desktop
.venv-desktop/bin/python -m pip install -r requirements-desktop.txt
.venv-desktop/bin/python desktop.py
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv-desktop
.venv-desktop\Scripts\python -m pip install -r requirements-desktop.txt
.venv-desktop\Scripts\python desktop.py
```

## Build downloads

Run with the desktop environment's Python on each target operating system:

```sh
python -m unittest discover -s tests -v
python scripts/build_desktop.py
```

This bundles the application, tests its local server and bundled assets, and writes
a ZIP into `dist/`. It includes only the app's templates, named static assets, and
optional `static/icons/`; credentials and financial databases are not packaged.
On Windows, install [Inno Setup 6](https://jrsoftware.org/isinfo.php) and run
`ISCC.exe packaging\windows.iss` to produce the installer as well.

The GitHub Actions workflow **Build desktop downloads** builds on Mac and Windows,
runs tests, and uploads downloads as workflow artifacts. Open the repository's
Actions tab, select that workflow, and choose
**Run workflow**. Download the artifacts from the finished run. Nothing is
automatically published to a public release. The Mac runner builds for its own
architecture; Intel binaries require an additional build on an Intel Mac runner.
Building Windows from a Mac is not supported by PyInstaller.

Before distributing, test the GUI on a clean computer of each target platform:
launch, import a CSV, change a category, save a budget, close and reopen, download
the example CSV, and install an updated build to verify that data remains intact.
Automated bundle checks do not replace these native-window checks.

## Publish a preview release

1. Run **Build desktop downloads** from the Actions tab for the intended release
   branch. The workflow must be present on the default branch to run manually.
2. Wait for both platform jobs to succeed, then download and extract their artifacts.
3. Complete the platform checks listed above.
4. Create a draft under **Releases**, select the release commit, and assign a
   version tag and title. Mark preview versions as **Pre-release**.
5. Attach the application ZIP and installer files extracted from the artifacts.
   Include supported architectures, installation steps, and known limitations
   in the release notes.
6. Publish the release after reviewing its notes and attached files.

The workflow does not publish releases automatically. It runs manually or when a
tag beginning with `desktop-v` is pushed; a normal push to `main` does not start a
build.

## Branding

The interface uses `templates/index.html`, `static/app.js`, and
`static/style.css`. Place custom button images in `static/icons/`.
For the application icon, add `packaging/ledger.icns` for Mac and
`packaging/ledger.ico` for Windows, then rebuild. Without these files the packaging
tool's default icon is used. Changing `static/favicon.svg` changes the web icon,
not the installed desktop icon.

Packaging references: [pywebview](https://pywebview.flowrl.com/guide/installation.html)
and [PyInstaller](https://pyinstaller.org/en/stable/usage.html).
