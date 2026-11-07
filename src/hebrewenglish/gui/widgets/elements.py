from nicegui import ui


def heading(title: str) -> ui.label:
    """A small-caps section heading."""
    return ui.label(title).classes("text-overline text-primary")


def caption(value: str) -> ui.label:
    """Secondary text in a smaller, greyed type."""
    return ui.label(value).classes("text-caption text-grey-7")
