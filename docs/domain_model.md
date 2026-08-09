# Domain Model

**Version:** 1.0
**Updated:** 2026-08-09
**Source of truth:** `app/database.py`

The Education Center CRM uses one canonical SQLite schema. Business calculations
are performed in the service layer; templates only display prepared data.

## User

Authenticated application account.

Fields: `id`, `full_name`, `email`, `phone`, `password_hash`, `role`,
`status`, `created_at`.

Roles:

- `admin`: complete administration
- `manager`: daily operational administration
- `teacher`: assigned groups, lessons and attendance

## Student

A participant managed by the education center.

Fields: `id`, `full_name`, `email`, `phone`, `guardian_name`,
`guardian_phone`, `status`, `notes`, `created_at`.

Statuses: `active`, `inactive`, `archived`.

## Course

A reusable educational offer.

Fields: `id`, `title`, `description`, `category`, `default_fee`,
`status`, `created_at`.

A teacher is assigned to a group, not duplicated on the course.

## Teacher

The operational teaching profile. A teacher may be linked to one login account
through `user_id`.

Fields: `id`, `user_id`, `full_name`, `email`, `phone`,
`specialization`, `status`, `created_at`.

Relationship: `teachers.user_id -> users.id`.

## Group

A concrete course group with a teacher, capacity and schedule description.

Fields: `id`, `course_id`, `teacher_id`, `name`, `capacity`,
`start_date`, `end_date`, `schedule_description`, `status`, `created_at`.

Relationships:

- `groups.course_id -> courses.id`
- `groups.teacher_id -> teachers.id`

## Group Student

The only canonical enrollment relation in v1.0.

Fields: `id`, `group_id`, `student_id`, `status`, `joined_at`.

Relationships:

- `group_students.group_id -> groups.id`
- `group_students.student_id -> students.id`
- one student can occur only once in the same group

Statuses: `enrolled`, `paused`, `completed`, `cancelled`.

## Lesson

One scheduled lesson instance.

Fields: `id`, `group_id`, `teacher_id`, `starts_at`, `ends_at`,
`room_label`, `delivery_mode`, `topic`, `status`, `created_at`.

Relationships:

- `lessons.group_id -> groups.id`
- `lessons.teacher_id -> teachers.id`

## Attendance

One student's status for one lesson.

Fields: `id`, `lesson_id`, `student_id`, `status`, `note`, `marked_at`.

The pair `lesson_id + student_id` is unique. Statuses are `present`,
`absent`, `late` and `excused`.

## Payment

An invoice and its accumulated payment state.

Fields: `id`, `student_id`, `group_id`, `amount_due`, `amount_paid`,
`due_date`, `paid_at`, `status`, `method`, `note`, `created_at`.

Statuses are calculated from amount and due date:

- `pending`: no payment and not overdue
- `partial`: payment received, balance remains
- `paid`: paid amount covers the invoice
- `overdue`: due date passed with an open balance

Relationships:

- `payments.student_id -> students.id`
- `payments.group_id -> groups.id`

## Derived dashboard values

The service layer calculates twelve operational metrics, including active
students, courses and groups, today's lessons, open and overdue invoices,
monthly revenue, outstanding balances, attendance, teacher count and occupied
group places. It also prepares group capacity, free-place and occupancy values
for the dashboard. The frontend only displays these prepared values and does
not recalculate business data.
