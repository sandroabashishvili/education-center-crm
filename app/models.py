from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    id: Optional[int] = None
    full_name: str = ""
    email: str = ""
    phone: str = ""
    role: str = "admin"  # admin, manager, teacher
    status: str = "active"
    created_at: str = ""


@dataclass
class Student:
    id: Optional[int] = None
    full_name: str = ""
    name: str = ""  # Backward compatibility alias
    email: str = ""
    phone: str = ""
    guardian_name: str = ""
    guardian_phone: str = ""
    status: str = "active"
    notes: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.full_name and self.name:
            self.full_name = self.name
        elif not self.name and self.full_name:
            self.name = self.full_name


@dataclass
class Course:
    id: Optional[int] = None
    name: str = ""
    title: str = ""  # Backward compatibility alias
    description: str = ""
    category: str = "General"
    default_fee: float = 0.0
    teacher: str = ""
    status: str = "active"
    created_at: str = ""

    def __post_init__(self):
        if not self.name and self.title:
            self.name = self.title
        elif not self.title and self.name:
            self.title = self.name


@dataclass
class Teacher:
    id: Optional[int] = None
    user_id: Optional[int] = None
    full_name: str = ""
    email: str = ""
    phone: str = ""
    specialization: str = ""
    status: str = "active"
    created_at: str = ""


@dataclass
class Group:
    id: Optional[int] = None
    course_id: int = 0
    teacher_id: Optional[int] = None
    name: str = ""
    capacity: int = 15
    start_date: str = ""
    end_date: str = ""
    schedule_description: str = ""
    status: str = "active"
    course_name: str = ""
    teacher_name: str = ""
    student_count: int = 0
    created_at: str = ""


@dataclass
class Lesson:
    id: Optional[int] = None
    group_id: int = 0
    teacher_id: Optional[int] = None
    starts_at: str = ""
    ends_at: str = ""
    room_label: str = "Room 101"
    delivery_mode: str = "in_person"
    topic: str = ""
    status: str = "scheduled"
    group_name: str = ""
    teacher_name: str = ""
    created_at: str = ""


@dataclass
class Attendance:
    id: Optional[int] = None
    lesson_id: int = 0
    student_id: int = 0
    status: str = "present"  # present, absent, late, excused
    note: str = ""
    marked_at: str = ""
    student_name: str = ""


@dataclass
class Payment:
    id: Optional[int] = None
    student_id: int = 0
    group_id: Optional[int] = None
    amount_due: float = 0.0
    amount_paid: float = 0.0
    due_date: str = ""
    paid_at: Optional[str] = None
    status: str = "pending"  # pending, partial, paid, overdue
    method: str = "cash"
    note: str = ""
    student_name: str = ""
    group_name: str = ""
    created_at: str = ""


@dataclass
class Enrollment:
    id: Optional[int] = None
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    status: str = "Active"
    payment_status: str = "Pending"
    amount_paid: float = 0.0
    student_name: str = ""
    course_title: str = ""
