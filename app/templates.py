# Master template styles and layouts for Education Center CRM

NAV_HEADER = """
<header class="topbar">
  <div class="brand">
    <span class="brand-badge">🎓</span>
    <div>
      <div style="font-weight: 700; font-size: 1.1rem;">Education Center CRM</div>
      <div style="font-size: 0.75rem; color: var(--muted);">Management System</div>
    </div>
  </div>
  <nav class="nav-links">
    <a href="{{ url_for('index') }}" class="nav-item {% if active_page == 'dashboard' %}active{% endif %}">📊 Dashboard</a>
    <a href="{{ url_for('students_page') }}" class="nav-item {% if active_page == 'students' %}active{% endif %}">👥 Students</a>
    <a href="{{ url_for('courses_page') }}" class="nav-item {% if active_page == 'courses' %}active{% endif %}">📚 Courses</a>
    <a href="{{ url_for('groups_page') }}" class="nav-item {% if active_page == 'groups' %}active{% endif %}">🏫 Groups</a>
    <a href="{{ url_for('lessons_page') }}" class="nav-item {% if active_page == 'lessons' %}active{% endif %}">📅 Schedule</a>
    <a href="{{ url_for('payments_page') }}" class="nav-item {% if active_page == 'payments' %}active{% endif %}">💰 Payments</a>
    <a href="{{ url_for('teachers_page') }}" class="nav-item {% if active_page == 'teachers' %}active{% endif %}">👨‍🏫 Teachers</a>
  </nav>
  <div class="auth-box">
    {% if session.get('logged_in') %}
      <span class="user-chip">
        <strong>{{ session.get('user_name') }}</strong>
        <small>{{ session.get('user_role') }}</small>
      </span>
      <form action="{{ url_for('logout') }}" method="POST" style="margin: 0;">
        <button type="submit" class="btn btn-sm btn-outline">Logout</button>
      </form>
    {% else %}
      <form action="{{ url_for('login') }}" method="POST" class="login-form">
        <input type="email" name="username" placeholder="admin@education.ge" autocomplete="username" required>
        <input type="password" name="password" placeholder="Password" autocomplete="current-password" required>
        <button type="submit" class="btn btn-sm">Login</button>
      </form>
    {% endif %}
  </div>
</header>
"""

