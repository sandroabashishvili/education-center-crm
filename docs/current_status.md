# Current Status

**Status:** Functional Portfolio MVP v1.0 completed
**Updated:** 2026-08-13

## Implemented

- Flask 3.1.3 application with a versioned SQLite schema
- secure Werkzeug password hashing
- CSRF protection for all write requests
- session-based authentication
- role-based authorization for administrator, manager and teacher
- teacher access limited to assigned groups and lessons
- protected CRM data pages
- student search, profiles, editing, status and deletion
- courses, teachers, groups and canonical group enrollment
- lesson scheduling and attendance
- invoices, partial payments and overdue status calculation
- twelve database-backed dashboard metrics and UTF-8 CSV exports
- dashboard tables for recent students, recent payments, upcoming lessons and group occupancy
- record-specific dashboard links for students, payments, lessons and groups
- server-side validation with visible feedback
- separated Jinja templates and shared static CSS
- validated SQLite backup and restore CLI
- responsive desktop, tablet and mobile interface with card-style compact tables
- linked application brand that returns to the dashboard
- static read-only GitHub Pages preview

## Verification

- 12 automated regression tests pass
- Python compilation passes
- fresh database initialization passes
- SQLite integrity and backup/restore pass
- CSRF rejection and protected-page redirects pass
- administrator, manager and teacher permissions pass
- teacher data scoping passes
- student CRUD, attendance and payment workflows pass
- invalid forms and overpayments are rejected
- CSV exports pass
- dashboard rendering and record-specific links pass
- automated browser scan passes without horizontal overflow or serious accessibility violations

## Storage

The executable application uses one canonical SQLite schema with nine tables:

- users
- students
- courses
- teachers
- groups
- group_students
- lessons
- attendance
- payments

The former duplicate enrollment model and unused notification table are no
longer part of v1.0.

## Portfolio boundary

This repository contains a functional local CRM application with generated demo
data. GitHub Pages hosts a static read-only preview because it cannot run a
persistent Flask and SQLite backend.

## v1.0 completion

The functional portfolio scope is complete. Future changes should be driven by
a real deployment requirement or a clearly selected v1.1 feature, rather than
additional portfolio-only expansion.

## Possible production follow-up

These items are intentionally outside the portfolio v1.0 scope:

- password recovery and account administration
- audit logging
- deployment and monitoring configuration
- production WSGI hosting
- formal migration workflow for long-running installations
- organizational backup retention and data-protection procedures
