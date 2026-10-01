import re


def apply_security_headers(response):
    """Adds baseline security headers to every response. Called from an
    after_request hook in the app factory."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


def password_strength_ok(password: str) -> bool:
    """Minimum bar: 8+ characters. Extend here (uppercase/digit/symbol
    requirements) if your project rubric asks for stronger policy."""
    return bool(password) and len(password) >= 8


def looks_like_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value or ""))
