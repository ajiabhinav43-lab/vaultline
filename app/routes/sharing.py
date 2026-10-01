import io
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort, send_file
from flask_login import login_required, current_user

from app.extensions import db
from app.forms import ShareForm
from app.models import Document, Share, User
from app.services.sharing import parse_expiry
from app.services.audit import log_action
from app.services import storage

bp = Blueprint("sharing", __name__)


@bp.route("/share/<int:doc_id>", methods=["GET", "POST"])
@login_required
def share_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.owner_id != current_user.id:
        abort(403)

    form = ShareForm()
    if form.validate_on_submit():
        recipient = User.query.filter_by(email=form.recipient_email.data.lower().strip()).first()

        if recipient.id == current_user.id:
            flash("You can't share a document with yourself.", "warning")
            return render_template("share_form.html", form=form, document=doc)

        existing = Share.query.filter_by(
            document_id=doc.id, shared_with_id=recipient.id, revoked_at=None
        ).first()
        if existing and existing.is_active():
            flash(f"Already shared with {recipient.email}. Revoke the existing share first to change it.", "warning")
            return redirect(url_for("dashboard.index"))

        share = Share(
            document_id=doc.id,
            owner_id=current_user.id,
            shared_with_id=recipient.id,
            permission=form.permission.data,
            expires_at=parse_expiry(form.expires_in.data),
        )
        db.session.add(share)
        db.session.commit()
        log_action("SHARE", user_id=current_user.id, document_id=doc.id,
                    details=f"shared with {recipient.email} ({share.permission})")
        flash(f"'{doc.original_filename}' shared with {recipient.email}.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("share_form.html", form=form, document=doc)


@bp.route("/shares/revoke/<int:share_id>", methods=["POST"])
@login_required
def revoke(share_id):
    share = Share.query.get_or_404(share_id)
    if share.owner_id != current_user.id:
        abort(403)
    share.revoked_at = datetime.utcnow()
    db.session.commit()
    log_action("REVOKE", user_id=current_user.id, document_id=share.document_id,
                details=f"revoked share with {share.shared_with.email}")
    flash("Share access revoked.", "info")
    return redirect(url_for("dashboard.index"))


@bp.route("/shares")
@login_required
def my_shares():
    """Every share the current user has given out, across all their documents."""
    all_shares = (Share.query.filter_by(owner_id=current_user.id)
                  .order_by(Share.created_at.desc()).all())
    return render_template("shares.html", shares=all_shares, document=None)


@bp.route("/documents/<int:doc_id>/shares")
@login_required
def manage_shares(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.owner_id != current_user.id:
        abort(403)
    all_shares = Share.query.filter_by(document_id=doc.id).order_by(Share.created_at.desc()).all()
    return render_template("shares.html", shares=all_shares, document=doc)


@bp.route("/s/<token>")
def access_by_token(token):
    """Public entry point for an expiring share link — no login required."""
    share = Share.query.filter_by(token=token).first()
    if not share or not share.is_active():
        log_action("VIEW", result="FAILURE", details="invalid/expired share token")
        abort(404)

    doc = Document.query.get_or_404(share.document_id)
    log_action("VIEW", document_id=doc.id, details="accessed via share token")
    data = storage.read_file_bytes(doc)
    return send_file(io.BytesIO(data), mimetype=doc.mime_type,
                      as_attachment=False, download_name=doc.original_filename)
