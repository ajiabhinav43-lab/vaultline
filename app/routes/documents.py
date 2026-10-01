import io

from flask import (Blueprint, render_template, redirect, url_for, flash,
                    abort, request, send_file)
from flask_login import login_required, current_user

from app.extensions import db
from app.forms import UploadForm
from app.models import Document, AuditLog
from app.services import storage
from app.services.hashing import calculate_sha256
from app.services.sharing import can_access
from app.services.audit import log_action
from app.utils.validators import validate_upload, generate_safe_filename, get_extension, MIME_MAP

bp = Blueprint("documents", __name__)


@bp.route("/documents/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        ok, error = validate_upload(file)
        if not ok:
            flash(error, "danger")
            return render_template("upload.html", form=form)

        stored_filename = generate_safe_filename(file.filename)
        file_hash = calculate_sha256(file.stream)

        # Measure size before the stream gets consumed by save_file()
        file.stream.seek(0, 2)
        file_size = file.stream.tell()
        file.stream.seek(0)

        storage_path, backend = storage.save_file(current_user.id, stored_filename, file)

        ext = get_extension(file.filename)
        doc = Document(
            owner_id=current_user.id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_size=file_size,
            mime_type=MIME_MAP.get(ext, "application/octet-stream"),
            file_hash=file_hash,
            storage_path=storage_path,
            storage_backend=backend,
        )
        db.session.add(doc)
        db.session.commit()
        log_action("UPLOAD", user_id=current_user.id, document_id=doc.id,
                    details=doc.original_filename)
        flash(f"'{doc.original_filename}' uploaded successfully.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("upload.html", form=form)


@bp.route("/documents/view/<int:doc_id>")
@login_required
def view(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not can_access(doc, current_user, "view"):
        log_action("VIEW", user_id=current_user.id, document_id=doc.id, result="FAILURE")
        abort(403)
    log_action("VIEW", user_id=current_user.id, document_id=doc.id)
    can_download = can_access(doc, current_user, "download")
    is_owner = doc.owner_id == current_user.id
    return render_template("document_view.html", document=doc,
                            can_download=can_download, is_owner=is_owner)


@bp.route("/documents/raw/<int:doc_id>")
@login_required
def raw(doc_id):
    """Streams the actual file bytes for inline viewing (opened from document_view.html)."""
    doc = Document.query.get_or_404(doc_id)
    if not can_access(doc, current_user, "view"):
        abort(403)
    data = storage.read_file_bytes(doc)
    return send_file(io.BytesIO(data), mimetype=doc.mime_type,
                      as_attachment=False, download_name=doc.original_filename)


@bp.route("/documents/download/<int:doc_id>")
@login_required
def download(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if not can_access(doc, current_user, "download"):
        log_action("DOWNLOAD", user_id=current_user.id, document_id=doc.id, result="FAILURE")
        abort(403)
    log_action("DOWNLOAD", user_id=current_user.id, document_id=doc.id)
    data = storage.read_file_bytes(doc)
    return send_file(io.BytesIO(data), mimetype=doc.mime_type,
                      as_attachment=True, download_name=doc.original_filename)


@bp.route("/documents/delete/<int:doc_id>", methods=["POST"])
@login_required
def delete(doc_id):
    doc = Document.query.get_or_404(doc_id)
    if doc.owner_id != current_user.id:
        abort(403)
    doc.is_deleted = True
    db.session.commit()
    log_action("DELETE", user_id=current_user.id, document_id=doc.id,
                details=doc.original_filename)
    flash(f"'{doc.original_filename}' deleted.", "info")
    return redirect(url_for("dashboard.index"))


@bp.route("/activity")
@login_required
def my_activity():
    logs = (AuditLog.query.filter_by(user_id=current_user.id)
            .order_by(AuditLog.timestamp.desc()).limit(200).all())
    return render_template("activity.html", logs=logs)
