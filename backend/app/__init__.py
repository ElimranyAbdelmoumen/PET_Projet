import os
import psycopg2
from flask import Flask

from app.routes.auth import bp as auth_bp
from app.routes.submissions import bp as submissions_bp
from app.routes.admin import bp as admin_bp
from app.routes.web import bp as web_bp



def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

    # --- Blueprints / Routes ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(web_bp)
    # --- Health check ---
    @app.get("/health")
    def health():
        db_ok = False
        err = None
        try:
            conn = psycopg2.connect(os.environ["DATABASE_URL"])
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            cur.fetchone()
            cur.close()
            conn.close()
            db_ok = True
        except Exception as e:
            err = str(e)

        return {"status": "ok", "db": db_ok, "db_error": err}

    return app