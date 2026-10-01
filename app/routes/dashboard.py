from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Document, Share

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def index():
    my_documents = (Document.query
                     .filter_by(owner_id=current_user.id, is_deleted=False)
                     .order_by(Document.created_at.desc())
                     .all())
    shared_with_me = (Share.query
                       .filter_by(shared_with_id=current_user.id, revoked_at=None)
                       .order_by(Share.created_at.desc())
                       .all())
    shared_with_me = [s for s in shared_with_me if s.is_active()]

    stats = {
        "total_docs": len(my_documents),
        "total_shares_out": Share.query.filter_by(owner_id=current_user.id).count(),
        "total_shares_in": len(shared_with_me),
        "storage_used": sum(d.file_size for d in my_documents),
    }
    return render_template("dashboard.html", documents=my_documents,
                            shared_with_me=shared_with_me, stats=stats)
