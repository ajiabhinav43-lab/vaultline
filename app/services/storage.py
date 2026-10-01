"""
Storage service — abstracts *where* a document's bytes physically live.

Two backends:
  'local'    — writes to STORAGE_ROOT/user_<id>/<stored_filename> on disk.
               Fine for local development; NOT persistent on most free
               hosting platforms (Render's free disk is ephemeral).
  'supabase' — uploads to a Supabase Storage bucket. This is what
               production should use so files survive redeploys/restarts.

create_app() decides the active backend once, based on whether
SUPABASE_URL and SUPABASE_KEY are set, and stores it on app.config
as STORAGE_BACKEND. Every Document row also remembers which backend it
was saved under (Document.storage_backend), so switching backends later
doesn't break documents uploaded before the switch.
"""
import os

from flask import current_app


def _local_dir(user_id: int) -> str:
    path = os.path.join(current_app.config["STORAGE_ROOT"], f"user_{user_id}")
    os.makedirs(path, exist_ok=True)
    return path


def _get_supabase_client():
    from supabase import create_client
    url = current_app.config["SUPABASE_URL"]
    key = current_app.config["SUPABASE_KEY"]
    return create_client(url, key)


def save_file(user_id: int, stored_filename: str, file_storage) -> tuple[str, str]:
    """Saves an uploaded file. Returns (storage_path, backend)."""
    backend = current_app.config["STORAGE_BACKEND"]

    if backend == "supabase":
        object_key = f"user_{user_id}/{stored_filename}"
        file_storage.stream.seek(0)
        file_bytes = file_storage.stream.read()
        client = _get_supabase_client()
        bucket = current_app.config["SUPABASE_BUCKET"]
        client.storage.from_(bucket).upload(
            object_key, file_bytes,
            {"content-type": file_storage.mimetype or "application/octet-stream"},
        )
        return object_key, "supabase"

    # local backend
    dest_dir = _local_dir(user_id)
    dest_path = os.path.join(dest_dir, stored_filename)
    file_storage.save(dest_path)
    return dest_path, "local"


def get_file_size(storage_path: str, backend: str) -> int:
    if backend == "local":
        return os.path.getsize(storage_path)
    # For supabase, size is captured from the upload stream before saving
    # (see routes/documents.py) since the API doesn't return it directly.
    return 0


def read_file_bytes(document) -> bytes:
    """Fetches the raw bytes of a document regardless of backend."""
    if document.storage_backend == "supabase":
        client = _get_supabase_client()
        bucket = current_app.config["SUPABASE_BUCKET"]
        return client.storage.from_(bucket).download(document.storage_path)

    with open(document.storage_path, "rb") as f:
        return f.read()


def delete_file(document) -> None:
    if document.storage_backend == "supabase":
        client = _get_supabase_client()
        bucket = current_app.config["SUPABASE_BUCKET"]
        client.storage.from_(bucket).remove([document.storage_path])
        return

    if os.path.exists(document.storage_path):
        os.remove(document.storage_path)
