import os
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

import database
from management_routes import register_management_routes
from profile_routes import register_profile_routes
from routes import register_routes


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = APP_DIR / "crm.db"

STATUS_LABELS_DE = {
    "active": "Aktiv", "inactive": "Inaktiv", "archived": "Archiviert",
    "planned": "Geplant", "scheduled": "Geplant", "completed": "Abgeschlossen",
    "cancelled": "Abgesagt", "enrolled": "Eingeschrieben", "paid": "Bezahlt",
    "partial": "Teilbezahlt", "pending": "Offen", "overdue": "Überfällig",
    "cash": "Bar", "card": "Karte", "transfer": "Überweisung",
    "bank_transfer": "Banküberweisung", "present": "Anwesend", "absent": "Abwesend",
    "late": "Verspätet", "excused": "Entschuldigt",
}


def status_de(value):
    text = str(value or "").strip()
    return STATUS_LABELS_DE.get(text.lower(), text)


def date_de(value):
    text = str(value or "").strip()
    if not text or text == "-": return "-"
    try: return datetime.fromisoformat(text[:10]).strftime("%d.%m.%Y")
    except ValueError: return text


def datetime_de(value):
    text = str(value or "").strip()
    if not text or text == "-": return "-"
    try: return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%d.%m.%Y, %H:%M")
    except ValueError: return text


app = Flask(__name__)
app.config.update(
    DB_PATH=Path(os.environ.get("CRM_DB_PATH", DEFAULT_DB_PATH)),
    SECRET_KEY=os.environ.get("CRM_SECRET_KEY", "local-demo-only-change-me"),
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
csrf = CSRFProtect(app)
app.jinja_env.filters["status_de"] = status_de
app.jinja_env.filters["date_de"] = date_de
app.jinja_env.filters["datetime_de"] = datetime_de


@app.route("/favicon.ico")
def favicon_ico():
    return redirect(url_for("static", filename="favicon.svg"), code=302)


@app.errorhandler(CSRFError)
def handle_csrf_error(_error):
    return render_template("error.html", status_code=400, title="Ungueltige Anfrage", message="Das Formular ist abgelaufen oder unvollstaendig. Bitte laden Sie die Seite neu."), 400


@app.errorhandler(403)
def handle_forbidden(_error):
    return render_template("error.html", status_code=403, title="Zugriff nicht erlaubt", message="Ihre Rolle ist fuer diese Aktion nicht berechtigt."), 403


DB_PATH = app.config["DB_PATH"]
database.DB_PATH = DB_PATH
database.init_db(DB_PATH)
register_routes(app)
register_management_routes(app)
register_profile_routes(app)


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5001")))
