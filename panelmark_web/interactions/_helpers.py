"""Shared helpers for panelmark-web interactions."""


def scroll_offset(cursor: int | None, height: int, total: int) -> int:
    """Return the first-visible-row index that keeps *cursor* in the window.

    Uses a simple strategy: scroll just far enough that the cursor is visible,
    placing it at the bottom of the window when scrolling down.
    """
    if cursor is None or total == 0 or height <= 0:
        return 0
    return max(0, cursor - height + 1)
