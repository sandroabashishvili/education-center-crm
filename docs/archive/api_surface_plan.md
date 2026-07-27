<!--
Created: 2026-07-14
Last updated: 2026-07-14
Status: Active
Owner: Project maintainer
Notes: API surface planning for the current CRM MVP.
-->

# Education Center CRM — API Surface Plan (MVP v1)

ბოლო განახლება: 2026-07-14
სტატუსი: active

## Goal

ეს დოკუმენტი აფიქსირებს პირველი build-ისთვის საჭირო API ზედაპირს იმ დონეზე, რომ:
- FastAPI routes გაიშალოს სწორი მოდულებით
- frontend resource map იყოს ერთმნიშვნელოვანი
- build order იყოს გასაგები
- ზედმეტი endpoint-ები თავიდან ავიცილოთ

ეს არის **MVP-first API plan**, არა საბოლოო enterprise API contract.

---

## API Principles

პირველი ვერსიის პრინციპები:
- API აგებულია რესურსებზე დაფუძნებით
- business validation ხდება backend-ში
- list endpoints მხარს უჭერს basic filter/query პარამეტრებს
- UI-სთვის საჭირო summary endpoints შეიძლება ცალკე არსებობდეს
- ჯერ არ ვაკეთებთ რთულ public API/versioning სტრატეგიას

Base path:
- `/api/v1`

---

## 1. Auth

### Purpose
სისტემაში შესვლა და მიმდინარე user context-ის მიღება.

### Endpoints
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### Notes
- login იღებს `email` + `password`
- `GET /auth/me` აბრუნებს მიმდინარე user-ს და role-ს
- პირველ ვერსიაში password reset მხოლოდ placeholder-ად რჩება UI-ში

---

## 2. Users / Role Context

### Purpose
MVP-ში სრული user management არ არის ცენტრალური მოდული, მაგრამ authenticated actor context გვჭირდება.

### Endpoints
- `GET /users/me`

### Notes
- ეს შეიძლება ტექნიკურად დაემთხვას `/auth/me`-ს
- ცალკე full user CRUD პირველ build-ში პრიორიტეტი არ არის

---

## 3. Dashboard

### Purpose
მთავარი summary cards და recent operational overview.

### Endpoints
- `GET /dashboard/summary`
- `GET /dashboard/recent-activity` *(optional in first pass)*

### `GET /dashboard/summary` returns
- `total_students`
- `active_groups`
- `today_lessons`
- `overdue_payments_count`
- `this_month_revenue`
- `attendance_summary`

### Notes
- dashboard metrics ითვლება backend-ში fileciteturn1file55
- პირველი pass-ში recent activity შეიძლება იყოს mock/simple feed

---

## 4. Students

### Purpose
student registry, listing, profile view, status management.

### Endpoints
- `GET /students`
- `POST /students`
- `GET /students/{student_id}`
- `PATCH /students/{student_id}`
- `GET /students/{student_id}/attendance`
- `GET /students/{student_id}/payments`
- `GET /students/{student_id}/enrollments`

### Recommended filters for `GET /students`
- `search`
- `status`
- `group_id`
- `course_id`
- `payment_status`

### Notes
- student profile screen-ს სჭირდება composite view: basic info + enrollments + attendance + payments fileciteturn1file52
- `DELETE` არ არის აუცილებელი; ვიყენებთ status-based lifecycle-ს

---

## 5. Courses

### Purpose
minimal CRUD for course entity.

### Endpoints
- `GET /courses`
- `POST /courses`
- `GET /courses/{course_id}`
- `PATCH /courses/{course_id}`

### Filters
- `status`
- `search`

### Notes
- MVP-ში course არის ცალკე CRUD entity fileciteturn1file53turn1file55
- hard delete პირველ ვერსიაში არ გვჭირდება

---

## 6. Teachers

### Purpose
teacher business profile management.

### Endpoints
- `GET /teachers`
- `POST /teachers`
- `GET /teachers/{teacher_id}`
- `PATCH /teachers/{teacher_id}`
- `GET /teachers/{teacher_id}/groups`
- `GET /teachers/{teacher_id}/lessons`

### Notes
- teacher არის ცალკე business entity, არა მხოლოდ role flag fileciteturn1file53turn1file55
- teacher workload view შეიძლება backend aggregate-ით მივიღოთ

---

## 7. Groups

### Purpose
group lifecycle, group details, membership management.

### Endpoints
- `GET /groups`
- `POST /groups`
- `GET /groups/{group_id}`
- `PATCH /groups/{group_id}`
- `GET /groups/{group_id}/students`
- `POST /groups/{group_id}/students`
- `DELETE /groups/{group_id}/students/{student_id}` *(soft remove via enrollment status logic)*
- `GET /groups/{group_id}/lessons`
- `GET /groups/{group_id}/attendance-summary`

### Filters for `GET /groups`
- `status`
- `course_id`
- `teacher_id`

### Notes
- student↔group კავშირი რეალურად `StudentEnrollment`-ზე დგას fileciteturn1file55
- UI-სთვის membership actions group context-იდან ჩანს ყველაზე ბუნებრივად fileciteturn1file52

---

## 8. Enrollments

### Purpose
student-group membership records as first-class business operation.

### Endpoints
- `POST /enrollments`
- `PATCH /enrollments/{enrollment_id}`
- `GET /enrollments`

### Filters
- `student_id`
- `group_id`
- `status`

### Notes
- თუნდაც UI group screen-იდან მართავდეს, backend-ში enrollment ცალკე რესურსია
- `PATCH` გამოიყენება status ცვლილებისთვის: `active`, `paused`, `completed`, `cancelled`

---

## 9. Lessons / Schedule

