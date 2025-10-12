"""
Color palette for PerforMetrics v2.0 UI

Dark theme with violet accent colors for a human-crafted, professional look.
"""

# Core palette
ACCENT = "#7C3AED"
ACCENT_ALT = "#A78BFA"
BACKGROUND_DARK = "#0F0F0F"  # 더 어두운 회색으로 변경
SURFACE = "#151515"          # 더 밝은 검정색
SURFACE_ALT = "#151515"      # 더 밝은 검정색
TEXT_PRIMARY = "#E2E8F0"
TEXT_SECONDARY = "#94A3B8"
BORDER = "#FFFFFF0F"

# Semantic colors
SUCCESS = "#22C55E"
WARNING = "#F59E0B"
ERROR = "#EF4444"

# Legacy compatibility (keeping old names for existing code)
SLATE_200 = TEXT_PRIMARY
SLATE_400 = TEXT_SECONDARY
SLATE_500 = "rgba(100, 116, 139, 1)"
SLATE_600 = "rgba(71, 85, 105, 1)"
SLATE_700 = "rgba(51, 65, 85, 1)"
SLATE_800 = SURFACE
SLATE_900 = BACKGROUND_DARK

# Primary colors (updated to violet)
BLUE_400 = ACCENT_ALT
BLUE_500 = ACCENT
BLUE_600 = "#6D28D9"

# Success colors (green palette)
GREEN_400 = "rgba(74, 222, 128, 1)"
GREEN_500 = "rgba(34, 197, 94, 1)"
GREEN_600 = "rgba(22, 163, 74, 1)"

# Danger colors (red palette)
RED_400 = "rgba(248, 113, 113, 1)"
RED_500 = "rgba(239, 68, 68, 1)"
RED_600 = "rgba(220, 38, 38, 1)"

# Warning colors (yellow palette)
YELLOW_400 = "rgba(250, 204, 21, 1)"
YELLOW_500 = "rgba(234, 179, 8, 1)"
YELLOW_600 = "rgba(202, 138, 4, 1)"

# Special colors
WHITE = "rgba(255, 255, 255, 1)"
BLACK = "rgba(0, 0, 0, 1)"

# Transparency variants (for Glassmorphism)
def with_alpha(color: str, alpha: float) -> str:
    """Add transparency to a color"""
    # Extract RGB values from rgba string
    if color.startswith("rgba"):
        rgb_part = color.split("(")[1].split(")")[0]
        rgb_values = rgb_part.split(",")[:3]
        return f"rgba({','.join(rgb_values)},{alpha})"
    elif color.startswith("rgb"):
        rgb_part = color.split("(")[1].split(")")[0]
        rgb_values = rgb_part.split(",")
        return f"rgba({','.join(rgb_values)},{alpha})"
    else:
        return color

# Common transparency levels
ALPHA_10 = 0.1
ALPHA_20 = 0.2
ALPHA_30 = 0.3
ALPHA_40 = 0.4
ALPHA_50 = 0.5
ALPHA_60 = 0.6
ALPHA_70 = 0.7
ALPHA_80 = 0.8
ALPHA_90 = 0.9
ALPHA_95 = 0.95

# Glassmorphism colors
GLASS_BACKGROUND = with_alpha(SLATE_900, ALPHA_50)
GLASS_BORDER = with_alpha(SLATE_700, ALPHA_50)
GLASS_CARD_BG = with_alpha(SLATE_800, ALPHA_60)

# Neumorphism colors
NEURO_LIGHT = with_alpha(SLATE_700, ALPHA_30)
NEURO_DARK = with_alpha(BLACK, ALPHA_40)

# Component colors
SIDEBAR_BG = with_alpha(SLATE_900, ALPHA_70)
NAV_BUTTON_BG = with_alpha(SLATE_800, ALPHA_60)
NAV_BUTTON_HOVER = with_alpha(SLATE_700, ALPHA_50)
NAV_BUTTON_ACTIVE = with_alpha(BLUE_500, ALPHA_80)

# Input colors
INPUT_BG = with_alpha(SLATE_800, ALPHA_60)
INPUT_BORDER = with_alpha(SLATE_600, ALPHA_50)
INPUT_FOCUS = with_alpha(BLUE_400, ALPHA_80)

# Table colors
TABLE_BG = with_alpha(SLATE_900, ALPHA_60)
TABLE_GRID = with_alpha(SLATE_600, ALPHA_30)
TABLE_SELECTED = with_alpha(BLUE_500, ALPHA_30)
TABLE_HOVER = with_alpha(SLATE_700, ALPHA_40)

# Progress colors
PROGRESS_BG = with_alpha(SLATE_800, ALPHA_60)
PROGRESS_CHUNK = BLUE_500

# Scrollbar colors
SCROLLBAR_BG = with_alpha(SLATE_800, ALPHA_30)
SCROLLBAR_HANDLE = with_alpha(SLATE_600, ALPHA_60)
SCROLLBAR_HANDLE_HOVER = with_alpha(SLATE_500, ALPHA_80)

# Tooltip colors
TOOLTIP_BG = with_alpha(SLATE_900, ALPHA_95)
TOOLTIP_BORDER = with_alpha(BLUE_400, ALPHA_50)

# Text colors
TEXT_PRIMARY = SLATE_200
TEXT_SECONDARY = SLATE_400
TEXT_MUTED = SLATE_500
TEXT_INVERSE = WHITE