STYLES = """
<style>
  :root {
    --primary: #4f46e5;
    --primary-hover: #4338ca;
    --secondary: #0f766e;
    --bg: #f8fafc;
    --surface: #ffffff;
    --text: #0f172a;
    --muted: #64748b;
    --border: #e2e8f0;
    --shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.08);
    --shadow-lg: 0 20px 30px -10px rgba(15, 23, 42, 0.12);
  }

  * { box-sizing: border-box; }
  body {
    overflow-x: hidden;
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    margin: 0;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }

  .container {
    width: 100%;
    min-width: 0;
    max-width: 1280px;
    margin: 0 auto;
    padding: 1.5rem 1rem 3rem;
  }

  .topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--surface);
    padding: 1rem 1.5rem;
    border-radius: 16px;
    box-shadow: var(--shadow);
    border: 1px solid var(--border);
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .brand { display: flex; align-items: center; gap: 0.75rem; }
  .brand-badge {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    border-radius: 12px;
    display: grid;
    place-items: center;
    font-size: 1.4rem;
  }

  .nav-links { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  .nav-item {
    padding: 0.5rem 0.9rem;
    border-radius: 10px;
    color: var(--muted);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.92rem;
    transition: all 0.2s ease;
  }
  .nav-item:hover, .nav-item.active {
    background: #eef2ff;
    color: var(--primary);
  }

  .auth-box { display: flex; align-items: center; gap: 0.6rem; margin-left: auto; }

  .hero {
    background: linear-gradient(135deg, #3730a3 0%, #4f46e5 50%, #0f766e 100%);
    color: white;
    padding: 2rem;
    border-radius: 20px;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-lg);
  }

  .hero h1 { margin: 0 0 0.4rem; font-size: 1.8rem; font-weight: 700; overflow-wrap: anywhere; word-break: break-word; max-width: 100%; }
  .hero p { margin: 0; opacity: 0.9; font-size: 0.95rem; overflow-wrap: anywhere; max-width: 100%; }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-card {
    background: var(--surface);
    padding: 1.2rem;
    border-radius: 16px;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: #eef2ff;
    color: var(--primary);
    display: grid;
    place-items: center;
    font-size: 1.3rem;
  }
  .stat-val { font-size: 1.5rem; font-weight: 700; color: var(--text); line-height: 1.2; }
  .stat-lbl { font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; }

  .card {
    background: var(--surface);
    padding: 1.5rem;
    border-radius: 18px;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    margin-bottom: 1.5rem;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid var(--border);
  }
  .card-title { font-size: 1.1rem; font-weight: 600; margin: 0; }

  table { width: 100%; border-collapse: collapse; text-align: left; }
  th { font-size: 0.75rem; text-transform: uppercase; color: var(--muted); padding: 0.75rem; border-bottom: 1px solid var(--border); }
  td { padding: 0.8rem 0.75rem; border-bottom: 1px solid var(--border); font-size: 0.9rem; }
  tr:hover { background: #f8fafc; }

  .badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: capitalize;
  }
  .badge-success { background: #dcfce7; color: #15803d; }
  .badge-warning { background: #fef9c3; color: #a16207; }
  .badge-danger { background: #fee2e2; color: #b91c1c; }
  .badge-info { background: #e0f2fe; color: #0369a1; }
  .badge-neutral { background: #f1f5f9; color: #475569; }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.6rem 1.2rem;
    border-radius: 10px;
    background: var(--primary);
    color: white;
    border: none;
    font-weight: 500;
    font-size: 0.88rem;
    cursor: pointer;
    text-decoration: none;
    transition: background 0.2s ease;
  }
  .btn:hover { background: var(--primary-hover); }
  .btn-sm { padding: 0.35rem 0.75rem; font-size: 0.8rem; border-radius: 8px; }
  .btn-secondary { background: #f1f5f9; color: var(--text); }
  .btn-secondary:hover { background: #e2e8f0; }
  .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
  .btn-outline:hover { background: #f1f5f9; }
  .btn-danger { background: #ef4444; color: white; }
  .btn-danger:hover { background: #dc2626; }

  .form-group { margin-bottom: 1rem; }
  .form-group label { display: block; font-size: 0.85rem; font-weight: 500; margin-bottom: 0.35rem; color: var(--text); }
  .form-control {
    width: 100%;
    padding: 0.65rem 0.85rem;
    border: 1px solid var(--border);
    border-radius: 10px;
    font-size: 0.9rem;
    background: var(--bg);
  }
  .form-control:focus { outline: 2px solid var(--primary); background: white; }

  .filter-bar {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    align-items: center;
  }

  .action-btns { display: flex; gap: 0.4rem; flex-wrap: wrap; }
  .login-form { display: grid; grid-template-columns: repeat(3, auto); gap: 0.4rem; margin: 0; }
  .login-form input {
    width: 170px;
    padding: 0.45rem 0.65rem;
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .user-chip { display: grid; line-height: 1.15; }
  .user-chip small { color: var(--muted); text-transform: capitalize; }
  .flash-stack { display: grid; gap: 0.5rem; margin-bottom: 1rem; }
  .flash {
    padding: 0.75rem 1rem;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--surface);
  }
  .flash-success { background: #ecfdf5; border-color: #a7f3d0; color: #166534; }
  .flash-warning { background: #fffbeb; border-color: #fde68a; color: #92400e; }
  .flash-danger { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
  .header-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: flex-end; }

  @media (max-width: 1050px) and (min-width: 761px) {
    .stats-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  }

  @media (max-width: 760px) {
    .container { padding: 0.75rem 0.65rem 2rem; }
    .topbar { align-items: flex-start; padding: 0.9rem; border-radius: 12px; }
    .topbar > *, .hero, .stats-grid, .card { min-width: 0; max-width: 100%; }
    .nav-links { width: 100%; max-width: 100%; min-width: 0; flex-wrap: nowrap; overflow-x: auto; padding-bottom: 0.25rem; }
    .nav-item { flex: 0 0 auto; }
    .auth-box, .login-form { width: 100%; margin-left: 0; }
    .login-form { grid-template-columns: 1fr; }
    .login-form input { width: 100%; min-width: 0; }
    .login-form .btn { width: 100%; justify-content: center; }
    .hero { padding: 1.35rem; border-radius: 15px; }
    .hero h1 { font-size: 1.45rem; }
    .grid-2 { grid-template-columns: 1fr; }
    .card { padding: 1rem; overflow-x: auto; border-radius: 14px; }
    .card-header { align-items: flex-start; gap: 0.75rem; flex-wrap: wrap; }
    table { min-width: 680px; }
    .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .stat-card { padding: 0.85rem; align-items: flex-start; }
    .stat-icon { width: 40px; height: 40px; flex: 0 0 auto; }
    .stat-val { font-size: 1.25rem; }
    [id$="Modal"] > div { margin: 0.75rem; max-height: calc(100vh - 1.5rem); overflow-y: auto; }
  }

  @media (max-width: 600px) {
    .hero h1 { font-size: 1.2rem; line-height: 1.25; }
    .hero p { font-size: 0.86rem; }
    .stats-grid { grid-template-columns: 1fr; }
    .header-actions, .header-actions .btn { width: 100%; }
    .header-actions .btn { justify-content: center; }
  }
</style>
"""

BASE_LAYOUT = """<!doctype html>
<html lang="ka">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ PAGE_TITLE }} - Education Center CRM</title>
  PAGE_STYLES_HERE
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%234f46e5'/%3E%3Ctext x='50' y='58' font-size='52' text-anchor='middle' fill='white' font-family='Arial,sans-serif'%3E%F0%9F%8E%93%3C/text%3E%3C/svg%3E">
</head>
<body>
  <div class="container">
    PAGE_NAV_HEADER_HERE
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
      <div class="flash-stack" role="status">
        {% for category, message in messages %}
        <div class="flash flash-{{ category }}">{{ message }}</div>
        {% endfor %}
      </div>
      {% endif %}
    {% endwith %}
    PAGE_CONTENT_HERE
  </div>
</body>
</html>
"""

def render_page(title, content, active_page="dashboard"):
    nav = NAV_HEADER.replace("{{ active_page }}", active_page)
    page = BASE_LAYOUT.replace("{{ PAGE_TITLE }}", title)
    page = page.replace("PAGE_STYLES_HERE", STYLES)
    page = page.replace("PAGE_NAV_HEADER_HERE", nav)
    page = page.replace("PAGE_CONTENT_HERE", content)
    return page

