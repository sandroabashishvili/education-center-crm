import os
from pathlib import Path

from flask import Flask

import database
from routes import register_routes


APP_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = APP_DIR / "crm.db"

app = Flask(__name__)
app.config.update(
    DB_PATH=Path(os.environ.get("CRM_DB_PATH", DEFAULT_DB_PATH)),
    SECRET_KEY=os.environ.get("CRM_SECRET_KEY", "local-demo-only-change-me"),
)

DB_PATH = app.config["DB_PATH"]
database.DB_PATH = DB_PATH
database.init_db(DB_PATH)
register_routes(app)


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5001")),
    )
