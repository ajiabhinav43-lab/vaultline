from datetime import datetime

from app.extensions import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(120), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False)  # sha256
    storage_path = db.Column(db.String(500), nullable=False)
    # 'local' (storage/ on disk) or 'supabase' (Supabase Storage bucket).
    # Lets the same table serve documents saved before and after switching backends.
    storage_backend = db.Column(db.String(20), nullable=False, default="local")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    shares = db.relationship("Share", backref="document", lazy="dynamic",
                              cascade="all, delete-orphan")

    def human_size(self) -> str:
        size = self.file_size
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
