<!--
Created: 2026-07-14
Last updated: 2026-07-14
Status: Active
Owner: Project maintainer
Notes: Product brief and milestone direction for the current CRM project.
-->

# Education Center CRM — Project Brief (Final v1)

ბოლო განახლება: 2026-07-14
სტატუსი: active planning baseline

## 1. პროექტის მოკლე აღწერა

`Education Center CRM` არის სასწავლო ცენტრისთვის განკუთვნილი web-first ადმინისტრაციული სისტემა, რომელიც ფარავს სტუდენტების რეგისტრაციას, ჯგუფების მართვას, განრიგს, დასწრებას, გადახდებს, მასწავლებლებს და ძირითად ანგარიშგებას.

ეს არ არის full ERP. პირველი ვერსიის მიზანია მცირე, რეალისტური და დემონსტრირებადი CRM foundation.

## 2. პროდუქტის მიზანი

პირველი ვერსიის მიზანია:
- რეალური ადმინისტრაციული workflow-ის გამარტივება
- ბიზნეს-ლოგიკის სწორად დაფიქსირება backend-ში
- სწრაფი demo-ready სისტემის მიღება
- შემდგომი გაფართოების შესაძლებლობის დატოვება

## 3. ძირითადი მომხმარებლები

პირველი ვერსიის როლები:
- `admin`
- `manager`
- `teacher`

მოგვიანებით შესაძლო როლები:
- `student`
- `parent`

## 4. MVP მოდულები

პირველ ვერსიაში შედის:
- ავტორიზაცია
- სტუდენტების რეგისტრაცია და მართვა
- ჯგუფების მართვა
- კურსებთან მიბმა
- გაკვეთილების განრიგი
- დასწრების მონიშვნა
- გადახდების სტატუსების კონტროლი
- მასწავლებლების დირექტორია
- dashboard + ძირითადი რეპორტები

## 5. Non-MVP საზღვრები

პირველ ვერსიაში არ შედის:
- parent portal
- student mobile app
- ონლაინ გადახდები
- სრული accounting/ledger სისტემა
- payroll
- exam/certificate module
- multi-branch architecture
- production-grade SMS billing logic

## 6. პროდუქტის პრინციპები

პირველი build-ის პრინციპებია:
- მარტივი
- სუფთა
- რეალური
- სწრაფად გასაგები
- business-first
- extensible

## 7. არქიტექტურული მიმართულება

რეკომენდებული stack:
- Frontend: `Next.js + TypeScript + Tailwind CSS`
- Backend: `FastAPI + SQLAlchemy`
- Database: `PostgreSQL`
- Auth: role-based login

პრინციპი:
- business truth არის backend-ში
- UI არის lightweight admin interface
- სისტემა იგება მოდულურად

## 8. Build Philosophy

პირველი იმპლემენტაცია უნდა აშენდეს vertical slice პრინციპით.
ჯერ სრულდება ძირითადი end-to-end flow, შემდეგ ემატება დანარჩენი მოდულები.

საწყისი workflow:
1. Student creation
2. Group assignment
3. Lesson scheduling
4. Attendance marking
5. Payment tracking

## 9. წარმატების კრიტერიუმები

პირველი ვერსია წარმატებულია თუ:
- admin/manager სწრაფად ამატებს სტუდენტს
- სტუდენტის ჯგუფში გადანაწილება მარტივია
- კონკრეტული გაკვეთილისთვის დასწრება იინიშნება რამდენიმე კლიკში
- გადახდების overdue სტატუსი ნათლად ჩანს
- dashboard აჩვენებს მთავარ ბიზნეს სურათს
- demo დროს flow 2-3 წუთში გასაგებია

## 10. მიმდინარე სტატუსი

ამ მომენტში პროექტი ითვლება build-ready planning baseline-ად.
ეს ნიშნავს:
- scope უკვე მკაფიოა
- core entities განსაზღვრულია
- screen map ცნობილია
- შემდეგი ეტაპი არის final domain doc + scaffold
