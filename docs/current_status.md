# Current Status

**Status:** Functional Portfolio MVP v1.0 completed
**Updated:** 2026-08-09

## Implemented

- Flask application with a versioned SQLite schema
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
- dashboard metrics and UTF-8 CSV exports
- server-side validation with visible feedback
- separated Jinja templates and shared static CSS
- validated SQLite backup and restore CLI
- responsive desktop and mobile interface
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

## Possible production follow-up

These items are intentionally outside the portfolio v1.0 scope:

- password recovery and account administration
- audit logging
- deployment and monitoring configuration
- production WSGI hosting
- formal migration workflow for long-running installations
- organizational backup retention and data-protection procedures
