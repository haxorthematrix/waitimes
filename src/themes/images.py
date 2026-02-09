"""Image management for ride theming."""

import logging
import math
import random
from pathlib import Path
from typing import Optional

import pygame

from src.themes.colors import get_color_scheme

logger = logging.getLogger(__name__)

# Base path for images
IMAGES_DIR = Path(__file__).parent.parent.parent / "assets" / "images"

# Full screen image size
SCREEN_SIZE = (800, 480)

# Ride name to image folder mapping
RIDE_IMAGE_MAP = {
    # Magic Kingdom
    "space mountain": "space_mountain",
    "haunted mansion": "haunted_mansion",
    "pirates": "pirates_caribbean",
    "jungle cruise": "jungle_cruise",
    "big thunder": "big_thunder",
    "seven dwarfs": "seven_dwarfs",
    "small world": "small_world",
    "peter pan": "peter_pan",
    "tron": "tron",
    "tiana": "tiana",
    "bayou adventure": "tiana",
    "buzz lightyear": "buzz_lightyear",
    "space ranger": "buzz_lightyear",
    "dumbo": "dumbo",
    "winnie the pooh": "winnie_pooh",
    "mad tea party": "mad_tea_party",
    "country bear": "country_bear",
    "carousel of progress": "carousel_progress",
    "peoplemover": "peoplemover",
    "transit authority": "peoplemover",
    "little mermaid": "little_mermaid",
    "under the sea": "little_mermaid",
    "astro orbiter": "astro_orbiter",
    "barnstormer": "barnstormer",
    "magic carpets": "magic_carpets",
    "aladdin": "magic_carpets",
    "monsters inc": "monsters_inc",
    "laugh floor": "monsters_inc",
    "philharmagic": "philharmagic",
    "enchanted tiki": "tiki_room",

    # EPCOT
    "guardians": "guardians_galaxy",
    "cosmic rewind": "guardians_galaxy",
    "frozen": "frozen",
    "test track": "test_track",
    "remy": "remy",
    "ratatouille": "remy",
    "spaceship earth": "spaceship_earth",
    "soarin": "soarin",
    "living with the land": "living_land",
    "figment": "figment",
    "imagination": "figment",
    "mission: space": "mission_space",
    "mission space": "mission_space",
    "nemo & friends": "seas_nemo",
    "seas with nemo": "seas_nemo",
    "turtle talk": "seas_nemo",
    "journey of water": "journey_water",
    "moana": "journey_water",
    "gran fiesta": "gran_fiesta",
    "three caballeros": "gran_fiesta",

    # Hollywood Studios
    "rise of the resistance": "rise_resistance",
    "millennium falcon": "millennium_falcon",
    "smugglers run": "millennium_falcon",
    "tower of terror": "tower_terror",
    "twilight zone": "tower_terror",
    "slinky dog": "slinky_dog",
    "rock 'n' roller": "rock_roller",
    "aerosmith": "rock_roller",
    "toy story": "toy_story",
    "alien swirling": "alien_saucers",
    "star tours": "star_tours",
    "runaway railway": "runaway_railway",
    "mickey & minnie": "runaway_railway",
    "indiana jones": "indiana_jones",
    "epic stunt": "indiana_jones",

    # Animal Kingdom
    "flight of passage": "flight_passage",
    "avatar": "flight_passage",
    "na'vi river": "navi_river",
    "everest": "everest",
    "expedition everest": "everest",
    "kilimanjaro": "kilimanjaro",
    "safari": "kilimanjaro",
    "kali river": "kali_river",
    "lion king": "lion_king",
    "festival of the lion": "lion_king",
    "finding nemo": "finding_nemo_show",
    "big blue": "finding_nemo_show",
    "zootopia": "zootopia",
    "gorilla falls": "gorilla_falls",
    "wildlife express": "wildlife_express",

    # Magic Kingdom misc
    "railroad": "railroad",
    "hall of presidents": "hall_presidents",
    "speedway": "speedway",
    "regal carrousel": "carrousel",

    # Character meets
    "meet mickey": "meet_mickey",
    "town square theater": "meet_mickey",
    "princess fairytale hall": "meet_princesses",
    "meet cinderella": "meet_princesses",
    "meet princess tiana": "meet_princesses",
    "royal sommerhus": "meet_anna_elsa",
    "meet anna": "meet_anna_elsa",
    "meet elsa": "meet_anna_elsa",
    "red carpet dreams": "meet_characters",
    "meet olaf": "meet_characters",
    "celebrity spotlight": "meet_characters",
    "adventurers outpost": "meet_characters",
    "meet beloved": "meet_characters",
}