# 1. Dashboard Template
DASHBOARD_HTML = render_page(
    "Dashboard",
    """
    <div class="hero">
      <h1>გამარჯობა, ადმინისტრატორო!</h1>
      <p>სტუდენტები, ჯგუფები, დასწრება და გადახდები — ერთ სამუშაო სივრცეში.</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div>
          <div class="stat-val">{{ metrics.total_students }}</div>
          <div class="stat-lbl">აქტიური სტუდენტი</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📚</div>
        <div>
          <div class="stat-val">{{ metrics.total_courses }}</div>
          <div class="stat-lbl">კურსები</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🏫</div>
        <div>
          <div class="stat-val">{{ metrics.active_groups }}</div>
          <div class="stat-lbl">აქტიური ჯგუფები</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📅</div>
        <div>
          <div class="stat-val">{{ metrics.today_lessons }}</div>
          <div class="stat-lbl">დღევანდელი გაკვეთილი</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⚠️</div>
        <div>
          <div class="stat-val" style="color: {% if metrics.overdue_payments > 0 %}#dc2626{% else %}inherit{% endif %};">{{ metrics.overdue_payments }}</div>
          <div class="stat-lbl">ვადაგადაცილებული</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">💰</div>
        <div>
          <div class="stat-val">₾{{ "%.2f"|format(metrics.monthly_revenue) }}</div>
          <div class="stat-lbl">მიმდინარე თვის შემოსავალი</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div>
          <div class="stat-val">{{ metrics.attendance_rate }}%</div>
          <div class="stat-lbl">დასწრების მაჩვენებელი</div>
        </div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">👥 ბოლოს დამატებული სტუდენტები</h3>
          <a href="{{ url_for('students_page') }}" class="btn btn-sm btn-outline">ყველას ნახვა</a>
        </div>
        <table>
          <thead>
            <tr><th>ID</th><th>სახელი, გვარი</th><th>ელ-ფოსტა</th><th>მოქმედება</th></tr>
          </thead>
          <tbody>
            {% for s in metrics.recent_students %}
            <tr>
              <td>#{{ s[0] }}</td>
              <td><strong>{{ s[1] }}</strong></td>
              <td>{{ s[2] }}</td>
              <td><a href="{{ url_for('student_detail_page', student_id=s[0]) }}" class="btn btn-sm btn-outline">პროფილი</a></td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align: center; color: var(--muted);">სტუდენტები ჯერ არ არის</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">💰 ბოლო გადახდები</h3>
          <a href="{{ url_for('payments_page') }}" class="btn btn-sm btn-outline">ყველა გადახდა</a>
        </div>
        <table>
          <thead>
            <tr><th>სტუდენტი</th><th>თანხა</th><th>სტატუსი</th><th>ვადა</th></tr>
          </thead>
          <tbody>
            {% for p in metrics.recent_payments %}
            <tr>
              <td><strong>{{ p[1] }}</strong></td>
              <td>₾{{ "%.2f"|format(p[2]) }}</td>
              <td>
                <span class="badge {% if p[3] == 'paid' %}badge-success{% elif p[3] == 'partial' %}badge-info{% elif p[3] == 'overdue' %}badge-danger{% else %}badge-warning{% endif %}">
                  {{ p[3] }}
                </span>
              </td>
              <td>{{ p[4] }}</td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align: center; color: var(--muted);">გადახდები არ არის</td></tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
    """,
    active_page="dashboard"
)

