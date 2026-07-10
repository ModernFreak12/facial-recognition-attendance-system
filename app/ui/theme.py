"""
Shared theme constants and widget factory functions
for a modern, premium-looking Kivy UI.
"""
from kivy.utils import get_color_from_hex


# ───────────────────────────────────────────────────
# COLOR PALETTE  (dark theme, vibrant accents)
# ───────────────────────────────────────────────────
BG_DARK       = get_color_from_hex("#111120")
BG_CARD       = get_color_from_hex("#1A1A2E")
BG_INPUT      = get_color_from_hex("#16213E")

PRIMARY       = get_color_from_hex("#6C63FF")    # Vibrant indigo
PRIMARY_LIGHT = get_color_from_hex("#8B83FF")
SECONDARY     = get_color_from_hex("#00D2FF")    # Cyan accent
ACCENT_GREEN  = get_color_from_hex("#00E676")
ACCENT_RED    = get_color_from_hex("#FF5252")

TEXT_WHITE     = get_color_from_hex("#F0F0F5")
TEXT_MUTED     = get_color_from_hex("#8888AA")
TEXT_DARK      = get_color_from_hex("#111120")

BORDER_SUBTLE = get_color_from_hex("#2A2A4A")


# ───────────────────────────────────────────────────
# TYPOGRAPHY
# ───────────────────────────────────────────────────
FONT_SIZE_TITLE    = 28
FONT_SIZE_SUBTITLE = 18
FONT_SIZE_BODY     = 15
FONT_SIZE_BUTTON   = 16
FONT_SIZE_SMALL    = 13