class ImageManager:
    """Manages loading and caching of ride images."""

    def __init__(self):
        self._image_cache: dict[str, list[pygame.Surface]] = {}
        self._placeholder_cache: dict[str, pygame.Surface] = {}
        self._cycle_index: dict[str, int] = {}

    def _get_folder_for_ride(self, ride_name: str) -> str:
        """Get the image folder name for a ride."""
        ride_lower = ride_name.lower()

        for pattern, folder in RIDE_IMAGE_MAP.items():
            if pattern in ride_lower:
                return folder

        return "generic"

    def _load_images_from_folder(self, folder: str) -> list[pygame.Surface]:
        """Load all images from a folder."""
        folder_path = IMAGES_DIR / folder

        if not folder_path.exists():
            logger.debug(f"Image folder not found: {folder}")
            return []

        images = []
        for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
            for img_path in folder_path.glob(ext):
                try:
                    img = pygame.image.load(str(img_path))
                    images.append(img)
                    logger.debug(f"Loaded image: {img_path.name}")
                except pygame.error as e:
                    logger.warning(f"Failed to load image {img_path}: {e}")

        if images:
            logger.info(f"Loaded {len(images)} images from {folder}")

        return images

    def _create_placeholder(self, ride_name: str, theme: str) -> pygame.Surface:
        """Create a visually interesting placeholder image."""
        colors = get_color_scheme(theme)
        surface = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)

        # Create base gradient
        self._draw_gradient(surface, colors.background, colors.accent)

        # Add theme-specific visual elements
        self._draw_theme_elements(surface, theme, colors)

        return surface

    def _draw_gradient(self, surface: pygame.Surface, color1: tuple, color2: tuple):
        """Draw a diagonal gradient background."""
        width, height = surface.get_size()

        for y in range(height):
            for x in range(width):
                # Diagonal gradient with some variation
                ratio = (x + y) / (width + height)
                noise = math.sin(x * 0.02) * 0.05 + math.sin(y * 0.03) * 0.05

                r = int(color1[0] * (1 - ratio) + color2[0] * ratio * 0.4)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio * 0.4)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio * 0.4)

                # Clamp values
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))

                surface.set_at((x, y), (r, g, b, 255))

    def _draw_theme_elements(self, surface: pygame.Surface, theme: str, colors):
        """Draw decorative elements based on theme."""
        width, height = surface.get_size()

        if theme == "scifi":
            # Futuristic grid lines and circles
            for i in range(0, width, 80):
                alpha = 40 + random.randint(0, 20)
                pygame.draw.line(surface, (*colors.accent, alpha), (i, 0), (i, height), 1)
            for i in range(0, height, 60):
                alpha = 40 + random.randint(0, 20)
                pygame.draw.line(surface, (*colors.accent, alpha), (0, i), (width, i), 1)

            # Glowing orbs
            for _ in range(5):
                x = random.randint(100, width - 100)
                y = random.randint(100, height - 100)
                for r in range(60, 10, -10):
                    alpha = int(30 * (60 - r) / 50)
                    pygame.draw.circle(surface, (*colors.accent, alpha), (x, y), r)

        elif theme == "spooky":
            # Eerie fog/mist effect
            for _ in range(15):
                x = random.randint(-50, width)
                y = random.randint(height // 2, height)
                w = random.randint(100, 300)
                h = random.randint(30, 80)
                fog = pygame.Surface((w, h), pygame.SRCALPHA)
                for fy in range(h):
                    alpha = int(25 * (1 - fy / h))
                    pygame.draw.line(fog, (150, 100, 150, alpha), (0, fy), (w, fy))
                surface.blit(fog, (x, y))

            # Ghostly vertical streaks
            for _ in range(8):
                x = random.randint(0, width)
                h = random.randint(100, 300)
                for offset in range(-5, 6):
                    alpha = 20 - abs(offset) * 3
                    pygame.draw.line(
                        surface, (*colors.accent, max(0, alpha)),
                        (x + offset, height - h), (x + offset, height)
                    )

        elif theme == "starwars":
            # Star field
            for _ in range(150):
                x = random.randint(0, width)
                y = random.randint(0, height)
                brightness = random.randint(100, 255)
                size = random.choice([1, 1, 1, 2])
                pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)

            # Hyperspace streaks
            cx, cy = width // 2, height // 2
            for _ in range(30):
                angle = random.uniform(0, 2 * math.pi)
                length = random.randint(50, 200)
                start_dist = random.randint(50, 150)
                x1 = cx + int(math.cos(angle) * start_dist)
                y1 = cy + int(math.sin(angle) * start_dist)
                x2 = cx + int(math.cos(angle) * (start_dist + length))
                y2 = cy + int(math.sin(angle) * (start_dist + length))
                pygame.draw.line(surface, (*colors.accent, 100), (x1, y1), (x2, y2), 2)

        elif theme == "avatar":
            # Bioluminescent plants
            for _ in range(40):
                x = random.randint(0, width)
                y = random.randint(height // 3, height)
                # Glowing stem
                h = random.randint(40, 150)
                for i in range(h):
                    alpha = int(60 * (1 - i / h))
                    sway = int(math.sin(i * 0.1) * 5)
                    pygame.draw.circle(
                        surface, (*colors.accent, alpha),
                        (x + sway, y - i), 2
                    )
                # Glowing top
                for r in range(15, 3, -2):
                    alpha = int(80 * (15 - r) / 12)
                    pygame.draw.circle(surface, (*colors.accent, alpha), (x, y - h), r)

        elif theme == "pirate":
            # Waves
            for wave_y in range(height - 100, height, 20):
                points = []
                for x in range(0, width + 20, 20):
                    y_offset = int(math.sin(x * 0.03 + wave_y * 0.1) * 10)
                    points.append((x, wave_y + y_offset))
                if len(points) >= 2:
                    pygame.draw.lines(surface, (*colors.accent, 60), False, points, 2)

            # Coins/treasure sparkles
            for _ in range(20):
                x = random.randint(50, width - 50)
                y = random.randint(50, height - 50)
                pygame.draw.circle(surface, (*colors.accent, 150), (x, y), 4)
                pygame.draw.circle(surface, (255, 255, 200, 100), (x - 1, y - 1), 2)

        elif theme in ["whimsical", "playful"]:
            # Floating bubbles/circles
            for _ in range(25):
                x = random.randint(0, width)
                y = random.randint(0, height)
                r = random.randint(20, 60)
                pygame.draw.circle(surface, (*colors.accent, 40), (x, y), r)
                pygame.draw.circle(surface, (*colors.accent, 80), (x, y), r, 2)

            # Confetti
            for _ in range(50):
                x = random.randint(0, width)
                y = random.randint(0, height)
                w = random.randint(5, 15)
                h = random.randint(5, 15)
                color = random.choice([
                    (*colors.accent, 100),
                    (255, 200, 100, 100),
                    (100, 200, 255, 100),
                ])
                pygame.draw.rect(surface, color, (x, y, w, h))

        elif theme == "fantasy":
            # Sparkles/fairy dust
            for _ in range(60):
                x = random.randint(0, width)
                y = random.randint(0, height)
                # Four-pointed star
                size = random.randint(3, 10)
                alpha = random.randint(80, 200)
                points = [
                    (x, y - size), (x + 2, y),
                    (x + size, y), (x + 2, y + 2),
                    (x, y + size), (x - 2, y + 2),
                    (x - size, y), (x - 2, y)
                ]
                pygame.draw.polygon(surface, (*colors.accent, alpha), points)

        elif theme == "adventure":
            # Jungle vines/leaves
            for _ in range(10):
                x = random.randint(0, width)
                # Hanging vine
                points = [(x, 0)]
                y = 0
                while y < height * 0.7:
                    y += random.randint(20, 40)
                    x += random.randint(-20, 20)
                    points.append((x, y))
                if len(points) >= 2:
                    pygame.draw.lines(surface, (*colors.accent, 80), False, points, 3)

            # Scattered leaves
            for _ in range(30):
                x = random.randint(0, width)
                y = random.randint(0, height)
                pygame.draw.ellipse(
                    surface, (*colors.accent, 60),
                    (x, y, random.randint(10, 25), random.randint(5, 12))
                )

        else:  # classic/default
            # Subtle Disney-esque sparkle pattern
            for _ in range(40):
                x = random.randint(0, width)
                y = random.randint(0, height)
                size = random.randint(2, 6)
                pygame.draw.circle(surface, (*colors.accent, 80), (x, y), size)
                pygame.draw.circle(surface, (255, 255, 255, 40), (x, y), size + 2)

    def get_image(self, ride_name: str, theme: str) -> pygame.Surface:
        """Get an image for a ride (does not auto-cycle)."""
        folder = self._get_folder_for_ride(ride_name)

        # Load images if not cached
        if folder not in self._image_cache:
            self._image_cache[folder] = self._load_images_from_folder(folder)
            self._cycle_index[folder] = 0

        images = self._image_cache[folder]

        # If we have real images, return current one (no auto-cycle)
        if images:
            idx = self._cycle_index[folder]
            return images[idx]

        # Otherwise return a placeholder
        cache_key = f"{folder}_{theme}"
        if cache_key not in self._placeholder_cache:
            self._placeholder_cache[cache_key] = self._create_placeholder(ride_name, theme)

        return self._placeholder_cache[cache_key]

    def advance_all_cycles(self):
        """Advance image cycle for all rides. Call after a full round of rides."""
        for folder in self._cycle_index:
            if folder in self._image_cache and self._image_cache[folder]:
                num_images = len(self._image_cache[folder])
                self._cycle_index[folder] = (self._cycle_index[folder] + 1) % num_images

    def get_park_image(self, park_slug: str) -> Optional[pygame.Surface]:
        """Get an image for a park (for closed park displays)."""
        parks_dir = IMAGES_DIR / "parks"
        image_path = parks_dir / f"{park_slug}.png"

        if not image_path.exists():
            # Try jpg
            image_path = parks_dir / f"{park_slug}.jpg"

        if image_path.exists():
            try:
                img = pygame.image.load(str(image_path))
                logger.debug(f"Loaded park image: {park_slug}")
                return img
            except pygame.error as e:
                logger.warning(f"Failed to load park image {park_slug}: {e}")

        return None

    def preload_all(self):
        """Preload images for all mapped rides."""
        folders = set(RIDE_IMAGE_MAP.values())
        folders.add("generic")

        for folder in folders:
            if folder not in self._image_cache:
                self._image_cache[folder] = self._load_images_from_folder(folder)
                self._cycle_index[folder] = 0


# Global image manager instance
_image_manager: Optional[ImageManager] = None


def get_image_manager() -> ImageManager:
    """Get the global ImageManager instance."""
    global _image_manager
    if _image_manager is None:
        _image_manager = ImageManager()
    return _image_manager
