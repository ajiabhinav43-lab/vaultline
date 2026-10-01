import uuid

from flask import current_app
from werkzeug.utils import secure_filename

# A conservative allow-list of MIME types matched against extension.
# Defense-in-depth on top of the extension check — real hardening would
# add content sniffing / a library like python-magic, or ClamAV (see README).
MIME_MAP = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "txt": "text/plain",
}


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def allowed_file(filename: str) -> bool:
    ext = get_extension(filename)
    return bool(ext) and ext in current_app.config["ALLOWED_EXTENSIONS"]


def generate_safe_filename(original_filename: str) -> str:
    """Never trust the original filename for storage — generate an
    unguessable internal name and keep the extension only."""
    ext = get_extension(secure_filename(original_filename))
    return f"{uuid.uuid4().hex}.{ext}"


def validate_upload(file_storage):
    """Runs the upload workflow checks. Returns (ok, error_message)."""
    if file_storage is None or file_storage.filename == "":
        return False, "No file selected."

    if not allowed_file(file_storage.filename):
        return False, "File type not permitted."

    file_storage.stream.seek(0, 2)  # SEEK_END
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > current_app.config["MAX_CONTENT_LENGTH"]:
        return False, "File exceeds the 25 MB limit."
    if size == 0:
        return False, "File is empty."

    return True, None
