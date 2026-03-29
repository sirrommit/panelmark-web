"""DataclassForm — modal form widget driven by a dataclass instance."""

from panelmark_web.interactions.dataclass_form import DataclassFormInteraction


class DataclassForm(DataclassFormInteraction):
    """Thin widget wrapper around :class:`DataclassFormInteraction`.

    Use ``DataclassForm`` when a standalone form popup is preferred.
    Use :class:`~panelmark_web.interactions.DataclassFormInteraction` directly
    when embedding a form inside a larger multi-region shell.

    Adds Escape cancellation on top of the base interaction: pressing Escape
    fires ``signal_return()`` with ``(True, None)`` regardless of the action
    list.

    ``signal_return()`` → ``(True, action_result)`` when an action fires;
                          ``(True, None)`` on Escape/cancel;
                          ``(False, None)`` while still open.

    Parameters
    ----------
    dataclass_instance:
        An instance of a ``@dataclasses.dataclass`` class.
    title:
        Display title (informational; not rendered by the interaction
        itself — embed it in the panel heading or a sibling region).
    actions:
        Optional list of action dicts with ``"label"`` and ``"action"``
        keys.  ``"action"`` receives the current field-value dict and
        returns the shell exit value.
    on_change:
        Optional callback invoked with the current field-value dict after
        any field change.
    """

    def __init__(
        self,
        dataclass_instance,
        title: str = "Edit",
        actions=None,
        on_change=None,
    ) -> None:
        super().__init__(dataclass_instance, actions=actions, on_change=on_change)
        self.title = title
        self._df_cancelled = False

    def handle_key(self, key: str) -> tuple:
        if key == "\x1b":
            self._df_cancelled = True
            return True, None
        return super().handle_key(key)

    def signal_return(self) -> tuple:
        if self._df_cancelled:
            return True, None
        return super().signal_return()