# 2. Students Page Template
STUDENTS_HTML = render_page(
    "სტუდენტები",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">👥 სტუდენტების მართვა</h3>
        <div class="header-actions">
          {% if session.get('logged_in') %}
          <a href="{{ url_for('export_students_csv') }}" class="btn btn-outline">CSV ექსპორტი</a>
          <button onclick="document.getElementById('addStudentModal').style.display='flex'" class="btn">+ ახალი სტუდენტი</button>
          {% endif %}
        </div>
      </div>

      <form method="GET" class="filter-bar">
        <input type="text" name="q" value="{{ query }}" placeholder="ძებნა სახელით, ელ-ფოსტით ან ტელეფონით..." class="form-control" style="max-width: 320px;">
        <select name="status" class="form-control" style="max-width: 180px;">
          <option value="all" {% if status_filter == 'all' %}selected{% endif %}>ყველა სტატუსი</option>
          <option value="active" {% if status_filter == 'active' %}selected{% endif %}>Active</option>
          <option value="inactive" {% if status_filter == 'inactive' %}selected{% endif %}>Inactive</option>
        </select>
        <button type="submit" class="btn btn-secondary">ძებნა</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>სახელი, გვარი</th>
            <th>ელ-ფოსტა</th>
            <th>ტელეფონი</th>
            <th>მშობელი/მეთვალყურე</th>
            <th>სტატუსი</th>
            <th>მოქმედება</th>
          </tr>
        </thead>
        <tbody>
          {% for s in students %}
          <tr>
            <td>#{{ s[0] }}</td>
            <td><strong>{{ s[1] }}</strong></td>
            <td>{{ s[2] }}</td>
            <td>{{ s[3] or 'N/A' }}</td>
            <td>{{ s[4] or '-' }} ({{ s[5] or '-' }})</td>
            <td>
              <span class="badge {% if s[6] == 'active' %}badge-success{% else %}badge-neutral{% endif %}">{{ s[6] }}</span>
            </td>
            <td>
              <div class="action-btns">
                <a href="{{ url_for('student_detail_page', student_id=s[0]) }}" class="btn btn-sm btn-outline">ნახვა</a>
                {% if session.get('logged_in') %}
                <a href="{{ url_for('edit_student', student_id=s[0]) }}" class="btn btn-sm btn-secondary">რედაქტირება</a>
                <form action="{{ url_for('delete_student', student_id=s[0]) }}" method="POST" style="margin:0;" onsubmit="return confirm('დარწმუნებული ხართ?');">
                  <button type="submit" class="btn btn-sm btn-danger">წაშლა</button>
                </form>
                {% endif %}
              </div>
            </td>
          </tr>
          {% else %}
          <tr><td colspan="7" style="text-align: center; color: var(--muted); padding: 2rem;">სტუდენტები ვერ მოიძებნა</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Modal Add Student -->
    <div id="addStudentModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 99; align-items: center; justify-content: center;">
      <div style="background: white; padding: 1.5rem; border-radius: 16px; width: min(100%, 480px);">
        <h3>+ ახალი სტუდენტის დამატება</h3>
        <form action="{{ url_for('add_student_route') }}" method="POST">
          <div class="form-group">
            <label>სრული სახელი და გვარი *</label>
            <input type="text" name="full_name" required class="form-control">
          </div>
          <div class="form-group">
            <label>ელ-ფოსტა *</label>
            <input type="email" name="email" required class="form-control">
          </div>
          <div class="form-group">
            <label>ტელეფონის ნომერი</label>
            <input type="text" name="phone" class="form-control">
          </div>
          <div class="form-group">
            <label>მშობლის/მეთვალყურის სახელი</label>
            <input type="text" name="guardian_name" class="form-control">
          </div>
          <div class="form-group">
            <label>მშობლის ტელეფონი</label>
            <input type="text" name="guardian_phone" class="form-control">
          </div>
          <div class="form-group">
            <label>შენიშვნა</label>
            <textarea name="notes" class="form-control" rows="2"></textarea>
          </div>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <button type="button" onclick="document.getElementById('addStudentModal').style.display='none'" class="btn btn-secondary">გაუქმება</button>
            <button type="submit" class="btn">შენახვა</button>
          </div>
        </form>
      </div>
    </div>
    """,
    active_page="students"
)

# 3. Student Detail Page Template
STUDENT_DETAIL_HTML = render_page(
    "სტუდენტის პროფილი",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">👤 სტუდენტის პროფილი: {{ student[1] }}</h3>
        <a href="{{ url_for('students_page') }}" class="btn btn-sm btn-outline">← უკან დაბრუნება</a>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; background: #f8fafc; padding: 1rem; border-radius: 12px;">
        <div><strong>ID:</strong> #{{ student[0] }}</div>
        <div><strong>ელ-ფოსტა:</strong> {{ student[2] }}</div>
        <div><strong>ტელეფონი:</strong> {{ student[3] or 'N/A' }}</div>
        <div><strong>მშობელი:</strong> {{ student[4] or '-' }} ({{ student[5] or '-' }})</div>
        <div><strong>სტატუსი:</strong> <span class="badge badge-success">{{ student[6] }}</span></div>
        <div><strong>შენიშვნა:</strong> {{ student[7] or '-' }}</div>
      </div>

      <h4>🏫 ჯგუფები & კურსები</h4>
      <table>
        <thead>
          <tr><th>ჯგუფის სახელი</th><th>კურსი</th><th>სტატუსი</th><th>წევრია (თარიღიდან)</th></tr>
        </thead>
        <tbody>
          {% for g in groups %}
          <tr>
            <td><strong>{{ g[1] }}</strong></td>
            <td>{{ g[2] }}</td>
            <td><span class="badge badge-info">{{ g[3] }}</span></td>
            <td>{{ g[4] }}</td>
          </tr>
          {% else %}
          <tr><td colspan="4" style="text-align: center; color: var(--muted);">სტუდენტი ჯერ არ არის ჯგუფში</td></tr>
          {% endfor %}
        </tbody>
      </table>

      <h4 style="margin-top: 1.5rem;">💰 გადახდების ისტორია</h4>
      <table>
        <thead>
          <tr><th>ID</th><th>დასაფარი თანხა</th><th>გადახდილი</th><th>ვადა</th><th>სტატუსი</th><th>გადახდის თარიღი</th></tr>
        </thead>
        <tbody>
          {% for p in payments %}
          <tr>
            <td>#{{ p[0] }}</td>
            <td>₾{{ "%.2f"|format(p[1]) }}</td>
            <td>₾{{ "%.2f"|format(p[2]) }}</td>
            <td>{{ p[3] }}</td>
            <td>
              <span class="badge {% if p[4] == 'paid' %}badge-success{% elif p[4] == 'partial' %}badge-info{% elif p[4] == 'overdue' %}badge-danger{% else %}badge-warning{% endif %}">
                {{ p[4] }}
              </span>
            </td>
            <td>{{ p[5] or '-' }}</td>
          </tr>
          {% else %}
          <tr><td colspan="6" style="text-align: center; color: var(--muted);">გადახდის ისტორია სუფთაა</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    """,
    active_page="students"
)

