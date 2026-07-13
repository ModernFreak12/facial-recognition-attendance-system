"""
Shared theme constants for a modern, premium-looking Kivy UI.

All screens and widgets pull colors/fonts/spacing from here so that
the whole app stays visually consistent. Actual widget-building logic
(rounded buttons, cards, inputs) now lives in app/ui/widgets/ so it is
written once and reused everywhere instead of being copy-pasted into
every screen.
"""
from kivy.utils import get_color_from_hex


# ───────────────────────────────────────────────────
# COLOR PALETTE  (dark theme, vibrant accents)
# ───────────────────────────────────────────────────
BG_DARK       = get_color_from_hex("#111120")
BG_CARD       = get_color_from_hex("#1A1A2E")
BG_CARD_ALT   = get_color_from_hex("#20203A")   # slightly lighter, for nested cards
BG_INPUT      = get_color_from_hex("#16213E")

PRIMARY       = get_color_from_hex("#6C63FF")    # Vibrant indigo (teacher accent)
PRIMARY_LIGHT = get_color_from_hex("#8B83FF")
SECONDARY     = get_color_from_hex("#00D2FF")    # Cyan accent (student accent)
SECONDARY_LIGHT = get_color_from_hex("#5CE1FF")

ACCENT_GREEN  = get_color_from_hex("#00E676")    # Present
ACCENT_ORANGE = get_color_from_hex("#FFAB40")    # Late
ACCENT_RED    = get_color_from_hex("#FF5252")    # Absent
ACCENT_GREY   = get_color_from_hex("#3A3A55")    # No session / empty day

TEXT_WHITE     = get_color_from_hex("#F0F0F5")
TEXT_MUTED     = get_color_from_hex("#8888AA")
TEXT_DARK      = get_color_from_hex("#111120")

BORDER_SUBTLE = get_color_from_hex("#2A2A4A")


# ───────────────────────────────────────────────────
# ATTENDANCE STATUS → COLOR  (single source of truth)
# ───────────────────────────────────────────────────
STATUS_COLORS = {
    "PRESENT": ACCENT_GREEN,
    "LATE":    ACCENT_ORANGE,
    "ABSENT":  ACCENT_RED,
    "NONE":    ACCENT_GREY,   # no session that day / not yet marked
}

STATUS_MARKUP = {
    "PRESENT": "[color=00E676]",
    "LATE":    "[color=FFAB40]",
    "ABSENT":  "[color=FF5252]",
    "NONE":    "[color=8888AA]",
}


def status_color(status: str):
    return STATUS_COLORS.get((status or "NONE").upper(), ACCENT_GREY)


def status_markup(status: str):
    return STATUS_MARKUP.get((status or "NONE").upper(), STATUS_MARKUP["NONE"])


# ───────────────────────────────────────────────────
# TYPOGRAPHY
# ───────────────────────────────────────────────────
FONT_SIZE_TITLE    = 28
FONT_SIZE_SUBTITLE = 18
FONT_SIZE_BODY     = 15
FONT_SIZE_BUTTON   = 16
FONT_SIZE_SMALL    = 13
FONT_SIZE_TINY     = 11


# ───────────────────────────────────────────────────
# SPACING / RADII  (kept consistent across all cards & buttons)
# ───────────────────────────────────────────────────
RADIUS_CARD   = 16
RADIUS_BUTTON = 14
RADIUS_CHIP   = 10
CARD_PADDING  = [20, 16, 20, 16]
