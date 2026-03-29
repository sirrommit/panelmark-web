"""Tests for panelmark_web.page.prepare_page."""

from panelmark_web.page import prepare_page

SAMPLE_HTML = """\
<!DOCTYPE html>
<html>
<body>
<div class="pm-shell" data-pm-shell>content</div>
</body>
</html>"""

SAMPLE_HTML_NO_BODY = '<div class="pm-shell" data-pm-shell>content</div>'


def test_injects_ws_url_attribute():
    out = prepare_page(SAMPLE_HTML)
    assert 'data-pm-ws-url="/ws"' in out


def test_custom_ws_url():
    out = prepare_page(SAMPLE_HTML, ws_url="/api/ws")
    assert 'data-pm-ws-url="/api/ws"' in out


def test_absolute_ws_url():
    out = prepare_page(SAMPLE_HTML, ws_url="wss://example.com/ws")
    assert 'data-pm-ws-url="wss://example.com/ws"' in out


def test_ws_url_on_shell_root_not_duplicated():
    out = prepare_page(SAMPLE_HTML, ws_url="/ws")
    assert out.count("data-pm-ws-url") == 1


def test_data_pm_shell_still_present():
    out = prepare_page(SAMPLE_HTML)
    assert "data-pm-shell" in out


def test_injects_script_tag():
    out = prepare_page(SAMPLE_HTML)
    assert '<script src="/static/client.js"></script>' in out


def test_custom_script_src():
    out = prepare_page(SAMPLE_HTML, script_src="/assets/pm-client.js")
    assert '<script src="/assets/pm-client.js"></script>' in out


def test_script_before_body_close():
    out = prepare_page(SAMPLE_HTML)
    script_pos = out.index("<script")
    body_close_pos = out.index("</body>")
    assert script_pos < body_close_pos


def test_no_body_tag_appends_script():
    out = prepare_page(SAMPLE_HTML_NO_BODY)
    assert "<script" in out


def test_ws_url_special_chars_escaped():
    out = prepare_page(SAMPLE_HTML, ws_url='/ws?key="value"')
    assert '"' not in out.split('data-pm-ws-url=')[1].split('>')[0].strip('"')


def test_idempotent_script_injection_position():
    """Script tag appears exactly once."""
    out = prepare_page(SAMPLE_HTML)
    assert out.count("<script") == 1
