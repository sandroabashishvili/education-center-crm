<!--
Created: 2026-07-14
Last updated: 2026-07-14
Status: Active
Owner: Project maintainer
Notes: Backend module structure for the current Flask MVP.
-->

🧱 backend_scaffold_plan.md
1. მიზანი

ეს დოკუმენტი განსაზღვრავს:

backend ფოლდერების სტრუქტურას
ფაილების naming წესებს
კოდის დაყოფის პრინციპს

👉 მიზანი:
სუფთა, გასაგები და გაფართოებადი FastAPI backend

2. Root Structure
backend/
  app/
    main.py
    core/
    db/
    models/
    schemas/
    api/
    services/
  requirements.txt
  .env
3. Folder Breakdown
📁 app/main.py

👉 entry point

FastAPI app init
router-ების ჩართვა
📁 core/

👉 config & shared logic

core/
  config.py
  security.py
env variables
auth helpers (later)
📁 db/

👉 database setup

db/
  base.py
  session.py
SQLAlchemy Base
DB connection
📁 models/

👉 database tables

models/
  user.py
  student.py
  teacher.py
  course.py
  group.py
  enrollment.py
  lesson.py
  attendance.py
  payment.py

👉 ეს მოდის პირდაპირ შენი domain_model_final-იდან

📁 schemas/

👉 request/response models (Pydantic)

schemas/
  student.py
  group.py
  course.py
  lesson.py
  attendance.py
  payment.py

👉 API input/output validation

📁 api/

👉 routes (endpoint-ები)

api/
  routes/
    auth.py
    students.py
    courses.py
    groups.py
    lessons.py
    attendance.py
    payments.py
📁 services/

👉 business logic layer

services/
  student_service.py
  group_service.py
  payment_service.py

👉 აქ იქნება:

payment status calculation
enrollment logic
attendance rules
4. Naming Rules
model: student.py → class Student
schema: StudentCreate, StudentResponse
route: /students
service: create_student()

👉 consistency = ძალიან მნიშვნელოვანია

5. პირველი build order (ძალიან მნიშვნელოვანია)

არ დაწერო ყველაფერი ერთად ❌

🔥 Phase 1 (first working slice)
DB connection
Student model
Student schema
/students endpoints:
POST
GET

👉 აქ უნდა გქონდეს უკვე:
working API

🔥 Phase 2
Course
Group
Enrollment
🔥 Phase 3
Lesson
Attendance
🔥 Phase 4
Payment logic
6. First Endpoint Example (რას ვაკეთებთ პირველივე ეტაპზე)
POST /students
GET /students

👉 ეს პატარაა, მაგრამ კრიტიკული:

DB მუშაობს?
API მუშაობს?
validation მუშაობს?

თუ ეს მუშაობს → მთელი პროექტი “გაიხსნა”

7. Architecture Rule (ძალიან მნიშვნელოვანია)

❌ route-ში არ ვწერთ ბიზნეს ლოგიკას
✅ ვიყენებთ service layer-ს

მაგალითად:

# route
create_student()

# service
handle student creation logic
8. Definition of Done (scaffold level)

შენ scaffold მზად გაქვს თუ:

პროექტი ეშვება (uvicorn main:app)
/students მუშაობს
DB-ში ინახება data
response ბრუნდება
