"""Main display renderer for wait times."""

import logging
import time as time_module
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pygame

from src.models.ride import Ride, WaitTimesData, ClosedPark
from src.themes.colors import get_color_scheme, get_wait_color, ColorScheme
from src.themes.fonts import get_font_manager, FontManager
from src.themes.images import get_image_manager, ImageManager
from src.api.weather import WeatherData
from src.events.scheduler import EventScheduler, ScheduledEvent, EventType
from src.events.animations import FireworksAnimation, ParadeAnimation, VideoPlayer

logger = logging.getLogger(__name__)

# Display dimensions (Raspberry Pi 7" touchscreen)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

# Layout constants for overlay box
BOX_MARGIN = 30
BOX_PADDING = 20
BOX_ALPHA = 200  # Semi-transparent (0-255)

DOT_Y = SCREEN_HEIGHT - 25
DOT_RADIUS = 5
DOT_SPACING = 16

# Status indicator colors
STATUS_WARNING = (255, 193, 7)   # Amber for stale data
STATUS_ERROR = (220, 53, 69)     # Red for errors


@dataclass
class DisplayConfig:
    """Configuration for the display."""

    width: int = SCREEN_WIDTH
    height: int = SCREEN_HEIGHT
    fullscreen: bool = False
    fps: int = 30
    display_duration: float = 8.0  # seconds per ride
    transition_duration: float = 0.5  # crossfade duration


