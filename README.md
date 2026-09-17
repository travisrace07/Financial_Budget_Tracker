# Ledger

Personal budget tracker built with Python/Flask, SQLAlchemy, MySQL 8.4, and dependency-free HTML/CSS/JavaScript charts.

[Source code](https://github.com/travisrace07/Financial_Budget_Tracker)

## Portfolio demo

Ledger demonstrates CSV validation, merchant-based categorization, monthly financial summaries, category budgets, visual reporting, and recurring-payment detection.

The `docs/` folder is a standalone, sample-only dashboard for GitHub Pages. Visitors can explore charts, reporting months, transaction search, budgets, and recurring-charge examples. The figures are fictional illustrative fixtures, not a complete underlying ledger. Uploads and saving are disabled in the public demo; the full Python/MySQL app below implements those features. GitHub Pages serves the frontend only and does not run Python or MySQL.

### Publish the repository and demo

1. Open https://github.com/travisrace07/Financial_Budget_Tracker while signed in as the repository owner.
2. Push this project to that repository, or use **Add file → Upload files** to upload the contents of the clean source package. Preserve the folders, including `docs/`.
3. In the GitHub repository, open **Settings → Pages**. Choose **Deploy from a branch**, select the branch containing your code, choose **/docs**, and save.
4. GitHub will display the published demo link on that page. Add it to the repository's **About → Website** field and your portfolio.

Only commit project source and fictional sample data. `.gitignore` excludes local credentials, environment files, databases, transaction CSVs, and the virtual environment. Git ignore rules do not remove files already committed; inspect your commit before publishing. Never upload the entire folder as a ZIP because it contains local private files.

After changing the interface, regenerate the demo and commit the updated `docs/` files:

```sh
python3 scripts/build_demo.py
```

Preview it locally with `python3 -m http.server 8080 --directory docs`, then open http://localhost:8080.

### Architecture and scope

- **Backend:** Flask endpoints for CSV import, dashboard aggregation, category corrections, and monthly budgets.
- **Persistence:** SQLAlchemy models backed by MySQL; isolated SQLite databases support local tests.
- **Frontend:** Responsive HTML/CSS and vanilla JavaScript with charts and accessible form labels.
- **Data handling:** Atomic CSV validation, duplicate detection, decimal currency arithmetic, and heuristic recurring-payment detection.

The full app is a local, single-user project. Authentication, multiple accounts, bank synchronization, and production hosting are outside this release. Categorization uses rules rather than machine learning.

## Run with MySQL

Install Docker Desktop, then from this folder:

```sh
cp .env.example .env
# Edit .env and replace both passwords with random alphanumeric values.
docker compose up --build -d
```

Open http://localhost:8000. MySQL data persists in the `ledger_data` volume. The app is bound to your machine's loopback interface; this is a single-user local application with no authentication. Add authentication and HTTPS before exposing it to a network. Back up MySQL before removing its volume.

## Run Python directly

With a MySQL database and user already created:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export DATABASE_URL='mysql+pymysql://ledger:YOUR_PASSWORD@localhost:3306/ledger?charset=utf8mb4'
.venv/bin/python app.py
```

Tables are created on startup. The Docker deployment supplies the database automatically. For a local development preview without MySQL, explicitly use `DATABASE_URL=sqlite:///preview.db`; SQLite is only a development alternative, not the Docker application's database.

## Import and use

- Upload a UTF-8 CSV with `date,description,amount`, or `date,description,debit,credit`. Accepted aliases: transaction date, posted date, merchant, memo, details. Optional `category` must match an app category.
- Use ISO dates or US dates. Default amounts: negative = expense, positive = income. Select the import checkbox if your bank uses the opposite convention. Debit/credit columns use nonnegative amounts.
- Maximum 5 MB and 10,000 rows. Validation is atomic: a bad row rejects the whole file and reports its row number.
- Rule-based merchant matching categorizes spending. Correct categories in Transactions. Corrections update charts and budget totals; they do not train future rules.
- Income includes positive non-transfer transactions (including refunds). Spending includes negative non-transfer transactions. Savings = income minus spending. Savings rate is unavailable when income is zero. All values use USD; there is no currency conversion.
- Budgets are per category and month. Saving an existing category updates its limit. Select each month to set its budgets.
- Recurring estimates require the last three same-description charges to have weekly, biweekly, or monthly intervals and similar amounts, with the latest payment in the selected month. This is a heuristic, not subscription verification.
- Exact date/description/amount occurrences are deduplicated across imports, preserving repeated identical rows within a file. Without bank transaction IDs/account identifiers, overlapping files from different accounts or identical legitimate payments can be ambiguous. Review skipped counts; this version is intended for one consolidated ledger.
- Sample dashboard data is isolated in browser memory. Import the downloadable CSV if you want editable sample records in the database.

## Checks

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Tests use an isolated SQLite database for API and financial logic. To run the same API tests against a disposable MySQL database, set `TEST_DATABASE_URL` to its connection URL. Tests erase that database's application tables. Do not use your personal database.

## Guided local MySQL setup (Workbench installation)

Run `.venv/bin/python setup_mysql.py` and enter your MySQL administrator username and password privately in Terminal. The script creates the `ledger` database and a unique app account, verifies access, and writes `.mysql-local.json` with owner-only permissions. This file is excluded from Git and Docker. The administrator password is not saved.

Then run `.venv/bin/python run_mysql.py` and open http://127.0.0.1:8001. Port 8001 keeps the MySQL app distinct from the SQLite preview on port 8000. Existing SQLite preview transactions are not automatically migrated; import your CSV into the MySQL app. Keep Terminal running while using the dashboard; press Control-C to stop it.
