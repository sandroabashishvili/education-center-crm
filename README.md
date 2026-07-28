# Education Center CRM

A portfolio-grade Flask and SQLite application with a complete German-language interface for the day-to-day administration of a small education center.

![Education Center CRM dashboard](assets/dashboard-preview.png)

## What it demonstrates

- session-based admin login
- student registry, search, filtering, profile view, editing, and lifecycle status
- courses, teachers, groups, and group enrollment
- lesson scheduling and per-student attendance
- invoices, partial receipts, and automatically refreshed overdue status
- dashboard KPIs calculated from the database
- UTF-8 CSV exports for students and payments
- responsive desktop and mobile layouts
- service-layer business logic and automated regression tests

## Portfolio demo

[Open the static portfolio preview](https://sandro-abashishvili.sandroabashishvili.chatgpt.site/demos/education-crm/)

The GitHub project contains the functional Flask application. The portfolio URL is a static preview because the portfolio hosting does not run a persistent SQLite backend.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

Open `http://127.0.0.1:5001`.

The database is created and populated with realistic demo records on first start.

### Demo login

```text
Email:    admin@bildungszentrum.de
Password: admin123
```

These credentials are for the local portfolio demo only.

## Test

```bash
python -m unittest discover -s tests -v
```

The suite covers health and dashboard responses, authentication guards, student CRUD, POST-only deletion, group enrollment, attendance, overdue payments, and CSV exports.

## Configuration

Optional environment variables:

```bash
export CRM_SECRET_KEY="replace-this-for-non-demo-use"
export CRM_DB_PATH="/absolute/path/to/crm.db"
export PORT="5001"
```

See [.env.example](.env.example).

## Architecture

```text
.
├── app/
│   ├── main.py       # Flask bootstrap and configuration
│   ├── database.py   # SQLite schema, compatibility migrations, demo seed
│   ├── models.py     # domain dataclasses
│   ├── routes.py     # HTTP routes and request handling
│   ├── services.py   # queries and business rules
│   ├── templates.py  # server-rendered admin UI
│   └── utils.py      # parsing helpers
├── assets/
├── docs/
├── tests/
└── requirements.txt
```

## Status and honest scope

The current version is a completed portfolio MVP. It is designed for a local demonstration and uses SQLite with generated demo data.

It is not presented as a production SaaS. Production work would still require CSRF protection, per-role authorization rules, password-reset flows, audit logging, deployment configuration, database migrations, backups, and a production WSGI server.

See [current status](docs/current_status.md) for the detailed implementation boundary.

## Author

Aleksandre (Sandro) Abashishvili<br>
[Portfolio](https://sandro-abashishvili.sandroabashishvili.chatgpt.site) · [GitHub](https://github.com/sandroabashishvili) · [LinkedIn](https://www.linkedin.com/in/aleksandre-abashishvili-03417617a/)
