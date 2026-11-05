from hebrewenglish.gui.model import Attestation, ResolvedForm
from hebrewenglish.gui.theme import PRIMARY_DARK
from .elements import box, text

_ATTESTED_DOT = "bg-primary"
_UNATTESTED_DOT = "border border-[#8d897f]"


def _dot(classes: str) -> None:
    box(f"block h-2 w-2 shrink-0 rounded-full {classes}", tag="span")


def attestation_mark(status: Attestation, compact: bool = False) -> None:
    attested = status is Attestation.ATTESTED
    size = "text-[10px] uppercase tracking-[0.1em]" if compact else "text-[11px]"
    colour = "text-[#405f73]" if attested else "text-[#807d74]"
    with box(f"inline-flex items-center gap-1.5 font-semibold {size} {colour}", tag="span"):
        _dot(_ATTESTED_DOT if attested else _UNATTESTED_DOT)
        text("Attested" if attested else "Not attested", tag="span")


def attestation_legend() -> None:
    with box("flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-[#6b7280]").props(
        'aria-label="Attestation legend"'
    ):
        text("Key", "font-semibold uppercase tracking-[0.12em] text-[#494b49]", "span")
        for dot, label in [(_ATTESTED_DOT, "Biblical attestation"), (_UNATTESTED_DOT, "Unattested / reconstructed")]:
            with box("inline-flex items-center gap-1.5", tag="span"):
                _dot(dot)
                text(label, tag="span")


def reference_list(resolved: ResolvedForm) -> None:
    if resolved.attestation is Attestation.UNATTESTED or not resolved.references:
        text("No matching biblical attestations", "mt-2 text-[10px] font-medium text-[#858585]", "p")
        return
    with box(f"ng-references mt-2 flex flex-wrap gap-x-2 gap-y-1 text-[10px] leading-4 text-[{PRIMARY_DARK}]", "ul"):
        for reference in resolved.references:
            text(reference, tag="li")
