# Current Status

Status: `Portfolio MVP complete`<br>
Updated: `2026-07-27`

## Implemented

- Flask application bootstrap and environment-based configuration
- SQLite schema and automatic demo-data initialization
- admin session login and logout
- authenticated write operations
- POST-only destructive routes
- student list, search, status filter, profile, create, edit, and delete
- course and teacher directories
- group creation and student enrollment
- lesson scheduling
- attendance marking
- payment invoices and receipt recording
- automatic pending, partial, paid, and overdue status refresh
- dashboard metrics for students, courses, groups, today's lessons, overdue invoices, monthly revenue, and attendance
- student and payment CSV exports
- responsive admin interface

## Verification

- 8 automated regression tests pass
- Python compilation passes
- fresh-database initialization verified
- desktop rendering checked at 1440 × 1200
- narrow mobile rendering checked with a 390 CSS-pixel viewport
- write routes, CRUD, attendance, payment, overdue filter, and CSV exports verified

## Portfolio boundary

This repository is a functional local MVP with generated demo data. The public portfolio contains a static preview, not a hosted multi-user CRM backend.

## Production follow-up

- CSRF tokens
- granular admin, manager, and teacher permissions
- password reset and user management
- audit trail
- migration tooling
- PostgreSQL
- backup and restore procedures
- production WSGI deployment
