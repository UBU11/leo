from src.scraper.filters import clean_markdown_or_text, prune_html


def test_prune_html_strips_scripts_and_styles():
    raw = "<div>Hello <script>alert(1)</script><style>.a{color:red}</style>World</div>"
    cleaned = prune_html(raw)
    assert "<script>" not in cleaned
    assert "alert(1)" not in cleaned
    assert "World" in cleaned


def test_clean_markdown_or_text_collapses_whitespace():
    raw = "Line 1\n\n\n\nLine 2    extra   spaces"
    cleaned = clean_markdown_or_text(raw)
    assert "Line 1\n\nLine 2 extra spaces" == cleaned
