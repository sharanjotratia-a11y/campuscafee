# CampusCart

A Flask application for exploring campus cafe sales, orders, students, and reports.
The SQLite database and exported CSV are generated locally and are intentionally
excluded from this repository.

## Requirements

- Python 3
- Flask

Install Flask from the project root:

```powershell
python -m pip install Flask
```

## Run locally

Set unique passwords for the generated admin and analyst accounts, then create
the local database:

```powershell
$env:CAMPUSCART_ADMIN_PASSWORD = "replace-with-a-unique-admin-password"
$env:CAMPUSCART_ANALYST_PASSWORD = "replace-with-a-unique-analyst-password"
python .\CampusCart\create_db.py
```

Set a signing key and start the application:

```powershell
$env:FLASK_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python .\CampusCart\app.py
```

Sign in with username `admin` or `analyst` and the corresponding password set
above. The generated database contains synthetic sample records. Running the
database generator again replaces the existing local database.

For deployments, configure these values as environment secrets and use a
production-ready WSGI server; do not commit `.env` files, database files, or
exported data.
