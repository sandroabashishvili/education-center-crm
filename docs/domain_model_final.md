<!--
Created: 2026-07-14
Last updated: 2026-07-14
Status: Active
Owner: Project maintainer
Notes: Core domain entities and relationships for the education center CRM.
-->

# Domain Model Final

ბოლო განახლება: `2026-04-13`

## Goal

ეს დოკუმენტი აფიქსირებს `Education Center CRM`-ის პირველი რეალური build-ისთვის საჭირო
საბოლოო domain model-ს იმ დონეზე, რომ:
- backend schema-ის დაწყება იყოს შესაძლებელი
- API რესურსები სწორად გაიშალოს
- UI screens დაეყრდნოს ერთ business truth-ს
- future expansion შესაძლებელი დარჩეს

ეს არის **MVP-final domain definition**, არა enterprise-level სრული მოდელი.

---

## Core Principles

პირველი ვერსიის წესები:
- business truth ინახება backend-ში
- derived სტატუსები და summary metrics ითვლება backend/service layer-ში
- UI არ უნდა იგონებდეს საკუთარ გამოთვლებს
- schema უნდა იყოს მარტივი, მკაფიო და გაფართოებადი

პირველ ვერსიაში შეგნებულად არ ვამატებთ:
- multi-branch complexity
- payroll
- exam/certificate logic
- parent/student portal
- advanced accounting ledger
- real SMS billing engine

---

## Main Entities

## 1. User

### Purpose
სისტემაში ავტორიზებული ადამიანი.

### Fields
- `id`
- `full_name`
- `email`
- `phone`
- `password_hash`
- `role`
- `status`
- `created_at`
- `updated_at`

### Roles
- `admin`
- `manager`
- `teacher`

### Status
- `active`
- `inactive`

### Notes
- ყველა login-capable actor მოდის `User` ცხრილიდან.
- `teacher` role-ის მქონე user-ს შეიძლება ჰქონდეს შესაბამისი `Teacher` business profile.

---

## 2. Teacher

### Purpose
მასწავლებლის business profile.

### Fields
- `id`
- `user_id`
- `display_name`
- `phone`
- `specialization`
- `status`
- `created_at`
- `updated_at`

### Status
- `active`
- `inactive`

### Rules
- `Teacher.user_id -> User.id`
- Teacher არის ცალკე business entity, არა მხოლოდ role flag.
- teacher login და teacher business profile ერთმანეთთან არის მიბმული.

---

## 3. Student

### Purpose
სასწავლო ცენტრის მოსწავლე.

### Fields
- `id`
- `full_name`
- `phone`
- `guardian_name`
- `guardian_phone`
- `status`
- `notes`
- `created_at`
- `updated_at`

### Status
- `active`
- `inactive`
- `archived`

### Rules
- `archived` student არ გამოიყენება ახალ enrollment-ში.
- `inactive` ნიშნავს, რომ მოსწავლე ახლა აქტიურ სასწავლო პროცესში შეიძლება არ იყოს, მაგრამ ისტორია ინახება.

---

## 4. Course

### Purpose
სასწავლო პროდუქტი/პროგრამა.

### Fields
- `id`
- `title`
- `description`
- `duration_weeks`
- `monthly_fee`
- `status`
- `created_at`
- `updated_at`

### Status
- `active`
- `inactive`
- `archived`

### Rules
- `Course` შედის MVP-ში როგორც მინიმალური CRUD entity.
- group ყოველთვის უკავშირდება ერთ course-ს.
- default fee source შეიძლება იყოს course, მაგრამ კონკრეტული billing logic მომავალში შეიძლება გაიშალოს ცალკე.

---

## 5. Group

### Purpose
კონკრეტული სასწავლო ჯგუფი.

### Fields
- `id`
- `name`
- `course_id`
- `teacher_id`
- `capacity`
- `status`
- `start_date`
- `end_date`
- `created_at`
- `updated_at`

### Status
- `planned`
- `active`
- `completed`
- `archived`

### Rules
- `Group.course_id -> Course.id`
- `Group.teacher_id -> Teacher.id`
- group-ს ჰყავს ერთი ძირითადი teacher პირველ MVP-ში.
- capacity გამოიყენება occupancy/reporting-ისთვის.
- completed/archived group-ში ახალი enrollment ნაგულისხმევად აღარ ემატება.

---

## 6. StudentEnrollment

### Purpose
student ↔ group კავშირი.

### Fields
- `id`
- `student_id`
- `group_id`
- `enrolled_at`
- `status`
- `created_at`
- `updated_at`

### Status
- `active`
- `paused`
- `completed`
- `cancelled`

### Rules
- `StudentEnrollment.student_id -> Student.id`
- `StudentEnrollment.group_id -> Group.id`
- student და group შორის ისტორია ინახება enrollment ჩანაწერებით.
- ერთი student-ს შეიძლება ჰქონდეს მრავალი enrollment ისტორიულად.
- ერთი enrollment record წარმოადგენს ერთ კონკრეტულ group membership-ს.

---

## 7. Lesson

### Purpose
კონკრეტული დაგეგმილი ან ჩატარებული გაკვეთილი.

### Fields
- `id`
- `group_id`
- `teacher_id`
- `starts_at`
- `ends_at`
- `room_label`
- `delivery_mode`
- `status`
- `created_at`
- `updated_at`

### Delivery Mode
- `offline`
- `online`

### Status
- `scheduled`
- `completed`
- `cancelled`

### Rules
- `Lesson.group_id -> Group.id`
- `Lesson.teacher_id -> Teacher.id`
- Lesson ინახება როგორც კონკრეტული scheduled instance.
- MVP-ში lesson-ები შეიძლება შეიქმნას ხელით ან მარტივი schedule flow-ით, მაგრამ storage დონეზე ყოველთვის არის ცალკე lesson record.
- attendance უკავშირდება lesson instance-ს და არა schedule template-ს.

