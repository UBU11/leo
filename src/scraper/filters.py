import re
from typing import Set

# ponytail: simple regex filters for stripping noisy tokens without pulling in heavy DOM parsing libraries
RE_SCRIPT_STYLE = re.compile(r"<(script|style|svg|noscript|header|footer|nav)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
RE_BASE64_DATA = re.compile(r"data:image/[^;]+;base64,[a-zA-Z0-9+/=]+", re.IGNORECASE)
RE_HTML_TAGS = re.compile(r"<[^>]+>")
RE_MULTI_WHITESPACE = re.compile(r"[ \t]+")
RE_MULTI_NEWLINES = re.compile(r"\n{3,}")

ECOMMERCE_TARGET_SELECTORS: Set[str] = {
    ".product-single__description",
    ".product__description",
    "main",
    "#main-content",
    ".product-description",
}


def prune_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    cleaned = RE_SCRIPT_STYLE.sub(" ", raw_html)
    cleaned = RE_BASE64_DATA.sub("", cleaned)
    return cleaned


def clean_markdown_or_text(raw_text: str, max_chars: int = 8000) -> str:
    if not raw_text:
        return ""
    text = RE_BASE64_DATA.sub("", raw_text)
    text = RE_MULTI_WHITESPACE.sub(" ", text)
    # ponytail: normalize 3+ newlines down to double newline for paragraph spacing
    text = re.sub(r"\n[ \t]*\n+", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(lines)
    cleaned = RE_MULTI_NEWLINES.sub("\n\n", cleaned)
    return cleaned[:max_chars].strip()