# 4. Courses Page Template
COURSES_HTML = render_page(
    "კურსები",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">📚 კურსების კატალოგი</h3>
        {% if session.get('logged_in') %}
        <button onclick="document.getElementById('addCourseModal').style.display='flex'" class="btn">+ ახალი კურსი</button>
        {% endif %}
      </div>

      <table>
        <thead>
          <tr><th>ID</th><th>კურსის დასახელება</th><th>კატეგორია</th><th>სტანდარტული საფასური</th><th>პედაგოგი</th><th>სტატუსი</th><th>მოქმედება</th></tr>
        </thead>
        <tbody>
          {% for c in courses %}
          <tr>
            <td>#{{ c[0] }}</td>
            <td><strong>{{ c[1] }}</strong><br><small style="color: var(--muted);">{{ c[2] or '' }}</small></td>
            <td><span class="badge badge-info">{{ c[3] or 'General' }}</span></td>
            <td>₾{{ "%.2f"|format(c[4] or 0) }}</td>
            <td>{{ c[5] or 'Unassigned' }}</td>
            <td><span class="badge badge-success">{{ c[6] }}</span></td>
            <td>
              {% if session.get('logged_in') %}
              <form action="{{ url_for('delete_course', course_id=c[0]) }}" method="POST" style="margin:0;" onsubmit="return confirm('წავშალოთ კურსი?');">
                <button type="submit" class="btn btn-sm btn-danger">წაშლა</button>
              </form>
              {% endif %}
            </td>
          </tr>
          {% else %}
          <tr><td colspan="7" style="text-align: center; color: var(--muted); padding: 2rem;">კურსები ვერ მოიძებნა</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Modal Add Course -->
    <div id="addCourseModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 99; align-items: center; justify-content: center;">
      <div style="background: white; padding: 1.5rem; border-radius: 16px; width: min(100%, 480px);">
        <h3>+ ახალი კურსის დამატება</h3>
        <form action="{{ url_for('add_course_route') }}" method="POST">
          <div class="form-group">
            <label>კურსის დასახელება *</label>
            <input type="text" name="name" required class="form-control">
          </div>
          <div class="form-group">
            <label>კატეგორია</label>
            <input type="text" name="category" placeholder="Programming, Languages..." class="form-control">
          </div>
          <div class="form-group">
            <label>სტანდარტული საფასური (₾)</label>
            <input type="number" step="0.01" name="default_fee" value="300" class="form-control">
          </div>
          <div class="form-group">
            <label>პედაგოგის სახელი</label>
            <input type="text" name="teacher" class="form-control">
          </div>
          <div class="form-group">
            <label>აღწერა</label>
            <textarea name="description" class="form-control" rows="2"></textarea>
          </div>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <button type="button" onclick="document.getElementById('addCourseModal').style.display='none'" class="btn btn-secondary">გაუქმება</button>
            <button type="submit" class="btn">დამატება</button>
          </div>
        </form>
      </div>
    </div>
    """,
    active_page="courses"
)

# 5. Groups Page Template
GROUPS_HTML = render_page(
    "ჯგუფები",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">🏫 სასწავლო ჯგუფები</h3>
        {% if session.get('logged_in') %}
        <button onclick="document.getElementById('addGroupModal').style.display='flex'" class="btn">+ ახალი ჯგუფი</button>
        {% endif %}
      </div>

      <table>
        <thead>
          <tr><th>ID</th><th>ჯგუფის სახელი</th><th>კურსი</th><th>პედაგოგი</th><th>სტუდენტები (ტევადობა)</th><th>განრიგი</th><th>სტატუსი</th><th>მოქმედება</th></tr>
        </thead>
        <tbody>
          {% for g in groups %}
          <tr>
            <td>#{{ g[0] }}</td>
            <td><strong>{{ g[1] }}</strong></td>
            <td>{{ g[2] }}</td>
            <td>{{ g[3] }}</td>
            <td><span class="badge badge-info">{{ g[5] }} / {{ g[4] }}</span></td>
            <td>{{ g[6] or 'დაუდგენელია' }}</td>
            <td><span class="badge badge-success">{{ g[7] }}</span></td>
            <td>
              <a href="{{ url_for('group_detail_page', group_id=g[0]) }}" class="btn btn-sm btn-outline">დეტალები</a>
            </td>
          </tr>
          {% else %}
          <tr><td colspan="8" style="text-align: center; color: var(--muted); padding: 2rem;">ჯგუფები არ არის შექმნილი</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Modal Add Group -->
    <div id="addGroupModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 99; align-items: center; justify-content: center;">
      <div style="background: white; padding: 1.5rem; border-radius: 16px; width: min(100%, 480px);">
        <h3>+ ახალი ჯგუფის შექმნა</h3>
        <form action="{{ url_for('add_group_route') }}" method="POST">
          <div class="form-group">
            <label>კურსი *</label>
            <select name="course_id" required class="form-control">
              {% for c in courses %}
              <option value="{{ c[0] }}">{{ c[1] }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-group">
            <label>პედაგოგი</label>
            <select name="teacher_id" class="form-control">
              <option value="">-- აირჩიეთ --</option>
              {% for t in teachers %}
              <option value="{{ t[0] }}">{{ t[1] }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-group">
            <label>ჯგუფის დასახელება *</label>
            <input type="text" name="name" required placeholder="მაგ: Python 2026 - Evening" class="form-control">
          </div>
          <div class="form-group">
            <label>ტევადობა (მაქს. სტუდენტი)</label>
            <input type="number" name="capacity" value="15" class="form-control">
          </div>
          <div class="form-group">
            <label>განრიგის აღწერა</label>
            <input type="text" name="schedule_description" placeholder="ორშაბათი - ოთხშაბათი 19:00" class="form-control">
          </div>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <button type="button" onclick="document.getElementById('addGroupModal').style.display='none'" class="btn btn-secondary">გაუქმება</button>
            <button type="submit" class="btn">შექმნა</button>
          </div>
        </form>
      </div>
    </div>
    """,
    active_page="groups"
)

