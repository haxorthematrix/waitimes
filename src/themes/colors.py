"""Color schemes for ride theming."""

from dataclasses import dataclass
from typing import Optional

# Type alias for RGB colors
Color = tuple[int, int, int]


@dataclass
class ColorScheme:
    """Color scheme for a ride display."""

    background: Color
    accent: Color
    text_primary: Color = (255, 255, 255)
    text_secondary: Color = (180, 180, 180)
    image_border: Optional[Color] = None

    def __post_init__(self):
        # Default image border to accent color
        if self.image_border is None:
            self.image_border = self.accent


# Wait time colors (universal across all themes)
WAIT_COLORS = {
    "short": (46, 204, 113),      # Green: 0-20 min
    "moderate": (241, 196, 15),    # Yellow: 21-45 min
    "long": (230, 126, 34),        # Orange: 46-75 min
    "very_long": (231, 76, 60),    # Red: 76+ min
}

# Theme color schemes
THEME_COLORS = {
    "scifi": ColorScheme(
        background=(10, 10, 25),
        accent=(76, 201, 240),      # Bright cyan
    ),
    "spooky": ColorScheme(
        background=(25, 10, 25),
        accent=(128, 19, 54),       # Deep red/purple
        text_secondary=(150, 130, 150),
    ),
    "pirate": ColorScheme(
        background=(20, 15, 10),
        accent=(201, 162, 39),      # Gold
        text_secondary=(180, 160, 130),
    ),
    "adventure": ColorScheme(
        background=(15, 35, 25),
        accent=(149, 213, 178),     # Soft green
    ),
    "whimsical": ColorScheme(
        background=(40, 35, 50),
        accent=(255, 159, 28),      # Warm orange
        text_secondary=(200, 190, 210),
    ),
    "playful": ColorScheme(
        background=(30, 30, 45),
        accent=(255, 107, 107),     # Coral
    ),
    "action": ColorScheme(
        background=(15, 15, 20),
        accent=(255, 65, 54),       # Hot red
    ),
    "fantasy": ColorScheme(
        background=(25, 20, 35),
        accent=(180, 130, 255),     # Soft purple
        text_secondary=(190, 180, 200),
    ),
    "future": ColorScheme(
        background=(15, 20, 30),
        accent=(100, 200, 255),     # Light blue
    ),
    "starwars": ColorScheme(
        background=(5, 5, 10),
        accent=(255, 69, 0),        # Orange-red (lightsaber)
    ),
    "avatar": ColorScheme(
        background=(5, 20, 25),
        accent=(0, 255, 200),       # Bioluminescent teal
    ),
    "classic": ColorScheme(
        background=(20, 20, 30),
        accent=(255, 215, 0),       # Classic gold
    ),
}

# Default scheme
DEFAULT_SCHEME = THEME_COLORS["classic"]


def get_color_scheme(theme: str) -> ColorScheme:
    """Get the color scheme for a theme.

    Args:
        theme: Theme identifier

    Returns:
        ColorScheme instance
    """
    return THEME_COLORS.get(theme, DEFAULT_SCHEME)


def get_wait_color(category: str) -> Color:
    """Get the color for a wait time category.

    Args:
        category: Wait category ('short', 'moderate', 'long', 'very_long')

    Returns:
        RGB color tuple
    """
    return WAIT_COLORS.get(category, WAIT_COLORS["moderate"])


def blend_colors(color1: Color, color2: Color, ratio: float = 0.5) -> Color:
    """Blend two colors together.

    Args:
        color1: First RGB color
        color2: Second RGB color
        ratio: Blend ratio (0.0 = all color1, 1.0 = all color2)

    Returns:
        Blended RGB color
    """
    return (
        int(color1[0] * (1 - ratio) + color2[0] * ratio),
        int(color1[1] * (1 - ratio) + color2[1] * ratio),
        int(color1[2] * (1 - ratio) + color2[2] * ratio),
    )


def darken(color: Color, amount: float = 0.3) -> Color:
    """Darken a color.

    Args:
        color: RGB color
        amount: Darkening amount (0.0 = no change, 1.0 = black)

    Returns:
        Darkened RGB color
    """
    return (
        int(color[0] * (1 - amount)),
        int(color[1] * (1 - amount)),
        int(color[2] * (1 - amount)),
    )


def lighten(color: Color, amount: float = 0.3) -> Color:
    """Lighten a color.

    Args:
        color: RGB color
        amount: Lightening amount (0.0 = no change, 1.0 = white)

    Returns:
        Lightened RGB color
    """
    return (
        int(color[0] + (255 - color[0]) * amount),
        int(color[1] + (255 - color[1]) * amount),
        int(color[2] + (255 - color[2]) * amount),
    )
