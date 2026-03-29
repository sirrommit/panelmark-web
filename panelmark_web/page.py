"""Helper for preparing a panelmark-html page for use with panelmark-web."""

import re


def prepare_page(
    html: str,
    *,
    ws_url: str = "/ws",
    script_src: str = "/static/client.js",
) -> str:
    """Inject panelmark-web runtime hooks into a rendered panelmark-html page.

    Performs two modifications to ``html``:

    1. Adds ``data-pm-ws-url`` to the shell root element (``[data-pm-shell]``)
       so that ``client.js`` knows which WebSocket endpoint to connect to.
    2. Injects ``<script src="...">`` before ``</body>``.

    Parameters
    ----------
    html:
        The HTML string returned by ``panelmark_html.render_document()``.
    ws_url:
        WebSocket path or absolute URL.  Relative paths (e.g. ``"/ws"``) are
        resolved against the current page host by the browser client.  Absolute
        ``ws://`` / ``wss://`` URLs are used as-is.  Defaults to ``"/ws"``.
    script_src:
        URL of the ``client.js`` script to inject.  Defaults to
        ``"/static/client.js"``.

    Returns
    -------
    str
        Modified HTML ready to serve.

    Example
    -------
    ::

        from panelmark_html import render_document
        from panelmark_web.page import prepare_page

        html = render_document(shell)
        html = prepare_page(html, ws_url="/ws", script_src="/static/client.js")
    """
    # 1. Inject data-pm-ws-url on the shell root.
    #    The stable hook is the boolean attribute data-pm-shell (no value).
    #    We insert the new attribute immediately after it.
    ws_url_escaped = ws_url.replace('"', "&quot;")
    html = re.sub(
        r'\bdata-pm-shell\b',
        f'data-pm-shell data-pm-ws-url="{ws_url_escaped}"',
        html,
        count=1,
    )

    # 2. Inject the script tag before </body>.
    script_tag = f'<script src="{script_src}"></script>'
    if "</body>" in html:
        html = html.replace("</body>", script_tag + "\n</body>", 1)
    else:
        html = html + "\n" + script_tag

    return html