# 6. Group Detail Template
GROUP_DETAIL_HTML = render_page(
    "ჯგუფის დეტალები",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">🏫 ჯგუფი: {{ group[1] }}</h3>
        <a href="{{ url_for('groups_page') }}" class="btn btn-sm btn-outline">← ჯგუფების სია</a>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; background: #f8fafc; padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;">
        <div><strong>კურსი:</strong> {{ group[2] }}</div>
        <div><strong>პედაგოგი:</strong> {{ group[3] }}</div>
        <div><strong>ტევადობა:</strong> {{ members|length }} / {{ group[4] }}</div>
        <div><strong>განრიგი:</strong> {{ group[7] or '-' }}</div>
        <div><strong>სტატუსი:</strong> <span class="badge badge-success">{{ group[8] }}</span></div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h4>👨‍🎓 ჯგუფის წევრები (სტუდენტები)</h4>
        {% if session.get('logged_in') %}
        <button onclick="document.getElementById('enrollModal').style.display='flex'" class="btn btn-sm">+ სტუდენტის დამატება ჯგუფში</button>
        {% endif %}
      </div>

      <table>
        <thead>
          <tr><th>ID</th><th>სახელი, გვარი</th><th>ელ-ფოსტა</th><th>ტელეფონი</th><th>წევრობის სტატუსი</th></tr>
        </thead>
        <tbody>
          {% for m in members %}
          <tr>
            <td>#{{ m[0] }}</td>
            <td><strong>{{ m[1] }}</strong></td>
            <td>{{ m[2] }}</td>
            <td>{{ m[3] or '-' }}</td>
            <td><span class="badge badge-success">{{ m[5] }}</span></td>
          </tr>
          {% else %}
          <tr><td colspan="5" style="text-align: center; color: var(--muted);">ჯგუფში სტუდენტები არ არის ჩარიცხული</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Modal Enroll Student -->
    <div id="enrollModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 99; align-items: center; justify-content: center;">
      <div style="background: white; padding: 1.5rem; border-radius: 16px; width: min(100%, 420px);">
        <h3>+ სტუდენტის ჩარიცხვა ჯგუფში</h3>
        <form action="{{ url_for('enroll_student_route', group_id=group[0]) }}" method="POST">
          <div class="form-group">
            <label>აირჩიეთ სტუდენტი *</label>
            <select name="student_id" required class="form-control">
              {% for s in all_students %}
              <option value="{{ s[0] }}">{{ s[1] }} ({{ s[2] }})</option>
              {% endfor %}
            </select>
          </div>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <button type="button" onclick="document.getElementById('enrollModal').style.display='none'" class="btn btn-secondary">გაუქმება</button>
            <button type="submit" class="btn">ჩარიცხვა</button>
          </div>
        </form>
      </div>
    </div>
    """,
    active_page="groups"
)

# 7. Lessons & Attendance Schedule Template
LESSONS_HTML = render_page(
    "გაკვეთილების განრიგი",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">📅 გაკვეთილების განრიგი & დასწრება</h3>
        {% if session.get('logged_in') %}
        <button onclick="document.getElementById('addLessonModal').style.display='flex'" class="btn">+ გაკვეთილის ჩანიშვნა</button>
        {% endif %}
      </div>

      <table>
        <thead>
          <tr><th>ID</th><th>ჯგუფი</th><th>პედაგოგი</th><th>დაწყება</th><th>ოთახი</th><th>თემა</th><th>სტატუსი</th><th>დასწრება</th></tr>
        </thead>
        <tbody>
          {% for l in lessons %}
          <tr>
            <td>#{{ l[0] }}</td>
            <td><strong>{{ l[1] }}</strong></td>
            <td>{{ l[2] }}</td>
            <td>{{ l[3] }}</td>
            <td><span class="badge badge-neutral">{{ l[5] }}</span></td>
            <td>{{ l[6] or '-' }}</td>
            <td><span class="badge badge-info">{{ l[7] }}</span></td>
            <td>
              <a href="{{ url_for('attendance_page', lesson_id=l[0]) }}" class="btn btn-sm btn-outline">📝 დასწრების მონიშვნა</a>
            </td>
          </tr>
          {% else %}
          <tr><td colspan="8" style="text-align: center; color: var(--muted); padding: 2rem;">ჩანიშნული გაკვეთილები არ არის</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Modal Add Lesson -->
    <div id="addLessonModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 99; align-items: center; justify-content: center;">
      <div style="background: white; padding: 1.5rem; border-radius: 16px; width: min(100%, 480px);">
        <h3>+ ახალი გაკვეთილის ჩანიშვნა</h3>
        <form action="{{ url_for('add_lesson_route') }}" method="POST">
          <div class="form-group">
            <label>ჯგუფი *</label>
            <select name="group_id" required class="form-control">
              {% for g in groups %}
              <option value="{{ g[0] }}">{{ g[1] }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-group">
            <label>დაწყების დრო *</label>
            <input type="datetime-local" name="starts_at" required class="form-control">
          </div>
          <div class="form-group">
            <label>დასრულების დრო *</label>
            <input type="datetime-local" name="ends_at" required class="form-control">
          </div>
          <div class="form-group">
            <label>ოთახი / აუდიტორია</label>
            <input type="text" name="room_label" value="Room 101" class="form-control">
          </div>
          <div class="form-group">
            <label>გაკვეთილის თემა</label>
            <input type="text" name="topic" placeholder="მაგ: Functions & Loops" class="form-control">
          </div>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <button type="button" onclick="document.getElementById('addLessonModal').style.display='none'" class="btn btn-secondary">გაუქმება</button>
            <button type="submit" class="btn">ჩანიშვნა</button>
          </div>
        </form>
      </div>
    </div>
    """,
    active_page="lessons"
)