---

## 8. AttendanceRecord

### Purpose
ერთი მოსწავლის დასწრება ერთ გაკვეთილზე.

### Fields
- `id`
- `lesson_id`
- `student_id`
- `status`
- `comment`
- `recorded_by_user_id`
- `created_at`
- `updated_at`

### Status
- `present`
- `absent`
- `late`

### Rules
- `AttendanceRecord.lesson_id -> Lesson.id`
- `AttendanceRecord.student_id -> Student.id`
- `AttendanceRecord.recorded_by_user_id -> User.id`
- ერთ lesson-ზე ერთ student-ს უნდა ჰქონდეს მაქსიმუმ ერთი attendance record.
- bulk marking UI საბოლოოდ ამ ჩანაწერებს წერს ინდივიდუალურად.

---

## 9. Payment

### Purpose
ფინანსური ჩანაწერი student/group კონტექსტში.

### Fields
- `id`
- `student_id`
- `group_id`
- `amount_due`
- `amount_paid`
- `currency`
- `due_date`
- `paid_at`
- `status`
- `method`
- `comment`
- `created_at`
- `updated_at`

### Status
- `pending`
- `partial`
- `paid`
- `overdue`

### Method
- `cash`
- `bank_transfer`
- `card`
- `other`

### Rules
- `Payment.student_id -> Student.id`
- `Payment.group_id -> Group.id`
- payment status backend-ში ითვლება `amount_due`, `amount_paid`, `due_date`, `paid_at`-ის მიხედვით.
- პირველ MVP-ში payment record შეიძლება წარმოადგენდეს ერთი billing cycle-ის ვალდებულებას.
- overdue ნიშნავს: გადაუხდელია ან არასრულადაა გადახდილი და `due_date` გასულია.
- partial ნიშნავს: `0 < amount_paid < amount_due`.
- paid ნიშნავს: `amount_paid >= amount_due`.

---

## 10. NotificationLog

### Purpose
შეტყობინების ისტორია და integration-ready audit trail.

### Fields
- `id`
- `student_id`
- `target_phone`
- `channel`
- `template_key`
- `message_text`
- `status`
- `sent_at`
- `created_at`

### Channel
- `sms`
- `whatsapp`
- `internal`

### Status
- `queued`
- `sent`
- `failed`

### Rules
- Notifications პირველ MVP-ში არ არის სრულფასოვანი end-user module.
- ეს entity ინახება architecture readiness-ისთვის და manual/mock flows-ისთვის.
- რეალური SMS provider integration მოდის შემდეგ ეტაპზე.

---

## Relationships Summary

- `Teacher.user_id -> User.id`
- `Group.course_id -> Course.id`
- `Group.teacher_id -> Teacher.id`
- `StudentEnrollment.student_id -> Student.id`
- `StudentEnrollment.group_id -> Group.id`
- `Lesson.group_id -> Group.id`
- `Lesson.teacher_id -> Teacher.id`
- `AttendanceRecord.lesson_id -> Lesson.id`
- `AttendanceRecord.student_id -> Student.id`
- `AttendanceRecord.recorded_by_user_id -> User.id`
- `Payment.student_id -> Student.id`
- `Payment.group_id -> Group.id`
- `NotificationLog.student_id -> Student.id`

---

## Derived Business Truth

backend/service layer თავიდანვე უნდა თვლიდეს:
- active students count
- active groups count
- today lessons count
- overdue payments count
- monthly revenue
- attendance rate
- group occupancy

### Rule
ეს გამოთვლები არ უნდა იყოს UI-ს პასუხისმგებლობა.

---

## MVP Business Rules

### Enrollment
- student group-ში დამატება ხდება `StudentEnrollment` ჩანაწერით.
- active group membership უნდა განისაზღვროს enrollment status-ით.

### Attendance
- attendance იწერება lesson-by-lesson.
- attendance marking დაშვებულია admin, manager და შესაბამის teacher actor-ებისთვის.

### Payments
- debt view მიიღება payment records-ის aggregate-ით.
- overdue list backend-მა უნდა დააბრუნოს მზა ფილტრად ან query rule-ით.

### Teachers
- teacher workload ითვლება მინიმუმ group და lesson მიბმების საფუძველზე.

### Reports
- პირველი ვერსიის reports აგებულია არსებული transactional data-დან და არა ცალკე analytics warehouse-დან.

---

## Explicit MVP Decisions

ამ დოკუმენტში ფიქსირდება შემდეგი საბოლოო გადაწყვეტილებები:

1. `Course` შედის MVP-ში.
2. `Teacher` არის ცალკე business entity.
3. `Lesson` ინახება instance-ებად.
4. `Payment.status` ითვლება backend-ში.
5. `NotificationLog` რჩება architecture-ready დონეზე.
6. business logic-ის primary truth არის backend/service layer.

---

## Non-MVP / Later Expansion

შემდეგ ეტაპზე შეიძლება დაემატოს:
- recurring schedule template model
- guardian portal
- student portal/app
- invoice automation
- salary/payroll logic
- exam/certificate records
- branch/tenant separation
- richer notification templates and provider integrations

---

## Build Consequence

ამ domain model-იდან უკვე შეიძლება პირდაპირი გადასვლა:
- SQLAlchemy models-ზე
- Alembic migrations-ზე
- FastAPI schemas/routes-ზე
- admin UI resource map-ზე

შემდეგი სწორი ნაბიჯი:
- `api_surface_plan.md`
- ან პირდაპირ `backend scaffold`
