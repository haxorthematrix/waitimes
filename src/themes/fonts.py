"""Font mappings for ride theming."""

import logging
from pathlib import Path
from typing import Optional

import pygame

logger = logging.getLogger(__name__)

# Base path for fonts
FONTS_DIR = Path(__file__).parent.parent.parent / "assets" / "fonts"

# Available font files
FONT_FILES = {
    "orbitron": "Orbitron-Bold.ttf",
    "creepster": "Creepster-Regular.ttf",
    "pirata": "PirataOne-Regular.ttf",
    "rye": "Rye-Regular.ttf",
    "fredoka": "FredokaOne-Regular.ttf",
    "luckiest": "LuckiestGuy-Regular.ttf",
    "bangers": "Bangers-Regular.ttf",
    "cinzel": "Cinzel-Bold.ttf",
    "exo2": "Exo2-Bold.ttf",
    "audiowide": "Audiowide-Regular.ttf",
}

# Theme categories for font selection
FONT_THEMES = {
    "scifi": "orbitron",       # Space Mountain, TRON, Test Track
    "spooky": "creepster",     # Haunted Mansion, Tower of Terror
    "pirate": "pirata",        # Pirates of the Caribbean
    "adventure": "rye",        # Jungle Cruise, Expedition Everest, Safari
    "whimsical": "fredoka",    # It's a Small World, character meets
    "playful": "luckiest",     # Toy Story rides, Dumbo, teacups
    "action": "bangers",       # Rock n Roller Coaster, Slinky Dog
    "fantasy": "cinzel",       # Fantasyland rides, Frozen
    "future": "exo2",          # Tomorrowland, Epcot Future World
    "starwars": "audiowide",   # Star Wars rides
    "avatar": "exo2",          # Pandora rides
    "classic": "cinzel",       # Classic Disney rides
}

# Ride name to theme mapping (partial matches supported)
# The key is searched within the ride name (case-insensitive)
RIDE_THEME_MAP = {
    # Magic Kingdom - Tomorrowland
    "space mountain": "scifi",
    "tron": "scifi",
    "astro orbiter": "scifi",
    "buzz lightyear": "scifi",
    "space ranger": "scifi",
    "peoplemover": "future",
    "transit authority": "future",
    "carousel of progress": "future",
    "tomorrowland speedway": "future",
    "monsters inc": "playful",
    "laugh floor": "playful",

    # Magic Kingdom - Fantasyland
    "haunted mansion": "spooky",
    "seven dwarfs": "fantasy",
    "peter pan": "fantasy",
    "small world": "whimsical",
    "little mermaid": "fantasy",
    "under the sea": "fantasy",
    "dumbo": "playful",
    "mad tea": "playful",
    "carrousel": "fantasy",
    "regal carrousel": "fantasy",
    "barnstormer": "playful",
    "winnie the pooh": "whimsical",
    "philharmagic": "fantasy",
    "princess": "fantasy",
    "cinderella": "fantasy",
    "enchanted tales": "fantasy",
    "tiana": "whimsical",
    "bayou adventure": "whimsical",

    # Magic Kingdom - Adventureland
    "pirates": "pirate",
    "jungle cruise": "adventure",
    "magic carpets": "adventure",
    "tiki room": "adventure",
    "enchanted tiki": "adventure",

    # Magic Kingdom - Frontierland
    "big thunder": "adventure",
    "splash mountain": "adventure",
    "country bear": "adventure",
    "tom sawyer": "adventure",

    # Magic Kingdom - Liberty Square
    "hall of presidents": "classic",

    # EPCOT
    "guardians": "scifi",
    "cosmic rewind": "scifi",
    "test track": "scifi",
    "spaceship earth": "future",
    "mission: space": "scifi",
    "mission space": "scifi",
    "frozen": "fantasy",
    "remy": "whimsical",
    "ratatouille": "whimsical",
    "soarin": "adventure",
    "figment": "whimsical",
    "imagination": "whimsical",
    "nemo": "whimsical",
    "seas with nemo": "whimsical",
    "living with the land": "adventure",
    "gran fiesta": "whimsical",
    "three caballeros": "whimsical",
    "turtle talk": "whimsical",
    "journey of water": "adventure",
    "moana": "adventure",

    # Hollywood Studios
    "tower of terror": "spooky",
    "twilight zone": "spooky",
    "rock 'n' roller": "action",
    "aerosmith": "action",
    "slinky dog": "playful",
    "toy story": "playful",
    "alien swirling": "playful",
    "rise of the resistance": "starwars",
    "millennium falcon": "starwars",
    "smugglers run": "starwars",
    "star tours": "starwars",
    "runaway railway": "playful",
    "mickey & minnie": "playful",
    "indiana jones": "adventure",
    "epic stunt": "adventure",
    "muppet": "playful",
    "beauty and the beast": "fantasy",
    "frozen sing": "fantasy",

    # Animal Kingdom
    "flight of passage": "avatar",
    "avatar": "avatar",
    "na'vi river": "avatar",
    "everest": "adventure",
    "expedition everest": "adventure",
    "kilimanjaro": "adventure",
    "safari": "adventure",
    "kali river": "adventure",
    "lion king": "adventure",
    "festival of the lion": "adventure",
    "finding nemo": "whimsical",
    "big blue": "whimsical",
    "gorilla falls": "adventure",
    "zootopia": "playful",
    "wildlife express": "adventure",
    "railroad": "classic",
    "hall of presidents": "classic",
    "speedway": "future",
    "regal carrousel": "fantasy",

    # Character meets
    "meet mickey": "classic",
    "town square": "classic",
    "princess fairytale": "fantasy",
    "royal sommerhus": "fantasy",
    "meet anna": "fantasy",
    "meet elsa": "fantasy",
    "red carpet": "playful",
    "meet olaf": "fantasy",
    "celebrity spotlight": "playful",
    "adventurers outpost": "adventure",
    "meet beloved": "classic",
}