# 8. Attendance Marking Template
ATTENDANCE_HTML = render_page(
    "დასწრების მონიშვნა",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">📝 დასწრების მონიშვნა: {{ lesson[1] }} ({{ lesson[3] }})</h3>
        <a href="{{ url_for('lessons_page') }}" class="btn btn-sm btn-outline">← განრიგში დაბრუნება</a>
      </div>

      <form action="{{ url_for('save_attendance_route', lesson_id=lesson[0]) }}" method="POST">
        <table>
          <thead>
            <tr><th>სტუდენტი</th><th>დასწრების სტატუსი</th><th>შენიშვნა</th></tr>
          </thead>
          <tbody>
            {% for r in records %}
            <tr>
              <td><strong>{{ r[1] }}</strong></td>
              <td>
                <select name="status_{{ r[0] }}" class="form-control" style="width: 160px; display: inline-block;">
                  <option value="present" {% if r[2] == 'present' %}selected{% endif %}>🟢 Present (ესწრება)</option>
                  <option value="absent" {% if r[2] == 'absent' %}selected{% endif %}>🔴 Absent (არაა)</option>
                  <option value="late" {% if r[2] == 'late' %}selected{% endif %}>🟡 Late (დააგვიანა)</option>
                  <option value="excused" {% if r[2] == 'excused' %}selected{% endif %}>⚪ Excused (საპატიო)</option>
                </select>
              </td>
              <td>
                <input type="text" name="note_{{ r[0] }}" value="{{ r[3] }}" placeholder="შენიშვნა..." class="form-control">
              </td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align: center; color: var(--muted);">ამ ჯგუფში სტუდენტები არ არის ჩარიცხული</td></tr>
            {% endfor %}
          </tbody>
        </table>

        {% if records %}
        <div style="margin-top: 1.5rem; display: flex; justify-content: flex-end;">
          <button type="submit" class="btn">💾 დასწრების შენახვა</button>
        </div>
        {% endif %}
      </form>
    </div>
    """,
    active_page="lessons"
)

# 9. Payments Page Template
PAYMENTS_HTML = render_page(
    "გადახდები",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">💰 გადახდები & ინვოისები</h3>
        <div class="header-actions">
          {% if session.get('logged_in') %}
          <a href="{{ url_for('export_payments_csv') }}" class="btn btn-outline">CSV ექსპორტი</a>
          <button onclick="document.getElementById('addPaymentModal').style.display='flex'" class="btn">+ ინვოისის შექმნა</button>
          {% endif %}
        </div>
      </div>

      <form method="GET" class="filter-bar">
        <select name="status" class="form-control" style="max-width: 200px;">
          <option value="all" {% if status_filter == 'all' %}selected{% endif %}>ყველა გადახდა</option>
          <option value="paid" {% if status_filter == 'paid' %}selected{% endif %}>Paid (გადახდილი)</option>
          <option value="partial" {% if status_filter == 'partial' %}selected{% endif %}>Partial (ნაწილობრივ)</option>
          <option value="pending" {% if status_filter == 'pending' %}selected{% endif %}>Pending (მოლოდინში)</option>
          <option value="overdue" {% if status_filter == 'overdue' %}selected{% endif %}>Overdue (ვადაგადაცილებული)</option>
        </select>
        <button type="submit" class="btn btn-secondary">ფილტრი</button>
      </form>

      <table>
        <thead>
          <tr><th>ID</th><th>სტუდენტი</th><th>ჯგუფი</th><th>გადასახდელი</th><th>გადახდილი</th><th>ვადა</th><th>სტატუსი</th><th>გადახდის მეთოდი</th><th>მოქმედება</th></tr>
        </thead>
        <tbody>
          {% for p in payments %}
          <tr>
            <td>#{{ p[0] }}</td>
            <td><strong>{{ p[1] }}</strong></td>
            <td>{{ p[2] }}</td>
            <td>₾{{ "%.2f"|format(p[3]) }}</td>
            <td>₾{{ "%.2f"|format(p[4]) }}</td>
            <td>{{ p[5] }}</td>
            <td>
              <span class="badge {% if p[7] == 'paid' %}badge-success{% elif p[7] == 'partial' %}badge-info{% elif p[7] == 'overdue' %}badge-danger{% else %}badge-warning{% endif %}">
                {{ p[7] }}
              </span>
            </td>
            <td>{{ p[8] or 'cash' }}</td>
            <td>
              {% if p[7] != 'paid' and session.get('logged_in') %}
              <button onclick="openPayModal({{ p[0] }}, {{ p[3] - p[4] }})" class="btn btn-sm btn-outline">💵 თანხის მიღება</button>
              {% endif %}
            </td>
          </tr>
          {% else %}
          <tr><td colspan="9" style="text-align: center; color: var(--muted); padding: 2rem;">გადახდები ვერ მოიძებნა</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Modal Add Invoice -->
    <div id="addPaymentModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 99; align-items: center; justify-content: center;">
      <div style="background: white; padding: 1.5rem; border-radius: 16px; width: min(100%, 480px);">
        <h3>+ ახალი ინვოისის შექმნა</h3>
        <form action="{{ url_for('add_payment_route') }}" method="POST">
          <div class="form-group">
            <label>სტუდენტი *</label>
            <select name="student_id" required class="form-control">
              {% for s in students %}
              <option value="{{ s[0] }}">{{ s[1] }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-group">
            <label>ჯგუფი</label>
            <select name="group_id" class="form-control">
              <option value="">-- არცერთი --</option>
              {% for g in groups %}
              <option value="{{ g[0] }}">{{ g[1] }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-group">
            <label>დასაფარი თანხა (₾) *</label>
            <input type="number" step="0.01" name="amount_due" required value="300.00" class="form-control">
          </div>
          <div class="form-group">
            <label>გადახდის ვადა *</label>
            <input type="date" name="due_date" required class="form-control">
          </div>
          <div class="form-group">
            <label>შენიშვნა</label>
            <input type="text" name="note" placeholder="მაგ: ივლისის სწავლის საფასური" class="form-control">
          </div>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <button type="button" onclick="document.getElementById('addPaymentModal').style.display='none'" class="btn btn-secondary">გაუქმება</button>
            <button type="submit" class="btn">შექმნა</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Pay Receipt -->
    <div id="payModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 99; align-items: center; justify-content: center;">
      <div style="background: white; padding: 1.5rem; border-radius: 16px; width: min(100%, 420px);">
        <h3>💵 თანხის მიღების დაფიქსირება</h3>
        <form action="{{ url_for('record_payment_route') }}" method="POST">
          <input type="hidden" name="payment_id" id="pay_payment_id">
          <div class="form-group">
            <label>გადახდილი თანხა (₾) *</label>
            <input type="number" step="0.01" name="amount_paid" id="pay_amount" required class="form-control">
          </div>
          <div class="form-group">
            <label>გადახდის თარიღი</label>
            <input type="date" name="paid_at" value="{{ today_date }}" class="form-control">
          </div>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <button type="button" onclick="document.getElementById('payModal').style.display='none'" class="btn btn-secondary">გაუქმება</button>
            <button type="submit" class="btn">დაფიქსირება</button>
          </div>
        </form>
      </div>
    </div>

    <script>
      function openPayModal(paymentId, remaining) {
        document.getElementById('pay_payment_id').value = paymentId;
        document.getElementById('pay_amount').value = remaining > 0 ? remaining : 0;
        document.getElementById('payModal').style.display = 'flex';
      }
    </script>
    """,
    active_page="payments"
)

# 10. Teachers Page Template
TEACHERS_HTML = render_page(
    "პედაგოგები",
    """
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">👨‍🏫 პედაგოგების დირექტორია</h3>
        {% if session.get('logged_in') %}
        <button onclick="document.getElementById('addTeacherModal').style.display='flex'" class="btn">+ ახალი პედაგოგი</button>
        {% endif %}
      </div>

      <table>
        <thead>
          <tr><th>ID</th><th>სახელი, გვარი</th><th>ელ-ფოსტა</th><th>ტელეფონი</th><th>სპეციალიზაცია</th><th>სტატუსი</th></tr>
        </thead>
        <tbody>
          {% for t in teachers %}
          <tr>
            <td>#{{ t[0] }}</td>
            <td><strong>{{ t[1] }}</strong></td>
            <td>{{ t[2] }}</td>
            <td>{{ t[3] or '-' }}</td>
            <td><span class="badge badge-info">{{ t[4] or 'General' }}</span></td>
            <td><span class="badge badge-success">{{ t[5] }}</span></td>
          </tr>
          {% else %}
          <tr><td colspan="6" style="text-align: center; color: var(--muted); padding: 2rem;">პედაგოგები ვერ მოიძებნა</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- Modal Add Teacher -->
    <div id="addTeacherModal" style="display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 99; align-items: center; justify-content: center;">
      <div style="background: white; padding: 1.5rem; border-radius: 16px; width: min(100%, 480px);">
        <h3>+ ახალი პედაგოგის დამატება</h3>
        <form action="{{ url_for('add_teacher_route') }}" method="POST">
          <div class="form-group">
            <label>სრული სახელი და გვარი *</label>
            <input type="text" name="full_name" required class="form-control">
          </div>
          <div class="form-group">
            <label>ელ-ფოსტა *</label>
            <input type="email" name="email" required class="form-control">
          </div>
          <div class="form-group">
            <label>ტელეფონი</label>
            <input type="text" name="phone" class="form-control">
          </div>
          <div class="form-group">
            <label>სპეციალიზაცია</label>
            <input type="text" name="specialization" placeholder="Python, Languages, Math..." class="form-control">
          </div>
          <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
            <button type="button" onclick="document.getElementById('addTeacherModal').style.display='none'" class="btn btn-secondary">გაუქმება</button>
            <button type="submit" class="btn">დამატება</button>
          </div>
        </form>
      </div>
    </div>
    """,
    active_page="teachers"
)

# Legacy alias export for backward compatibility
HTML = DASHBOARD_HTML
COURSE_DETAIL_HTML = COURSES_HTML
DETAIL_HTML = STUDENT_DETAIL_HTML
EDIT_HTML = render_page(
    "სტუდენტის რედაქტირება",
    """
    <div class="card" style="max-width: 760px; margin-inline: auto;">
      <div class="card-header">
        <h3 class="card-title">✏️ სტუდენტის რედაქტირება</h3>
        <a href="{{ url_for('students_page') }}" class="btn btn-sm btn-outline">← უკან</a>
      </div>
      <form method="POST">
        <div class="grid-2">
          <div class="form-group">
            <label>სრული სახელი და გვარი *</label>
            <input class="form-control" name="name" value="{{ student[1] }}" required>
          </div>
          <div class="form-group">
            <label>ელ-ფოსტა *</label>
            <input class="form-control" type="email" name="email" value="{{ student[2] }}" required>
          </div>
          <div class="form-group">
            <label>ტელეფონი</label>
            <input class="form-control" name="phone" value="{{ student[3] or '' }}">
          </div>
          <div class="form-group">
            <label>მშობელი / მეთვალყურე</label>
            <input class="form-control" name="guardian_name" value="{{ student[4] or '' }}">
          </div>
          <div class="form-group">
            <label>მშობლის ტელეფონი</label>
            <input class="form-control" name="guardian_phone" value="{{ student[5] or '' }}">
          </div>
          <div class="form-group">
            <label>სტატუსი</label>
            <select class="form-control" name="status">
              <option value="active" {% if student[6] == 'active' %}selected{% endif %}>Active</option>
              <option value="inactive" {% if student[6] == 'inactive' %}selected{% endif %}>Inactive</option>
              <option value="archived" {% if student[6] == 'archived' %}selected{% endif %}>Archived</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>შენიშვნა</label>
          <textarea class="form-control" name="notes" rows="3">{{ student[7] or '' }}</textarea>
        </div>
        <div class="header-actions">
          <a href="{{ url_for('students_page') }}" class="btn btn-secondary">გაუქმება</a>
          <button type="submit" class="btn">ცვლილებების შენახვა</button>
        </div>
      </form>
    </div>
    """,
    active_page="students",
)
