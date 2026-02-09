"""Main display renderer for wait times."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pygame

from src.models.ride import Ride, WaitTimesData, ClosedPark
from src.themes.colors import get_color_scheme, get_wait_color, ColorScheme
from src.themes.fonts import get_font_manager, FontManager
from src.themes.images import get_image_manager, ImageManager

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

    def _get_data_age_minutes(self) -> int:
        """Get age of current data in minutes."""
        if self.last_data_update is None:
            return -1
        age = datetime.now() - self.last_data_update
        return int(age.total_seconds() / 60)

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

        # Calculate bar height based on content (smaller without park name)
        bar_height = 130
        bar_y = self.config.height - bar_height - 10

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

        # Render wait time (large, centered, at top of bar)
        wait_color = get_wait_color(ride.wait_category)
        wait_surface = font_wait_time.render(ride.display_wait, True, wait_color)
        wait_x = (self.config.width - wait_surface.get_width()) // 2
        wait_y = bar_y + 10
        surface.blit(wait_surface, (wait_x, wait_y))

        # Render ride name (centered, below wait time with more spacing)
        name_surface = font_ride_name.render(ride.name, True, colors.text_primary)
        # Truncate if too long
        if name_surface.get_width() > self.config.width - 40:
            # Try to fit by truncating
            truncated = ride.name
            while name_surface.get_width() > self.config.width - 40 and len(truncated) > 10:
                truncated = truncated[:-4] + "..."
                name_surface = font_ride_name.render(truncated, True, colors.text_primary)
        name_x = (self.config.width - name_surface.get_width()) // 2
        name_y = bar_y + 90
        surface.blit(name_surface, (name_x, name_y))

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

        # Calculate bar height
        bar_height = 140
        bar_y = self.config.height - bar_height - 10

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

        # Render CLOSED (large, centered, in red)
        closed_color = (231, 76, 60)  # Red
        closed_surface = font_closed.render("CLOSED", True, closed_color)
        closed_x = (self.config.width - closed_surface.get_width()) // 2
        closed_y = bar_y + 10
        surface.blit(closed_surface, (closed_x, closed_y))

        # Render park name (centered, below CLOSED)
        name_surface = font_park_name.render(park.name, True, colors.text_primary)
        name_x = (self.config.width - name_surface.get_width()) // 2
        name_y = bar_y + 85
        surface.blit(name_surface, (name_x, name_y))

        # Render opens at time (centered, below park name)
        if park.opens_at:
            opens_text = f"Opens at {park.opens_at}"
            opens_surface = font_opens.render(opens_text, True, colors.accent)
            opens_x = (self.config.width - opens_surface.get_width()) // 2
            opens_y = bar_y + 115
            surface.blit(opens_surface, (opens_x, opens_y))

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
            if not self.display_items:
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

        return True

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
