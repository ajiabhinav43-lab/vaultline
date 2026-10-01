from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, Document, AuditLog, Share

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@bp.route("/")
@bp.route("/dashboard")
@login_required
@admin_required
def index():
    stats = {
        "total_users": User.query.count(),
        "total_documents": Document.query.filter_by(is_deleted=False).count(),
        "total_shares": Share.query.count(),
        "total_events": AuditLog.query.count(),
        "recent_logs": AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user(user_id):
    from app.services.audit import log_action
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You can't disable your own account.", "warning")
        return redirect(url_for("admin.users"))
    user.is_active_flag = not user.is_active_flag
    db.session.commit()
    log_action("ACCOUNT_TOGGLE", user_id=current_user.id, details=f"{user.email} -> active={user.is_active_flag}")
    flash(f"{user.email} is now {'active' if user.is_active_flag else 'disabled'}.", "info")
    return redirect(url_for("admin.users"))


@bp.route("/documents")
@login_required
@admin_required
def documents():
    docs = Document.query.filter_by(is_deleted=False).order_by(Document.created_at.desc()).all()
    return render_template("admin/documents.html", documents=docs)


@bp.route("/logs")
@login_required
@admin_required
def logs():
    all_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    return render_template("admin/logs.html", logs=all_logs)
