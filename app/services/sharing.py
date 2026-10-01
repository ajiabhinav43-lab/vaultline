from datetime import datetime, timedelta

from app.models.share import Share

_EXPIRY_MAP = {
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def parse_expiry(code: str):
    if code == "never":
        return None
    delta = _EXPIRY_MAP.get(code)
    return datetime.utcnow() + delta if delta else None


def can_access(document, user, action: str) -> bool:
    """action: 'view' | 'download' | 'manage'"""
    if document.owner_id == user.id:
        return True

    share = Share.query.filter_by(document_id=document.id, shared_with_id=user.id).first()
    if not share or not share.is_active():
        return False

    if action == "view":
        return True
    if action == "download":
        return share.permission == "DOWNLOAD"
    return False  # only the owner can 'manage' (delete / share / revoke)
