import os

from flask import Flask, render_template, redirect, url_for
from flask_login import current_user
from dotenv import load_dotenv

from config import config_by_name
from app.extensions import db, migrate, login_manager, bcrypt, csrf, limiter
from app.utils.security import apply_security_headers

load_dotenv()


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    # --- Decide storage backend once, at startup ---
    # 'supabase' if credentials are present, else 'local' for zero-setup dev.
    if app.config.get("SUPABASE_URL") and app.config.get("SUPABASE_KEY"):
        app.config["STORAGE_BACKEND"] = "supabase"
    else:
        app.config["STORAGE_BACKEND"] = "local"
        os.makedirs(app.config["STORAGE_ROOT"], exist_ok=True)
        os.makedirs(app.config["QUARANTINE_ROOT"], exist_ok=True)

    os.makedirs(app.instance_path, exist_ok=True)

    # --- Init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Register blueprints ---
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.documents import bp as documents_bp
    from app.routes.sharing import bp as sharing_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(sharing_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    # --- Error handlers ---
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413

    app.after_request(apply_security_headers)

    # --- Auto-create tables + default admin in dev/testing only.
    # In production, use `flask db upgrade` (see README) instead of
    # create_all(), so schema changes go through real migrations.
    if config_name in ("development", "testing"):
        with app.app_context():
            db.create_all()
            _create_default_admin(app)

    @app.cli.command("seed-admin")
    def seed_admin_command():
        """Creates the default admin account. Run once after `flask db upgrade`
        in production: `flask seed-admin`"""
        _create_default_admin(app)
        print("Done.")

    return app


def _create_default_admin(app):
    from app.models import User

    if User.query.filter_by(role="admin").first():
        return

    admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")

    admin = User(name="Administrator", email=admin_email, role="admin")
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()
    app.logger.info(f"Created default admin account: {admin_email} / {admin_password}")
