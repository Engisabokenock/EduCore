"""Text helpers."""
import re
import secrets
import unicodedata


def slugify(value: str, max_length: int = 150) -> str:
    """ASCII, lowercase, hyphen-separated slug (e.g. "CRE / IRE" -> "cre-ire")."""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return (slug or secrets.token_hex(4))[:max_length].strip("-")


def escape_like(term: str) -> str:
    """Escape LIKE wildcards so user input such as "100%" is matched literally."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
