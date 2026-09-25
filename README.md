# Ledger — Personal Budget Tracker

Ledger turns transaction CSVs into a monthly view of income, spending, and savings. It automatically groups transactions by category, compares spending against budgets, and identifies possible recurring charges.

Built with Python, Flask, SQLAlchemy, and vanilla JavaScript. The desktop edition
uses SQLite; the server edition also supports MySQL.

[View demo](https://travisrace07.github.io/Financial_Budget_Tracker/)

## Desktop installation

The desktop edition runs in its own window and saves transactions and budgets on
the local computer. Packaged downloads include Python and require no separate
Python, MySQL, or Docker installation.

Downloads are distributed through [GitHub Releases](https://github.com/travisrace07/Financial_Budget_Tracker/releases)
as release assets. Available operating systems and architectures are listed on
each release. GitHub's **Code → Download ZIP** provides the source code; desktop
packages are attached separately under **Assets**.

| Computer | Download | Installation |
| --- | --- | --- |
| Mac with Apple silicon | `Ledger-macOS-arm64.zip` | Unzip, move `Ledger.app` to Applications, then open it. |
| Intel Mac, if an Intel build is provided | `Ledger-macOS-x86_64.zip` | Unzip, move `Ledger.app` to Applications, then open it. |
| Windows x64 | `Ledger-Windows-Setup.exe` | Run the installer and open Ledger from the Start menu. |
| Windows x64, portable option | `Ledger-Windows-x64.zip` | Extract the whole ZIP and open `Ledger/Ledger.exe`. Keep the `_internal` folder alongside it. |

Windows requires [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).
Install the Evergreen Runtime if it is missing. Initial preview packages are
unsigned and may show operating-system security prompts. The default Mac workflow
builds for its runner's architecture; it does not produce both Mac architectures.

### Getting started

1. Open Ledger and select **Explore sample dashboard** to view fictional sample data.
2. Select **Back to my finances**, then open **Import transactions** and download
   the example CSV.
3. Import that CSV and inspect the income, expenses, and savings totals.
4. Change a transaction's category and set a budget for the selected month.
5. Close and reopen Ledger to verify that the imported data and budget persist.

Financial data is stored separately from the installed application and persists
when the application is replaced. See [desktop installation, backup, and build instructions](DESKTOP.md) for data
locations and troubleshooting. The desktop edition starts with an empty database;
it does not automatically copy an existing MySQL database.

## Features

- Import transactions from CSV files, with validation and duplicate detection.
- Categorize spending using merchant rules and correct categories manually.
- Track monthly income, expenses, net savings, and savings rate.
- Set monthly category budgets and see spending against each limit.
- Explore cash flow, spending breakdowns, and six-month savings trends.
- Find recurring weekly, biweekly, and monthly charges.
- Search transactions by description or category.

The demo uses fictional sample figures and supports browsing only. CSV imports, category changes, and saved budgets are available when running the full app locally.

## Run the web application from source

The following options run the Flask application in a browser. For desktop source
setup and packaging, see the [desktop guide](DESKTOP.md).

### With Docker

Install Docker Desktop, then run these commands from the project folder:

```sh
cp .env.example .env
```

Edit `.env` and replace both placeholder passwords with long, random alphanumeric values. Then start the app:

```sh
docker compose up --build -d
```

Open [localhost:8000](http://localhost:8000). MySQL stores data in the `ledger_data` Docker volume, which persists between restarts.

### With Python and an existing MySQL server

Create a virtual environment and install the dependencies:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Run the setup script and enter the MySQL administrator credentials in Terminal:

```sh
.venv/bin/python setup_mysql.py
```

The script creates the `ledger` database and a dedicated application user. Connection settings are saved locally in `.mysql-local.json`; the administrator password is not saved.

Start the app:

```sh
.venv/bin/python run_mysql.py
```

Open [localhost:8001](http://localhost:8001). Keep Terminal running while using the app, and press Control-C to stop it.

Alternatively, supply a database connection directly:

```sh
export DATABASE_URL='mysql+pymysql://ledger:YOUR_PASSWORD@localhost:3306/ledger?charset=utf8mb4'
.venv/bin/python app.py
```

This starts the app on port 8000 and creates its tables on startup. SQLite is also available for development by setting `DATABASE_URL=sqlite:///preview.db`.

## CSV format

Use a UTF-8 CSV with these columns:

```csv
date,description,amount
2026-09-01,Monthly payroll,6800.00
2026-09-02,Apartment rent,-1800.00
2026-09-07,Whole Foods,-126.45
```

Negative amounts represent expenses; positive amounts represent income. Select the import option for positive spending amounts if the bank export uses the opposite convention. Separate `debit` and `credit` columns are also supported, using nonnegative values.

Dates can use `YYYY-MM-DD`, `MM/DD/YYYY`, or `MM/DD/YY`. An optional `category` column can supply an existing app category. Files can contain up to 10,000 transactions and must be smaller than 5 MB. If a row fails validation, the entire import is rejected with its row number.

An [example CSV](static/sample.csv) is included in the project.

## How calculations work

Income includes positive transactions, including refunds. Expenses include negative transactions. Transfers are excluded from both. Net savings equals income minus expenses; savings rate is net savings divided by income. All amounts are in USD.

Budgets apply to one category and month. Updating a category changes its spending totals, but does not change the rules used to categorize future imports.

Recurring-charge estimates use the last three payments with the same description, similar amounts, and weekly, biweekly, or monthly intervals. The latest payment must fall in the selected month. These estimates may miss renamed merchants or changing payment amounts.

Duplicate detection compares dates, descriptions, amounts, and repeated occurrences within a file. Without bank transaction IDs, identical payments from different accounts can be ambiguous. The app is intended for one consolidated ledger.

## Project structure

| Path | Purpose |
| --- | --- |
| `app.py` | Flask routes, CSV parsing, database models, and financial calculations |
| `templates/` | Dashboard HTML |
| `static/` | JavaScript, styles, and sample transactions |
| `tests/` | API, calculation, and desktop persistence tests |
| `desktop.py` | Desktop window, local server, and SQLite storage |
| `packaging/` | Application bundle and Windows installer configuration |
| `scripts/build_desktop.py` | Builds and checks desktop packages |
| `.github/workflows/desktop.yml` | Mac and Windows build workflow |
| `DESKTOP.md` | Desktop setup, backups, packaging, and release instructions |
| `docs/` | Static sample-data demo |
| `scripts/build_demo.py` | Rebuilds the demo from the dashboard source |
| `setup_mysql.py` | Local database setup |
| `run_mysql.py` | Starts the app with saved MySQL settings |

## Tests

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests use an isolated SQLite database by default. To test against MySQL, set `TEST_DATABASE_URL` to a disposable database connection. The tests erase that database's application tables.

## Desktop builds and releases

The **Build desktop downloads** workflow creates Mac and Windows packages and
uploads them as workflow artifacts. Release publication is a separate step. See
[building desktop packages](DESKTOP.md#build-downloads) and
[publishing a preview release](DESKTOP.md#publish-a-preview-release) for maintainer
instructions.

## Current scope

Ledger is a local, single-user application. It does not include login accounts, bank synchronization, or currency conversion. The public demo has no database connection and does not accept financial uploads. Its sample figures illustrate the interface rather than a complete transaction history.

Local credentials, environment files, and database files are excluded from version control. The full app should remain local unless authentication and appropriate hosting security are added.
