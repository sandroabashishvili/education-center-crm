"""Development web entrypoint. Desktop imports the side-effect-free factory."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database
from app_factory import create_app, date_de, datetime_de, status_de

DB_PATH = Path(os.environ.get("CRM_DB_PATH", database.DB_PATH))
app = create_app({"DB_PATH": DB_PATH, "DEMO_MODE": os.environ.get("CRM_DEMO_MODE", "1") == "1"})

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5001")))
