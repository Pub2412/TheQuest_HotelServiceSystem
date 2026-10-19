"""
Theme configuration for The Quest Hotel Management System.
Defines colors, fonts, system slogans, and status styling.
Theme: Royal Purple, Warm Gold/Yellow, and Crisp White.
"""

# Brand Identity
SYSTEM_NAME = "The Quest"
SYSTEM_SUBTITLE = "Hotel Management System"
SYSTEM_SLOGAN = "We shall never deny a guest, even the most ridiculous request"

# Core Color Palette: Purple, Yellow, White
COLOR_PRIMARY_DARK = "#23073D"     # Deep Royal Purple
COLOR_PRIMARY = "#3B185F"          # Rich Velvet Purple
COLOR_PRIMARY_LIGHT = "#581C87"    # Amethyst Purple
COLOR_PRIMARY_TINT = "#EDE9FE"     # Very soft purple tint

COLOR_ACCENT = "#F59E0B"           # Warm Gold / Amber Yellow
COLOR_ACCENT_HOVER = "#D97706"     # Deep Amber Gold
COLOR_ACCENT_LIGHT = "#FEF3C7"     # Champagne Yellow
COLOR_ACCENT_TEXT = "#78350F"      # Dark Amber for yellow backgrounds

COLOR_WHITE = "#FFFFFF"            # Crisp White
COLOR_BG = "#F8FAFC"               # Soft Off-White Surface
COLOR_CARD = "#FFFFFF"             # Card Background
COLOR_BORDER = "#E2E8F0"           # Subtle Divider
COLOR_BORDER_FOCUS = "#8B5CF6"     # Focus Ring Purple

# Semantic & Status Colors
COLOR_TEXT_DARK = "#0F172A"        # Deep Charcoal
COLOR_TEXT_NORMAL = "#1E293B"      # Dark Slate
COLOR_TEXT_MUTED = "#64748B"       # Muted Slate
COLOR_TEXT_LIGHT = "#94A3B8"       # Subdued Grey
COLOR_TEXT_WHITE = "#FFFFFF"

COLOR_SUCCESS = "#10B981"          # Emerald Green (Vacant / Complete)
COLOR_SUCCESS_BG = "#ECFDF5"
COLOR_SUCCESS_TEXT = "#065F46"

COLOR_DANGER = "#EF4444"           # Coral Red (Occupied / Overdue)
COLOR_DANGER_BG = "#FEF2F2"
COLOR_DANGER_TEXT = "#991B1B"

COLOR_WARNING = "#F59E0B"          # Gold Amber (Needs Service / Near Overdue)
COLOR_WARNING_BG = "#FFFBEB"
COLOR_WARNING_TEXT = "#92400E"

COLOR_INFO = "#3B82F6"             # Sapphire Blue (Reserved / Info)
COLOR_INFO_BG = "#EFF6FF"
COLOR_INFO_TEXT = "#1E40AF"

# Room Status Color Map
STATUS_COLORS = {
    "Vacant": {
        "bg": COLOR_SUCCESS_BG,
        "fg": COLOR_SUCCESS_TEXT,
        "border": COLOR_SUCCESS,
        "badge": "#10B981"
    },
    "Occupied": {
        "bg": COLOR_DANGER_BG,
        "fg": COLOR_DANGER_TEXT,
        "border": COLOR_DANGER,
        "badge": "#EF4444"
    },
    "Needs Service": {
        "bg": COLOR_WARNING_BG,
        "fg": COLOR_WARNING_TEXT,
        "border": COLOR_WARNING,
        "badge": "#F59E0B"
    },
    "Reserved": {
        "bg": COLOR_INFO_BG,
        "fg": COLOR_INFO_TEXT,
        "border": COLOR_INFO,
        "badge": "#3B82F6"
    }
}

# Typography
FONT_FAMILY = "Segoe UI"
FONT_HEADING = (FONT_FAMILY, 22, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 15, "bold")
FONT_TITLE = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_SMALL_BOLD = (FONT_FAMILY, 9, "bold")
FONT_STAT_VAL = (FONT_FAMILY, 20, "bold")
