import secrets
from datetime import datetime

from app.extensions import db


class Share(db.Model):
    __tablename__ = "shares"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    shared_with_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    permission = db.Column(db.String(20), nullable=False, default="VIEW")  # VIEW | DOWNLOAD
    token = db.Column(db.String(64), unique=True, nullable=False,
                       default=lambda: secrets.token_urlsafe(32))
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)

    shared_with = db.relationship("User", foreign_keys=[shared_with_id])
    sharer = db.relationship("User", foreign_keys=[owner_id])

    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def status_label(self) -> str:
        if self.revoked_at:
            return "Revoked"
        if self.expires_at and self.expires_at < datetime.utcnow():
            return "Expired"
        return "Active"
