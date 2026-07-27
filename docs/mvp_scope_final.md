<!--
Created: 2026-07-14
Last updated: 2026-07-14
Status: Active
Owner: Project maintainer
Notes: MVP scope definition for the current CRM build.
-->

# Education Center CRM — MVP Scope Final (v1)

ბოლო განახლება: 2026-07-14

## 1. Scope Freeze

ამ დოკუმენტის მიზანია პირველი რეალური build-ის scope-ის ერთმნიშვნელოვნად დაფიქსირება.

პირველ ვერსიაში ვაშენებთ მხოლოდ იმ ფუნქციებს, რომლებიც საჭიროა სასწავლო ცენტრის ყოველდღიური ადმინისტრაციული ოპერაციების საჩვენებლად და სამართავად.

## 2. In Scope

### 2.1 Auth
- email + password login
- role-based access
- roles: `admin`, `manager`, `teacher`

### 2.2 Students
- სტუდენტის დამატება
- სტუდენტის რედაქტირება
- სტუდენტის სტატუსი: `active`, `inactive`, `archived`
- ტელეფონის და guardian contact-ის შენახვა
- სტუდენტის პროფილიდან ჯგუფის მიბმა

### 2.3 Courses
- კურსი MVP-ში არსებობს როგორც ცალკე entity
- საჭიროა მინიმალური CRUD:
  - create
  - list
  - edit
  - active/inactive status
- კურსი გამოიყენება ჯგუფის კონტექსტში და student-facing catalog არ იგება

### 2.4 Groups
- ჯგუფის შექმნა
- course-ის მიბმა
- teacher-ის მიბმა
- capacity-ის დაფიქსირება
- start/end date
- სტატუსები: `planned`, `active`, `completed`, `archived`
- ჯგუფის წევრების ნახვა
- სტუდენტის ჯგუფში დამატება/ამოღება

### 2.5 Schedule / Lessons
- lesson ინახება როგორც კონკრეტული instance
- admin/manager ქმნის lesson slot-ს ხელით
- daily / weekly / group-based / teacher-based ხედები
- lesson fields:
  - starts_at
  - ends_at
  - room_label
  - delivery_mode
  - status
- recurring automation პირველ ვერსიაში არ კეთდება

### 2.6 Attendance
- კონკრეტული lesson-ისთვის დასწრების მონიშვნა
- statuses:
  - `present`
  - `absent`
  - `late`
- bulk action: mark all present
- bulk save
- edit single record

### 2.7 Payments
- payment ჩანაწერი უკავშირდება student-ს და group-ს
- ინახება:
  - amount_due
  - amount_paid
  - due_date
  - paid_at
  - status
  - method
- statuses:
  - `pending`
  - `partial`
  - `paid`
  - `overdue`
- overdue განისაზღვრება due_date + unpaid balance-ით
- ერთი payment record შეიძლება წარმოადგენდეს ერთი პერიოდის გადასახადს
- ავტომატური recurring invoicing პირველ ვერსიაში არ კეთდება

### 2.8 Teachers
- teacher არსებობს როგორც ცალკე business entity
- teacher profile-ს აქვს მინიმალური CRUD
- teacher დაკავშირებულია `User`-თან login-ისთვის
- teacher screen აჩვენებს:
  - basic info
  - specialization
  - assigned groups
  - load summary

### 2.9 Notifications
- MVP-ში არ ვაკეთებთ რეალურ SMS integration-ს
- ვტოვებთ მხოლოდ notification-ready architecture-ს
- სურვილის შემთხვევაში UI-ში შეიძლება იყოს manual/mock send placeholder
- NotificationLog ინახება future readiness-ისთვის, მაგრამ ეს არ არის core workflow

### 2.10 Reports
პირველი ვერსიის dashboard/reporting metric-ები:
- total students
- active groups
- today lessons
- overdue payments count
- this month revenue
- attendance summary

## 3. Out of Scope

- parent portal
- student app
- online payment integration
- invoice automation
- payroll
- certificate/exam workflows
- advanced analytics
- export engine beyond placeholder
- multi-branch support
- complex notification campaigns

## 4. Build Priorities

### Phase 1
- Auth
- Dashboard
- Students
- Student Profile
- Courses
- Groups

### Phase 2
- Schedule
- Attendance
- Payments

### Phase 3
- Teachers
- Reports polish
- Notification placeholder

## 5. Implementation Defaults

სანამ სხვა რამ არ გადავწყვიტეთ, ვმუშაობთ ამ default-ებით:
- ერთი lesson = ერთი კონკრეტული scheduled session
- recurring timetable ავტომატიზაცია არ გვაქვს
- course არის ცალკე CRUD entity
- teacher არის ცალკე business entity
- payment სტატუსი backend-ში ითვლება
- dashboard metrics backend-იდან მოდის

## 6. Definition of MVP Done

MVP მზად არის როცა შესაძლებელია:
1. admin login
2. course შექმნა
3. student რეგისტრაცია
4. group შექმნა და course/teacher მიბმა
5. student-ის group-ში დამატება
6. lesson-ის შექმნა
7. attendance-ის მონიშვნა
8. payment-ის დამატება და overdue-ის ნახვა
9. dashboard-ზე ძირითადი სტატუსების ნახვა
