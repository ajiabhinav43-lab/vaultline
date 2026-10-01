from flask import request

from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(action: str, user_id=None, document_id=None, result="SUCCESS", details=None):
    entry = AuditLog(
        user_id=user_id,
        document_id=document_id,
        action=action,
        ip_address=request.remote_addr if request else None,
        result=result,
        details=details,
    )
    db.session.add(entry)
    db.session.commit()