### Purpose
lesson instances-ის შექმნა და schedule views.

### Endpoints
- `GET /lessons`
- `POST /lessons`
- `GET /lessons/{lesson_id}`
- `PATCH /lessons/{lesson_id}`
- `GET /schedule`

### Filters for `GET /lessons`
- `date_from`
- `date_to`
- `group_id`
- `teacher_id`
- `status`

### `GET /schedule`
მიზანი:
- frontend-ს მისცეს daily / weekly view-სთვის მზად payload

### Notes
- lesson ინახება instance-ებად და recurring automation არ გვაქვს პირველ ვერსიაში fileciteturn1file53turn1file55
- `PATCH` შეიძლება გამოიყენოს cancel/reschedule flow-მა

---

## 10. Attendance

### Purpose
fast lesson-based attendance marking.

### Endpoints
- `GET /lessons/{lesson_id}/attendance`
- `POST /lessons/{lesson_id}/attendance/bulk-save`
- `PATCH /attendance/{attendance_id}`

### `bulk-save` behavior
იღებს array-ს:
- `student_id`
- `status`
- `comment` *(optional)*

### Notes
- attendance lesson-by-lesson ინახება fileciteturn1file53turn1file55
- ერთ lesson-ზე ერთ student-ს მაქსიმუმ ერთი attendance record უნდა ჰქონდეს fileciteturn1file55
- mark-all-present UI frontend concern-ია, მაგრამ საბოლოოდ bulk payload-ს აგზავნის backend-ში

---

## 11. Payments

### Purpose
payment tracking, debt/overdue visibility, history.

### Endpoints
- `GET /payments`
- `POST /payments`
- `GET /payments/{payment_id}`
- `PATCH /payments/{payment_id}`
- `GET /payments/overdue`
- `GET /students/{student_id}/payments`

### Filters for `GET /payments`
- `student_id`
- `group_id`
- `status`
- `date_from`
- `date_to`

### Notes
- `status` backend-ში ითვლება payment fields-იდან fileciteturn1file53turn1file55
- overdue list ცალკე endpoint-ად სასარგებლოა dashboard/action flow-სთვის

---

## 12. Reports

### Purpose
simple operational reporting.

### Endpoints
- `GET /reports/revenue-summary`
- `GET /reports/attendance-summary`
- `GET /reports/group-occupancy`
- `GET /reports/overdue-payments-summary`

### Notes
- ეს არ არის BI engine
- პირველ ვერსიაში reports აგებულია transactional tables-იდან fileciteturn1file55
- თუ საჭიროა, პირველი pass-ში ზოგი metric შეიძლება დარჩეს dashboard summary-ში და reports მოგვიანებით გაიშალოს

---

## 13. Notifications

### Purpose
architecture-ready placeholder for future integrations.

### Endpoints
- `GET /notifications/logs`
- `POST /notifications/mock-send` *(optional)*

### Notes
- რეალური SMS integration MVP-ში არ შედის fileciteturn1file53turn1file54turn1file55
- ეს მოდული არ არის პირველი scaffold-ის პრიორიტეტი

---

## Recommended Build Order

## Phase 1 — Foundation
1. `POST /auth/login`
2. `GET /auth/me`
3. `GET /dashboard/summary`
4. `GET /students`
5. `POST /students`
6. `GET /students/{student_id}`
7. `PATCH /students/{student_id}`
8. `GET /courses`
9. `POST /courses`
10. `GET /groups`
11. `POST /groups`
12. `GET /groups/{group_id}`
13. `POST /enrollments`

## Phase 2 — Operational Flow
14. `GET /lessons`
15. `POST /lessons`
16. `GET /schedule`
17. `GET /lessons/{lesson_id}/attendance`
18. `POST /lessons/{lesson_id}/attendance/bulk-save`
19. `GET /payments`
20. `POST /payments`
21. `GET /payments/overdue`

## Phase 3 — Expansion
22. `GET /teachers`
23. `POST /teachers`
24. `GET /teachers/{teacher_id}`
25. `GET /reports/revenue-summary`
26. `GET /reports/attendance-summary`
27. `GET /reports/group-occupancy`
28. `GET /notifications/logs`

---

## First Vertical Slice

პირველი რეალური end-to-end სამუშაო ჯაჭვი უნდა იყოს:
1. Login
2. Create Course
3. Create Student
4. Create Teacher
5. Create Group
6. Enroll Student to Group
7. Create Lesson
8. Mark Attendance
9. Add Payment
10. See Dashboard change

ეს ყველაზე კარგად ეწყობა უკვე დაფიქსირებულ MVP priorities-ს და core workflow-ს fileciteturn1file47turn1file53turn1file56

---

## Minimal Response Shape Guidance

პირველი scaffold-ისთვის რეკომენდებული პასუხების სტილი:
- list endpoints აბრუნებს:
  - `items`
  - `total`
- detail endpoints აბრუნებს ერთ რესურსს
- validation errors ბრუნდება სტანდარტულად FastAPI/Pydantic ფორმატში

---

## Explicit Non-Goals for API v1

ჯერ არ ვაკეთებთ:
- public third-party API keys
- webhook system
- advanced bulk import/export
- optimistic concurrency versioning
- complex audit history endpoints
- fine-grained permission matrix endpoints

---

## Build Consequence

ამ დოკუმენტიდან უკვე შეიძლება პირდაპირი გადასვლა:
- FastAPI route modules-ზე
- Pydantic schemas-ზე
- SQLAlchemy model-to-endpoint mapping-ზე
- backend scaffold-ის დირექტორიების სტრუქტურაზე

შემდეგი სწორი ნაბიჯი:
- `backend_scaffold_plan.md`
- ან პირდაპირ scaffold ფაილების შექმნა