class RideDisplay:
    """Handles rendering of ride wait times with full-screen images."""

    def __init__(self, config: Optional[DisplayConfig] = None):
        self.config = config or DisplayConfig()
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.running = False

        # Theme managers (initialized in setup)
        self.font_manager: Optional[FontManager] = None
        self.image_manager: Optional[ImageManager] = None

        # Fallback fonts
        self.font_small: Optional[pygame.font.Font] = None

        # Current state
        self.rides: list[Ride] = []
        self.display_items: list = []  # Rides + ClosedParks
        self.current_index: int = 0
        self.time_on_current: float = 0.0

        # Data state tracking
        self.last_data_update: Optional[datetime] = None
        self.data_is_stale: bool = False
        self.last_error: Optional[str] = None

        # Transition state
        self.transitioning: bool = False
        self.transition_progress: float = 0.0
        self.prev_surface: Optional[pygame.Surface] = None
        self.next_surface: Optional[pygame.Surface] = None

        # Weather data
        self.weather_data: Optional[WeatherData] = None

        # Event system
        self.event_scheduler: Optional[EventScheduler] = None
        self.active_event: Optional[ScheduledEvent] = None
        self.fireworks_animation: Optional[FireworksAnimation] = None
        self.parade_animation: Optional[ParadeAnimation] = None
        self.event_start_time: float = 0.0
        # Video players for events (keyed by park_slug + event_type)
        self.event_videos: dict[str, VideoPlayer] = {}
        self.current_video_player: Optional[VideoPlayer] = None

    def setup(self) -> bool:
        """Initialize pygame and create window."""
        try:
            pygame.init()
            pygame.font.init()

            # Set up display
            flags = pygame.FULLSCREEN if self.config.fullscreen else 0
            self.screen = pygame.display.set_mode(
                (self.config.width, self.config.height), flags
            )
            pygame.display.set_caption("Disney Wait Times")

            # Hide mouse cursor for kiosk mode
            if self.config.fullscreen:
                pygame.mouse.set_visible(False)

            self.clock = pygame.time.Clock()

            # Initialize theme managers with error handling
            try:
                self.font_manager = get_font_manager()
            except Exception as e:
                logger.error(f"Failed to initialize font manager: {e}")
                self.font_manager = None

            try:
                self.image_manager = get_image_manager()
            except Exception as e:
                logger.error(f"Failed to initialize image manager: {e}")
                self.image_manager = None

            # Fallback font
            self.font_small = pygame.font.Font(None, 24)

            logger.info(
                f"Display initialized: {self.config.width}x{self.config.height}"
            )
            return True

        except pygame.error as e:
            logger.error(f"Failed to initialize display: {e}")
            return False

    def shutdown(self):
        """Clean up pygame resources."""
        pygame.quit()
        logger.info("Display shut down")

    def set_rides(self, data: WaitTimesData):
        """Update the list of rides to display."""
        self.rides = data.all_open_rides
        self.display_items = data.get_display_items()
        if self.current_index >= len(self.display_items):
            self.current_index = 0

        # Update data freshness tracking
        self.last_data_update = data.last_fetch
        self.data_is_stale = data.is_stale

        if not data.fetch_success:
            self.last_error = data.error_message
        else:
            self.last_error = None

        closed_count = len(data.closed_parks)
        logger.info(f"Display updated with {len(self.rides)} rides, {closed_count} closed parks")

    def set_weather(self, weather: Optional[WeatherData]):
        """Update the weather data for display."""
        self.weather_data = weather
        if weather:
            logger.debug(f"Weather updated: {weather.temp_display}, {weather.condition}")

    def set_event_scheduler(self, scheduler: EventScheduler, video_paths: Optional[dict] = None):
        """Set the event scheduler for fireworks/parade events.

        Args:
            scheduler: EventScheduler instance
            video_paths: Optional dict mapping event keys to video paths
                         e.g. {"magic-kingdom_fireworks": "path/to/video.mp4"}
        """
        self.event_scheduler = scheduler
        # Initialize fallback animations
        self.fireworks_animation = FireworksAnimation(self.config.width, self.config.height)
        self.parade_animation = ParadeAnimation(self.config.width, self.config.height)

        # Load event videos if paths provided
        if video_paths:
            for key, path in video_paths.items():
                player = VideoPlayer(self.config.width, self.config.height)
                if player.load(path):
                    self.event_videos[key] = player
                    logger.info(f"Loaded event video: {key} -> {path}")
                else:
                    logger.warning(f"Failed to load event video: {path}")

        logger.info(f"Event scheduler set with {len(scheduler.events)} scheduled events, {len(self.event_videos)} videos")

    def _get_data_age_minutes(self) -> int:
        """Get age of current data in minutes."""
        if self.last_data_update is None:
            return -1
        age = datetime.now() - self.last_data_update
        return int(age.total_seconds() / 60)

    def _draw_weather_icon(self, surface: pygame.Surface, icon_code: str, x: int, y: int, size: int = 40):
        """Draw a weather icon at the specified position.

        Args:
            surface: Surface to draw on
            icon_code: OpenWeatherMap icon code (e.g., "01d", "10n")
            x: Center x position
            y: Center y position
            size: Icon size in pixels
        """
        half = size // 2

        if icon_code in ("01d",):  # Sunny
            # Yellow sun with rays
            pygame.draw.circle(surface, (255, 220, 50), (x, y), half - 5)
            for angle in range(0, 360, 45):
                import math
                rad = math.radians(angle)
                x1 = x + int((half - 8) * math.cos(rad))
                y1 = y + int((half - 8) * math.sin(rad))
                x2 = x + int((half + 2) * math.cos(rad))
                y2 = y + int((half + 2) * math.sin(rad))
                pygame.draw.line(surface, (255, 220, 50), (x1, y1), (x2, y2), 2)

        elif icon_code in ("01n",):  # Clear night - moon
            pygame.draw.circle(surface, (220, 220, 180), (x, y), half - 5)
            pygame.draw.circle(surface, (0, 0, 0, 0), (x + 8, y - 5), half - 8)  # Crescent effect
            # Draw crescent by overlapping circles
            pygame.draw.circle(surface, (220, 220, 180), (x - 3, y), half - 5)
            pygame.draw.circle(surface, (30, 30, 50), (x + 6, y - 3), half - 7)

        elif icon_code in ("02d", "02n", "03d", "03n", "04d", "04n"):  # Cloudy
            # Gray cloud shape
            cloud_color = (180, 180, 190)
            pygame.draw.circle(surface, cloud_color, (x - 8, y + 3), 12)
            pygame.draw.circle(surface, cloud_color, (x + 5, y + 5), 10)
            pygame.draw.circle(surface, cloud_color, (x, y - 3), 14)
            pygame.draw.circle(surface, cloud_color, (x + 12, y), 11)

        elif icon_code in ("09d", "09n", "10d", "10n"):  # Rain
            # Cloud with rain drops
            cloud_color = (150, 150, 160)
            pygame.draw.circle(surface, cloud_color, (x - 6, y - 5), 10)
            pygame.draw.circle(surface, cloud_color, (x + 6, y - 3), 9)
            pygame.draw.circle(surface, cloud_color, (x, y - 10), 11)
            # Rain drops
            rain_color = (100, 150, 255)
            for dx in [-8, 0, 8]:
                pygame.draw.line(surface, rain_color, (x + dx, y + 8), (x + dx - 3, y + 16), 2)

        elif icon_code in ("11d", "11n"):  # Storm/thunder
            # Dark cloud with lightning
            cloud_color = (100, 100, 110)
            pygame.draw.circle(surface, cloud_color, (x - 6, y - 8), 10)
            pygame.draw.circle(surface, cloud_color, (x + 6, y - 6), 9)
            pygame.draw.circle(surface, cloud_color, (x, y - 12), 11)
            # Lightning bolt
            bolt_color = (255, 255, 100)
            points = [(x, y - 2), (x - 5, y + 8), (x + 2, y + 6), (x - 3, y + 18)]
            pygame.draw.lines(surface, bolt_color, False, points, 3)

        elif icon_code in ("13d", "13n"):  # Snow
            # Cloud with snowflakes
            cloud_color = (200, 200, 210)
            pygame.draw.circle(surface, cloud_color, (x - 6, y - 5), 10)
            pygame.draw.circle(surface, cloud_color, (x + 6, y - 3), 9)
            pygame.draw.circle(surface, cloud_color, (x, y - 10), 11)
            # Snowflakes as small circles
            snow_color = (255, 255, 255)
            for dx, dy in [(-8, 10), (0, 14), (8, 10), (-4, 18), (4, 16)]:
                pygame.draw.circle(surface, snow_color, (x + dx, y + dy), 2)

        elif icon_code in ("50d", "50n"):  # Fog/mist
            # Horizontal lines
            fog_color = (180, 180, 180)
            for dy in [-8, -2, 4, 10]:
                pygame.draw.line(surface, fog_color, (x - 15, y + dy), (x + 15, y + dy), 3)
        else:
            # Default: question mark or simple indicator
            pygame.draw.circle(surface, (150, 150, 150), (x, y), half - 5, 2)

    def _get_theme_for_ride(self, ride: Ride) -> str:
        """Get the theme identifier for a ride."""
        if self.font_manager:
            return self.font_manager.get_theme_for_ride(ride.name)
        return "classic"

    def _get_font(self, theme: str, size: int) -> pygame.font.Font:
        """Get a font with fallback handling."""
        if self.font_manager:
            try:
                return self.font_manager.get_font(theme, size)
            except Exception as e:
                logger.warning(f"Font error for theme {theme}: {e}")
        return pygame.font.Font(None, size)

    def _get_fullscreen_image(self, ride_name: str, theme: str) -> pygame.Surface:
        """Get a full-screen image for a ride."""
        if self.image_manager:
            try:
                img = self.image_manager.get_image(ride_name, theme)
                # Scale to fill screen
                return pygame.transform.smoothscale(
                    img, (self.config.width, self.config.height)
                )
            except Exception as e:
                logger.warning(f"Image error for {ride_name}: {e}")

        # Create gradient fallback
        return self._create_gradient_background(theme)

    def _create_gradient_background(self, theme: str) -> pygame.Surface:
        """Create a gradient background based on theme colors."""
        colors = get_color_scheme(theme)
        surface = pygame.Surface(
            (self.config.width, self.config.height), pygame.SRCALPHA
        )

        # Vertical gradient from darker to lighter
        for y in range(self.config.height):
            ratio = y / self.config.height
            r = int(colors.background[0] * (1 - ratio * 0.3) + colors.accent[0] * ratio * 0.3)
            g = int(colors.background[1] * (1 - ratio * 0.3) + colors.accent[1] * ratio * 0.3)
            b = int(colors.background[2] * (1 - ratio * 0.3) + colors.accent[2] * ratio * 0.3)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.config.width, y))

        return surface

    def _render_ride_card(self, ride: Ride) -> pygame.Surface:
        """Render a single ride card with full-screen image and bottom bar overlay."""
        theme = self._get_theme_for_ride(ride)
        colors = get_color_scheme(theme)

        # Create surface
        surface = pygame.Surface(
            (self.config.width, self.config.height), pygame.SRCALPHA
        )

        # Full-screen background image
        bg_image = self._get_fullscreen_image(ride.name, theme)
        surface.blit(bg_image, (0, 0))

        # Get themed fonts
        font_ride_name = self._get_font(theme, 36)
        font_wait_time = self._get_font(theme, 80)
        font_weather = self._get_font("classic", 24)

        # Calculate bar height based on content
        bar_height = 140
        bar_y = self.config.height - bar_height  # Flush with bottom

        # Create full-width semi-transparent bar at bottom
        bar_surface = pygame.Surface((self.config.width, bar_height), pygame.SRCALPHA)
        bar_color = (*colors.background, BOX_ALPHA)
        bar_surface.fill(bar_color)

        # Add accent line at top of bar
        pygame.draw.line(
            bar_surface, (*colors.accent, 255),
            (0, 0), (self.config.width, 0), 3
        )

        surface.blit(bar_surface, (0, bar_y))

        # Weather section width (right side)
        weather_width = 100 if self.weather_data else 0
        content_width = self.config.width - weather_width - 40  # padding

        # Render wait time (large, on left side of content area)
        wait_color = get_wait_color(ride.wait_category)
        wait_surface = font_wait_time.render(ride.display_wait, True, wait_color)
        wait_x = 30
        wait_y = bar_y + 5  # Tight to top
        surface.blit(wait_surface, (wait_x, wait_y))

        # Render ride name (left-justified, below wait time)
        name_surface = font_ride_name.render(ride.name, True, colors.text_primary)
        max_name_width = content_width - 20
        if name_surface.get_width() > max_name_width:
            truncated = ride.name
            while name_surface.get_width() > max_name_width and len(truncated) > 10:
                truncated = truncated[:-4] + "..."
                name_surface = font_ride_name.render(truncated, True, colors.text_primary)
        name_x = 30  # Left-justified
        name_y = bar_y + 85  # More bottom margin
        surface.blit(name_surface, (name_x, name_y))

        # Render weather (right side, stacked icon + temp)
        if self.weather_data:
            weather_x = self.config.width - weather_width - 10

            # Weather icon
            icon_center_x = weather_x + weather_width // 2
            icon_center_y = bar_y + 45
            self._draw_weather_icon(surface, self.weather_data.icon_code, icon_center_x, icon_center_y, 50)

            # Temperature
            temp_surface = font_weather.render(
                self.weather_data.temp_display, True, colors.text_primary
            )
            temp_x = weather_x + (weather_width - temp_surface.get_width()) // 2
            temp_y = bar_y + 95
            surface.blit(temp_surface, (temp_x, temp_y))

        # Status indicator (stale data warning) - top right
        self._render_status_indicator(surface)

        return surface

    def _render_closed_park_card(self, park: ClosedPark) -> pygame.Surface:
        """Render a closed park card with full-screen image and bottom bar."""
        theme = "classic"  # Use classic theme for parks
        colors = get_color_scheme(theme)

        # Create surface
        surface = pygame.Surface(
            (self.config.width, self.config.height), pygame.SRCALPHA
        )

        # Try to get park image
        park_image = None
        if self.image_manager:
            park_image = self.image_manager.get_park_image(park.slug)

        if park_image:
            # Scale to fill screen
            bg_image = pygame.transform.smoothscale(
                park_image, (self.config.width, self.config.height)
            )
            surface.blit(bg_image, (0, 0))
        else:
            # Use gradient fallback
            bg_image = self._create_gradient_background(theme)
            surface.blit(bg_image, (0, 0))

        # Get fonts
        font_park_name = self._get_font(theme, 36)
        font_closed = self._get_font(theme, 80)
        font_opens = self._get_font(theme, 28)
        font_weather = self._get_font("classic", 24)

        # Calculate bar height
        bar_height = 140
        bar_y = self.config.height - bar_height  # Flush with bottom

        # Create full-width semi-transparent bar at bottom
        bar_surface = pygame.Surface((self.config.width, bar_height), pygame.SRCALPHA)
        bar_color = (*colors.background, BOX_ALPHA)
        bar_surface.fill(bar_color)

        # Add accent line at top of bar
        pygame.draw.line(
            bar_surface, (*colors.accent, 255),
            (0, 0), (self.config.width, 0), 3
        )

        surface.blit(bar_surface, (0, bar_y))

        # Weather section width (right side)
        weather_width = 100 if self.weather_data else 0
        content_width = self.config.width - weather_width - 40

        # Render CLOSED (large, on left side)
        closed_color = (231, 76, 60)  # Red
        closed_surface = font_closed.render("CLOSED", True, closed_color)
        closed_x = 30
        closed_y = bar_y + 10
        surface.blit(closed_surface, (closed_x, closed_y))

        # Render park name (left-justified)
        name_surface = font_park_name.render(park.name, True, colors.text_primary)
        name_x = 30  # Left-justified
        name_y = bar_y + 85
        surface.blit(name_surface, (name_x, name_y))

        # Render opens at time (left-justified, below park name)
        if park.opens_at:
            opens_text = f"Opens at {park.opens_at}"
            opens_surface = font_opens.render(opens_text, True, colors.accent)
            opens_x = 30  # Left-justified
            opens_y = bar_y + 115
            surface.blit(opens_surface, (opens_x, opens_y))

        # Render weather (right side, stacked icon + temp)
        if self.weather_data:
            weather_x = self.config.width - weather_width - 10

            # Weather icon
            icon_center_x = weather_x + weather_width // 2
            icon_center_y = bar_y + 45
            self._draw_weather_icon(surface, self.weather_data.icon_code, icon_center_x, icon_center_y, 50)

            # Temperature
            temp_surface = font_weather.render(
                self.weather_data.temp_display, True, colors.text_primary
            )
            temp_x = weather_x + (weather_width - temp_surface.get_width()) // 2
            temp_y = bar_y + 95
            surface.blit(temp_surface, (temp_x, temp_y))

        # Status indicator
        self._render_status_indicator(surface)

        return surface

    def _wrap_text(
        self, text: str, font: pygame.font.Font, max_width: int
    ) -> list[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            try:
                text_width = font.size(test_line)[0]
            except Exception:
                text_width = len(test_line) * 20

            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines if lines else [text]

    def _render_dots(self, surface: pygame.Surface, colors: ColorScheme):
        """Render navigation dots at bottom center."""
        if not self.display_items:
            return

        num_rides = len(self.display_items)
        max_dots = 25

        if num_rides > max_dots:
            visible_dots = max_dots
        else:
            visible_dots = num_rides

        total_width = (visible_dots - 1) * DOT_SPACING
        start_x = (self.config.width - total_width) // 2

        for i in range(visible_dots):
            x = start_x + i * DOT_SPACING

            if num_rides > max_dots:
                half = max_dots // 2
                if self.current_index < half:
                    actual_i = i
                elif self.current_index >= num_rides - half:
                    actual_i = num_rides - max_dots + i
                else:
                    actual_i = self.current_index - half + i
            else:
                actual_i = i

            is_current = actual_i == self.current_index

            if is_current:
                # Active dot - larger and brighter
                pygame.draw.circle(surface, (255, 255, 255), (x, DOT_Y), DOT_RADIUS + 2)
                pygame.draw.circle(surface, colors.accent, (x, DOT_Y), DOT_RADIUS)
            else:
                # Inactive dot - semi-transparent
                dot_surface = pygame.Surface((DOT_RADIUS * 2 + 2, DOT_RADIUS * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(dot_surface, (255, 255, 255, 120), (DOT_RADIUS + 1, DOT_RADIUS + 1), DOT_RADIUS)
                surface.blit(dot_surface, (x - DOT_RADIUS - 1, DOT_Y - DOT_RADIUS - 1))

    def _render_status_indicator(self, surface: pygame.Surface):
        """Render status indicator for stale data or errors."""
        age_minutes = self._get_data_age_minutes()

        if age_minutes > 10 or self.last_error:
            indicator_x = self.config.width - BOX_MARGIN - 15
            indicator_y = BOX_MARGIN + 15

            if self.last_error:
                color = STATUS_ERROR
            else:
                color = STATUS_WARNING

            # Draw warning badge
            badge_surface = pygame.Surface((60, 30), pygame.SRCALPHA)
            pygame.draw.rect(badge_surface, (*color, 200), (0, 0, 60, 30), border_radius=8)

            if age_minutes > 0:
                age_text = f"{age_minutes}m"
                age_font = self.font_small
                text_surface = age_font.render(age_text, True, (0, 0, 0))
                text_rect = text_surface.get_rect(center=(30, 15))
                badge_surface.blit(text_surface, text_rect)

            surface.blit(badge_surface, (indicator_x - 30, indicator_y - 15))

    def _render_event_screen(self, event: ScheduledEvent, elapsed_time: float) -> pygame.Surface:
        """Render a special event screen (fireworks or parade)."""
        colors = get_color_scheme("classic")

        # Create surface
        surface = pygame.Surface(
            (self.config.width, self.config.height), pygame.SRCALPHA
        )

        # Check if we have a video for this event
        video_key = f"{event.park_slug}_{event.event_type.value}"
        video_player = self.event_videos.get(video_key)

        if video_player and video_player.current_frame:
            # Use video playback
            video_player.render(surface)
        else:
            # Fall back to park image + particle animation
            park_image = None
            if self.image_manager:
                park_image = self.image_manager.get_park_image(event.park_slug)

            if park_image:
                bg_image = pygame.transform.smoothscale(
                    park_image, (self.config.width, self.config.height)
                )
                surface.blit(bg_image, (0, 0))
            else:
                bg_image = self._create_gradient_background("classic")
                surface.blit(bg_image, (0, 0))

            # Apply slight darkening for better animation visibility
            dark_overlay = pygame.Surface(
                (self.config.width, self.config.height), pygame.SRCALPHA
            )
            dark_overlay.fill((0, 0, 0, 80))
            surface.blit(dark_overlay, (0, 0))

            # Render the appropriate particle animation
            if event.event_type == EventType.FIREWORKS and self.fireworks_animation:
                self.fireworks_animation.render(surface)
            elif event.event_type == EventType.PARADE and self.parade_animation:
                self.parade_animation.render(surface)

        # Get fonts
        font_event = self._get_font("fantasy", 48)
        font_park = self._get_font("classic", 32)

        # Create bottom info bar
        bar_height = 100
        bar_y = self.config.height - bar_height  # Flush with bottom

        bar_surface = pygame.Surface((self.config.width, bar_height), pygame.SRCALPHA)
        bar_color = (*colors.background, 200)
        bar_surface.fill(bar_color)

        # Accent line
        accent_color = (255, 215, 0) if event.event_type == EventType.FIREWORKS else (255, 105, 180)
        pygame.draw.line(
            bar_surface, (*accent_color, 255),
            (0, 0), (self.config.width, 0), 3
        )

        surface.blit(bar_surface, (0, bar_y))

        # Event name
        if event.event_type == EventType.FIREWORKS:
            event_text = "FIREWORKS"
            event_color = (255, 215, 0)  # Gold
        else:
            event_text = "PARADE"
            event_color = (255, 105, 180)  # Pink

        event_surface = font_event.render(event_text, True, event_color)
        event_x = 30
        event_y = bar_y + 10
        surface.blit(event_surface, (event_x, event_y))

        # Park name
        park_surface = font_park.render(event.park_name, True, colors.text_primary)
        park_x = 30
        park_y = bar_y + 60
        surface.blit(park_surface, (park_x, park_y))

        # Time remaining (right side)
        time_remaining = event.duration_seconds - int(elapsed_time)
        if time_remaining > 0:
            mins = time_remaining // 60
            secs = time_remaining % 60
            time_text = f"{mins}:{secs:02d}"
            font_time = self._get_font("classic", 36)
            time_surface = font_time.render(time_text, True, colors.text_secondary)
            time_x = self.config.width - time_surface.get_width() - 30
            time_y = bar_y + 35
            surface.blit(time_surface, (time_x, time_y))

        # Weather (if available)
        if self.weather_data:
            weather_x = self.config.width - 120
            font_weather_icon = pygame.font.Font(None, 36)
            font_weather = self._get_font("classic", 22)

            icon_surface = font_weather_icon.render(
                self.weather_data.icon, True, colors.text_primary
            )
            icon_x = weather_x
            icon_y = bar_y + 15
            surface.blit(icon_surface, (icon_x, icon_y))

            temp_surface = font_weather.render(
                self.weather_data.temp_display, True, colors.text_primary
            )
            temp_x = weather_x
            temp_y = bar_y + 55
            surface.blit(temp_surface, (temp_x, temp_y))

        return surface

    def _render_no_rides(self) -> pygame.Surface:
        """Render a message when no rides are available."""
        colors = get_color_scheme("classic")

        surface = pygame.Surface(
            (self.config.width, self.config.height), pygame.SRCALPHA
        )

        # Dark gradient background
        surface = self._create_gradient_background("classic")

        message_font = self._get_font("fantasy", 38)
        sub_font = self._get_font("classic", 26)

        # Center message
        message = "No rides currently reporting wait times"
        text_surface = message_font.render(message, True, colors.text_secondary)
        text_rect = text_surface.get_rect(
            center=(self.config.width // 2, self.config.height // 2)
        )
        surface.blit(text_surface, text_rect)

        # Sub-message
        sub_message = "Parks may be closed"
        sub_surface = sub_font.render(sub_message, True, colors.accent)
        sub_rect = sub_surface.get_rect(
            center=(self.config.width // 2, self.config.height // 2 + 50)
        )
        surface.blit(sub_surface, sub_rect)

        # Last update time
        age_minutes = self._get_data_age_minutes()
        if age_minutes >= 0:
            time_text = f"Last updated: {age_minutes} minutes ago"
            time_surface = self.font_small.render(time_text, True, colors.text_secondary)
            time_rect = time_surface.get_rect(
                center=(self.config.width // 2, self.config.height // 2 + 100)
            )
            surface.blit(time_surface, time_rect)

        return surface

    def _render_display_item(self, item) -> pygame.Surface:
        """Render a display item (Ride or ClosedPark)."""
        if isinstance(item, ClosedPark):
            return self._render_closed_park_card(item)
        else:
            return self._render_ride_card(item)

    def _start_transition(self):
        """Begin transition to next item."""
        if len(self.display_items) <= 1:
            return

        self.transitioning = True
        self.transition_progress = 0.0

        self.prev_surface = self._render_display_item(self.display_items[self.current_index])
        self.current_index = (self.current_index + 1) % len(self.display_items)

        # Advance image cycles after completing a full round
        if self.current_index == 0 and self.image_manager:
            self.image_manager.advance_all_cycles()

        self.next_surface = self._render_display_item(self.display_items[self.current_index])

    def _update_transition(self, dt: float):
        """Update transition animation."""
        if not self.transitioning:
            return

        self.transition_progress += dt / self.config.transition_duration

        if self.transition_progress >= 1.0:
            self.transitioning = False
            self.transition_progress = 0.0
            self.prev_surface = None
            self.next_surface = None

    def update(self, dt: float):
        """Update display state."""
        if self.last_data_update:
            age = datetime.now() - self.last_data_update
            self.data_is_stale = age.total_seconds() > 900

        # Check for active events
        if self.event_scheduler:
            current_event = self.event_scheduler.get_active_event()

            if current_event and not self.active_event:
                # Event just started
                self.active_event = current_event
                self.event_start_time = time_module.time()
                # Reset animations and video
                if self.fireworks_animation:
                    self.fireworks_animation.reset()
                if self.parade_animation:
                    self.parade_animation.reset()
                # Reset video player if available
                video_key = f"{current_event.park_slug}_{current_event.event_type.value}"
                if video_key in self.event_videos:
                    self.event_videos[video_key].reset()
                logger.info(f"Event started: {current_event.event_type.value} at {current_event.park_name}")

            elif not current_event and self.active_event:
                # Event just ended
                logger.info(f"Event ended: {self.active_event.event_type.value}")
                self.active_event = None
                self.event_start_time = 0.0

        # Update animations if event is active
        if self.active_event:
            elapsed = time_module.time() - self.event_start_time
            # Check for video first
            video_key = f"{self.active_event.park_slug}_{self.active_event.event_type.value}"
            if video_key in self.event_videos:
                self.event_videos[video_key].update(dt, elapsed)
            elif self.active_event.event_type == EventType.FIREWORKS and self.fireworks_animation:
                self.fireworks_animation.update(dt, elapsed)
            elif self.active_event.event_type == EventType.PARADE and self.parade_animation:
                self.parade_animation.update(dt, elapsed)
            return  # Skip normal ride rotation during events

        if self.transitioning:
            self._update_transition(dt)
        else:
            self.time_on_current += dt
            if self.time_on_current >= self.config.display_duration:
                self.time_on_current = 0.0
                self._start_transition()

    def render(self):
        """Render current frame to screen."""
        if not self.screen:
            return

        try:
            # Check if event is active
            if self.active_event:
                elapsed = time_module.time() - self.event_start_time
                surface = self._render_event_screen(self.active_event, elapsed)
                self.screen.blit(surface, (0, 0))
            elif not self.display_items:
                surface = self._render_no_rides()
                self.screen.blit(surface, (0, 0))
            elif self.transitioning and self.prev_surface and self.next_surface:
                alpha = int(255 * self.transition_progress)
                self.screen.blit(self.prev_surface, (0, 0))
                self.next_surface.set_alpha(alpha)
                self.screen.blit(self.next_surface, (0, 0))
                self.next_surface.set_alpha(255)
            else:
                surface = self._render_display_item(self.display_items[self.current_index])
                self.screen.blit(surface, (0, 0))

            pygame.display.flip()

        except Exception as e:
            logger.error(f"Render error: {e}")
            self._render_error_screen(str(e))

    def _render_error_screen(self, error_message: str):
        """Render an error screen when something goes wrong."""
        try:
            self.screen.fill((30, 0, 0))
            error_font = pygame.font.Font(None, 36)
            text = error_font.render("Display Error", True, STATUS_ERROR)
            text_rect = text.get_rect(
                center=(self.config.width // 2, self.config.height // 2 - 30)
            )
            self.screen.blit(text, text_rect)

            detail_font = pygame.font.Font(None, 24)
            detail = detail_font.render(error_message[:50], True, (200, 200, 200))
            detail_rect = detail.get_rect(
                center=(self.config.width // 2, self.config.height // 2 + 20)
            )
            self.screen.blit(detail, detail_rect)

            pygame.display.flip()
        except Exception:
            pass

    def handle_events(self) -> bool:
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self._start_transition()
                elif event.key == pygame.K_s:
                    self._save_screenshot()

        return True

    def _save_screenshot(self):
        """Save a screenshot of the current display."""
        from pathlib import Path
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)

        # Find next available filename
        i = 1
        while True:
            filename = docs_dir / f"screenshot_{i}.png"
            if not filename.exists():
                break
            i += 1

        pygame.image.save(self.screen, str(filename))
        logger.info(f"Screenshot saved: {filename}")

    def run_loop(self, data: WaitTimesData, refresh_callback=None):
        """Main display loop."""
        self.set_rides(data)
        self.running = True

        logger.info("Starting display loop")

        while self.running:
            try:
                dt = self.clock.tick(self.config.fps) / 1000.0

                if not self.handle_events():
                    self.running = False
                    break

                self.update(dt)
                self.render()

            except Exception as e:
                logger.error(f"Error in display loop: {e}")
                continue

        logger.info("Display loop ended")
