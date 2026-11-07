from nicegui import ui

from hebrewenglish.gui.model import Attestation, ResolvedForm

from .elements import caption


def attestation_badge(status: Attestation, label: str = "") -> ui.badge:
    attested = status is Attestation.ATTESTED
    return ui.badge(
        label or ("Attested" if attested else "Not attested"),
        color="primary" if attested else "grey-7",
    ).props("outline")


def attestation_legend() -> None:
    with ui.row().classes("items-center gap-2").props('aria-label="Attestation legend"'):
        caption("Key")
        attestation_badge(Attestation.ATTESTED, "Biblical attestation")
        attestation_badge(Attestation.UNATTESTED, "Unattested / reconstructed")


def reference_list(resolved: ResolvedForm) -> None:
    if resolved.attestation is Attestation.UNATTESTED or not resolved.references:
        caption("No matching biblical attestations")
        return
    ui.label(" · ".join(resolved.references)).classes("text-caption text-primary")
