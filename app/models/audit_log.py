from datetime import datetime

from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.String(20), nullable=False, default="SUCCESS")  # SUCCESS | FAILURE
    details = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])