# Default theme for rides not in the map
DEFAULT_THEME = "classic"


class FontManager:
    """Manages loading and caching of themed fonts."""

    def __init__(self):
        self._font_cache: dict[tuple[str, int], pygame.font.Font] = {}
        self._available_fonts: set[str] = set()
        self._check_available_fonts()

    def _check_available_fonts(self):
        """Check which font files are available."""
        for font_id, filename in FONT_FILES.items():
            path = FONTS_DIR / filename
            if path.exists():
                self._available_fonts.add(font_id)
                logger.debug(f"Font available: {font_id}")
            else:
                logger.warning(f"Font file not found: {filename}")

        logger.info(f"Loaded {len(self._available_fonts)} fonts")

    def get_theme_for_ride(self, ride_name: str) -> str:
        """Determine the theme for a ride based on its name.

        Args:
            ride_name: The name of the ride

        Returns:
            Theme identifier string
        """
        ride_lower = ride_name.lower()

        for pattern, theme in RIDE_THEME_MAP.items():
            if pattern in ride_lower:
                return theme

        return DEFAULT_THEME

    def get_font(
        self,
        theme: str,
        size: int,
        fallback: bool = True
    ) -> pygame.font.Font:
        """Get a pygame font for the specified theme and size.

        Args:
            theme: Theme identifier (e.g., 'scifi', 'spooky')
            size: Font size in points
            fallback: If True, fall back to system font if theme font unavailable

        Returns:
            pygame.font.Font instance
        """
        font_id = FONT_THEMES.get(theme, FONT_THEMES[DEFAULT_THEME])
        cache_key = (font_id, size)

        # Check cache
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        # Try to load themed font
        if font_id in self._available_fonts:
            font_path = FONTS_DIR / FONT_FILES[font_id]
            try:
                font = pygame.font.Font(str(font_path), size)
                self._font_cache[cache_key] = font
                return font
            except pygame.error as e:
                logger.warning(f"Failed to load font {font_id}: {e}")

        # Fallback to system font
        if fallback:
            fallback_key = ("_system", size)
            if fallback_key not in self._font_cache:
                self._font_cache[fallback_key] = pygame.font.Font(None, size)
            return self._font_cache[fallback_key]

        raise ValueError(f"Font not available: {font_id}")

    def get_font_for_ride(self, ride_name: str, size: int) -> pygame.font.Font:
        """Get the appropriate font for a specific ride.

        Args:
            ride_name: The name of the ride
            size: Font size in points

        Returns:
            pygame.font.Font instance
        """
        theme = self.get_theme_for_ride(ride_name)
        return self.get_font(theme, size)


# Global font manager instance
_font_manager: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    """Get the global FontManager instance."""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager
