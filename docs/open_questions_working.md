<!--
Created: 2026-07-14
Last updated: 2026-07-14
Status: Draft
Owner: Project maintainer
Notes: Working notes for unresolved product and architecture decisions.
-->

# Education Center CRM — Working Decisions & Open Questions

ბოლო განახლება: 2026-07-14

ეს დოკუმენტი ინახავს იმ საკითხებს, რომლებიც გზადაგზა შეიძლება დაზუსტდეს, მაგრამ build-ს არ აჩერებს.

## უკვე დროებით დაფიქსირებული გადაწყვეტილებები

### 1. Course
გადაწყვეტილება: MVP-ში შედის როგორც მინიმალური CRUD entity.
მიზეზი: Group-ს სჭირდება მკაფიო course binding.

### 2. Notifications
გადაწყვეტილება: მხოლოდ notification-ready architecture.
მიზეზი: რეალური SMS integration ზედმეტად ამძიმებს პირველ build-ს.

### 3. Teacher Model
გადაწყვეტილება: Teacher არის ცალკე business entity + User login binding.
მიზეზი: მომავალში teacher profile და system user სხვადასხვა პასუხისმგებლობებს მოიცავს.

### 4. Lesson Model
გადაწყვეტილება: lesson ინახება როგორც კონკრეტული scheduled instance.
მიზეზი: ეს MVP-სთვის უფრო მარტივი და საკონტროლოა ვიდრე recurring engine.

### 5. Payment Logic
გადაწყვეტილება: payment სტატუსი ითვლება backend-ში.
მიზეზი: reporting და overdue control ერთ truth source-ზე უნდა იდგეს.

## ღია საკითხები, რომლებიც შემდეგ ეტაპზე შეიძლება დავაზუსტოთ

### 1. Payment Period Model
ჯერ არ გვაქვს საბოლოოდ დაფიქსირებული:
- თვიური billing period ცალკე ველით გვინდა თუ არა
- comment საკმარისია თუ არა პირველი ვერსიისთვის

დროებითი არჩევანი:
- პირველ build-ში ვიყენებთ `due_date` + `comment`-ს
- შემდეგ თუ დაგვჭირდა, დავამატებთ `billing_period_label` ველს

### 2. Guardian Data Depth
ჯერ არ გვაქვს განსაზღვრული:
- ერთი guardian თუ რამდენიმე contact
- address გვჭირდება თუ არა

დროებითი არჩევანი:
- ვინახავთ მხოლოდ `guardian_name` და `guardian_phone`

### 3. Reports Depth
ჯერ არ გვაქვს საბოლოო პასუხი:
- ცალკე reports გვერდზე რამდენი ბლოკი უნდა იყოს პირველ ვერსიაში

დროებითი არჩევანი:
- ვიწყებთ 4-6 ძირითად metric-ით და შემდეგ ვაფართოებთ

### 4. Permissions Granularity
ჯერ არ გვაქვს დეტალურად გაწერილი:
- manager და teacher ზუსტად რომელ actions ასრულებენ

დროებითი არჩევანი:
- `admin`: სრული წვდომა
- `manager`: თითქმის სრული ოპერაციული წვდომა
- `teacher`: თავის ჯგუფები, lessons, attendance view/update

## წესი

თუ რომელიმე ღია საკითხი build-ის დროს შეგვხვდა, default გადაწყვეტილებით ვაგრძელებთ და მხოლოდ საჭიროების შემთხვევაში ვაზუსტებთ.
