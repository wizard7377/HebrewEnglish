"""Colours and stylesheet for the Davar page, taken from the Figma Make prototype's theme."""

from nicegui import ui

PRIMARY = "#5898d4"
PRIMARY_DARK = "#3f7fbc"
PAGE = "#f5f5f5"
HERO = "#eef4fa"
BORDER = "#dedede"
MUTED = "#6b7280"
INFLECTION = "#2878b5"
SUFFIX = "#c43d3d"

# Shared Tailwind class strings for small-caps section headings
SECTION_LABEL = f"text-[11px] font-bold uppercase tracking-[0.08em] text-[{PRIMARY_DARK}]"
COLUMN_LABEL = "text-[10px] font-bold uppercase tracking-[0.12em]"

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Noto+Serif+Hebrew:wght@400;500&display=swap">'
)

# Only what Tailwind utilities cannot express; NiceGUI's own layout CSS is unlayered, so it outranks Tailwind
_CSS = f"""
.hebrew-text {{
  font-family: "SBL Hebrew", "Noto Serif Hebrew", serif;
  font-feature-settings: "kern" 1, "mark" 1, "mkmk" 1;
  text-rendering: optimizeLegibility;
  unicode-bidi: isolate;
}}
.morph-inflection {{ color: {INFLECTION}; }}
.morph-object-suffix {{ color: {SUFFIX}; }}

.unattested-row, .unattested-sticky {{
  background-color: #f1f1f1;
  background-image: repeating-linear-gradient(-45deg, transparent, transparent 8px, rgb(0 0 0 / 2.4%) 8px 9px);
}}
.ng-references li:not(:last-child)::after {{ content: "·"; margin-left: .5rem; color: #b0b0b0; }}

.ng-table th, .ng-table td {{ border-color: #e0e0e0; }}
.ng-table tbody tr:not(.unattested-row):hover,
.ng-table tbody tr:not(.unattested-row):hover > th {{ background: #f5f9fc; }}
.ng-person-cell {{ box-shadow: 1px 0 #e0e0e0; }}
.ng-merged-cell {{ background-color: #fbfdff; }}

.table-scroll {{ scrollbar-color: #9e9e9e #eee; scrollbar-width: thin; }}
.table-scroll::-webkit-scrollbar {{ height: 9px; }}
.table-scroll::-webkit-scrollbar-track {{ background: #eee; }}
.table-scroll::-webkit-scrollbar-thumb {{ background: #9e9e9e; border: 2px solid #eee; border-radius: 999px; }}

.ng-expansion {{ border: 1px solid {BORDER}; border-radius: 4px; background: #fff; box-shadow: 0 1px 3px #00000029; }}
.ng-expansion:hover {{ box-shadow: 0 2px 4px -1px #0003, 0 4px 5px #00000024; }}
.ng-expansion .q-expansion-item__container > .q-item {{ min-height: 88px; padding: 20px 28px; }}
.ng-expansion .nicegui-expansion-content {{ padding: 0; gap: 0; }}
@media (max-width: 639px) {{
  .ng-expansion .q-expansion-item__container > .q-item {{ padding: 20px; }}
}}

.ng-tabs .q-tab {{ min-height: 44px; padding: 0 16px; color: #616161; letter-spacing: .04em; }}
.ng-tabs .q-tab--active {{ color: {PRIMARY_DARK}; background: rgb(88 152 212 / 8%); }}

.ng-toggle .q-toggle__label {{ padding-left: 4px; }}
"""


def apply_theme() -> None:
    """Install the Davar colours, fonts and stylesheet on the current page."""
    ui.colors(primary=PRIMARY)
    ui.add_head_html(_FONTS)
    ui.add_css(_CSS)
    ui.query("body").style(f"background-color: {PAGE}; color: #1d1d1d")
    # Full-bleed sections: drop NiceGUI's default page padding and gap
    ui.query(".nicegui-content").style("padding: 0; gap: 0")
