"""Animation overlays for fireworks and parades."""

import math
import random
from dataclasses import dataclass, field
from typing import Optional

import pygame

from src.utils.logging_config import get_logger


@dataclass
class Particle:
    """A single particle in an animation."""

    x: float
    y: float
    vx: float
    vy: float
    color: tuple[int, int, int]
    life: float  # 0.0 to 1.0
    size: float
    decay: float


@dataclass
class Firework:
    """A firework that explodes into particles."""

    x: float
    y: float
    target_y: float
    vy: float
    color: tuple[int, int, int]
    exploded: bool = False
    particles: list[Particle] = field(default_factory=list)


class FireworksAnimation:
    """Animated fireworks display overlay."""

    # Firework colors (bright, celebratory)
    COLORS = [
        (255, 215, 0),    # Gold
        (255, 105, 180),  # Hot pink
        (0, 255, 255),    # Cyan
        (255, 69, 0),     # Red-orange
        (50, 205, 50),    # Lime green
        (255, 255, 255),  # White
        (147, 112, 219),  # Purple
        (255, 165, 0),    # Orange
    ]

    def __init__(self, width: int, height: int):
        """Initialize fireworks animation.

        Args:
            width: Display width
            height: Display height
        """
        self.logger = get_logger(__name__)
        self.width = width
        self.height = height
        self.fireworks: list[Firework] = []
        self.last_launch = 0.0
        self.launch_interval = 0.3  # Seconds between launches
        self.gravity = 0.15

    def update(self, dt: float, elapsed_time: float) -> None:
        """Update animation state.

        Args:
            dt: Delta time since last frame (seconds)
            elapsed_time: Total elapsed time since animation start
        """
        # Launch new fireworks periodically
        if elapsed_time - self.last_launch > self.launch_interval:
            self._launch_firework()
            self.last_launch = elapsed_time
            # Vary launch interval for more natural effect
            self.launch_interval = random.uniform(0.2, 0.6)

        # Update existing fireworks
        for fw in self.fireworks[:]:
            if not fw.exploded:
                # Move firework upward
                fw.y += fw.vy * dt * 60
                fw.vy += self.gravity * 0.3  # Slow down

                # Explode when reaching target
                if fw.y <= fw.target_y or fw.vy >= 0:
                    self._explode(fw)
            else:
                # Update particles
                for p in fw.particles[:]:
                    p.x += p.vx * dt * 60
                    p.y += p.vy * dt * 60
                    p.vy += self.gravity
                    p.life -= p.decay * dt * 60

                    if p.life <= 0:
                        fw.particles.remove(p)

                # Remove firework when all particles are gone
                if not fw.particles:
                    self.fireworks.remove(fw)

    def _launch_firework(self) -> None:
        """Launch a new firework from the bottom."""
        x = random.randint(int(self.width * 0.1), int(self.width * 0.9))
        color = random.choice(self.COLORS)
        target_y = random.randint(int(self.height * 0.15), int(self.height * 0.4))

        self.fireworks.append(
            Firework(
                x=x,
                y=self.height + 10,
                target_y=target_y,
                vy=-random.uniform(12, 16),
                color=color,
            )
        )

    def _explode(self, fw: Firework) -> None:
        """Create explosion particles for a firework."""
        fw.exploded = True
        num_particles = random.randint(60, 100)

        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            # Slight color variation
            color = tuple(
                max(0, min(255, c + random.randint(-30, 30))) for c in fw.color
            )

            fw.particles.append(
                Particle(
                    x=fw.x,
                    y=fw.y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    color=color,
                    life=1.0,
                    size=random.uniform(2, 4),
                    decay=random.uniform(0.01, 0.025),
                )
            )

    def render(self, surface: pygame.Surface) -> None:
        """Render fireworks onto surface.

        Args:
            surface: Pygame surface to render onto
        """
        for fw in self.fireworks:
            if not fw.exploded:
                # Draw rising firework as a small bright dot
                pygame.draw.circle(surface, fw.color, (int(fw.x), int(fw.y)), 3)
                # Trail effect
                trail_color = tuple(c // 2 for c in fw.color)
                pygame.draw.circle(
                    surface, trail_color, (int(fw.x), int(fw.y + 5)), 2
                )
            else:
                # Draw particles
                for p in fw.particles:
                    alpha = int(p.life * 255)
                    color = tuple(int(c * p.life) for c in p.color)
                    size = int(p.size * p.life)
                    if size > 0:
                        pygame.draw.circle(
                            surface, color, (int(p.x), int(p.y)), max(1, size)
                        )

    def reset(self) -> None:
        """Reset animation state."""
        self.fireworks.clear()
        self.last_launch = 0.0


@dataclass
class FloatingElement:
    """A floating element in parade animation (balloon, confetti, etc.)."""

    x: float
    y: float
    vx: float
    vy: float
    color: tuple[int, int, int]
    element_type: str  # "balloon", "confetti", "star"
    size: float
    rotation: float = 0.0
    rotation_speed: float = 0.0


class ParadeAnimation:
    """Animated parade celebration overlay."""

    # Parade colors (festive, bright)
    COLORS = [
        (255, 0, 0),      # Red
        (255, 165, 0),    # Orange
        (255, 255, 0),    # Yellow
        (0, 255, 0),      # Green
        (0, 191, 255),    # Deep sky blue
        (138, 43, 226),   # Blue violet
        (255, 20, 147),   # Deep pink
        (255, 215, 0),    # Gold
    ]

    def __init__(self, width: int, height: int):
        """Initialize parade animation.

        Args:
            width: Display width
            height: Display height
        """
        self.logger = get_logger(__name__)
        self.width = width
        self.height = height
        self.elements: list[FloatingElement] = []
        self.spawn_timer = 0.0
        self.spawn_interval = 0.1
        self.banner_offset = 0.0
        self.sparkle_timer = 0.0

    def update(self, dt: float, elapsed_time: float) -> None:
        """Update animation state.

        Args:
            dt: Delta time since last frame (seconds)
            elapsed_time: Total elapsed time since animation start
        """
        # Update banner scroll
        self.banner_offset = (elapsed_time * 50) % self.width

        # Spawn new elements
        self.spawn_timer += dt
        if self.spawn_timer > self.spawn_interval:
            self._spawn_element()
            self.spawn_timer = 0.0
            self.spawn_interval = random.uniform(0.05, 0.15)

        # Update sparkle timer
        self.sparkle_timer = elapsed_time

        # Update existing elements
        for elem in self.elements[:]:
            elem.x += elem.vx * dt * 60
            elem.y += elem.vy * dt * 60
            elem.rotation += elem.rotation_speed * dt * 60

            # Add slight wave motion to balloons
            if elem.element_type == "balloon":
                elem.x += math.sin(elapsed_time * 2 + elem.y * 0.05) * 0.5

            # Remove off-screen elements
            if (
                elem.x < -50
                or elem.x > self.width + 50
                or elem.y < -50
                or elem.y > self.height + 50
            ):
                self.elements.remove(elem)

    def _spawn_element(self) -> None:
        """Spawn a new floating element."""
        element_type = random.choices(
            ["balloon", "confetti", "star"],
            weights=[0.3, 0.5, 0.2],
        )[0]

        color = random.choice(self.COLORS)

        if element_type == "balloon":
            # Balloons rise from bottom
            self.elements.append(
                FloatingElement(
                    x=random.randint(0, self.width),
                    y=self.height + 20,
                    vx=random.uniform(-0.5, 0.5),
                    vy=random.uniform(-3, -1.5),
                    color=color,
                    element_type="balloon",
                    size=random.uniform(15, 25),
                )
            )
        elif element_type == "confetti":
            # Confetti falls from top
            self.elements.append(
                FloatingElement(
                    x=random.randint(0, self.width),
                    y=-10,
                    vx=random.uniform(-1, 1),
                    vy=random.uniform(2, 4),
                    color=color,
                    element_type="confetti",
                    size=random.uniform(6, 12),
                    rotation_speed=random.uniform(-5, 5),
                )
            )
        else:  # star
            # Stars twinkle across screen
            self.elements.append(
                FloatingElement(
                    x=random.randint(0, self.width),
                    y=random.randint(0, int(self.height * 0.6)),
                    vx=0,
                    vy=0,
                    color=(255, 255, 200),
                    element_type="star",
                    size=random.uniform(3, 8),
                )
            )

    def render(self, surface: pygame.Surface) -> None:
        """Render parade effects onto surface.

        Args:
            surface: Pygame surface to render onto
        """
        # Draw floating elements
        for elem in self.elements:
            if elem.element_type == "balloon":
                self._draw_balloon(surface, elem)
            elif elem.element_type == "confetti":
                self._draw_confetti(surface, elem)
            elif elem.element_type == "star":
                self._draw_star(surface, elem)

        # Draw sparkle banner at top
        self._draw_banner(surface)

    def _draw_balloon(self, surface: pygame.Surface, elem: FloatingElement) -> None:
        """Draw a balloon."""
        x, y = int(elem.x), int(elem.y)
        size = int(elem.size)

        # Balloon body (oval)
        pygame.draw.ellipse(
            surface,
            elem.color,
            (x - size // 2, y - size, size, int(size * 1.3)),
        )

        # Highlight
        highlight_color = tuple(min(255, c + 80) for c in elem.color)
        pygame.draw.ellipse(
            surface,
            highlight_color,
            (x - size // 4, y - size + 5, size // 3, size // 3),
        )

        # String
        pygame.draw.line(
            surface, (150, 150, 150), (x, y + int(size * 0.3)), (x, y + size), 1
        )

    def _draw_confetti(self, surface: pygame.Surface, elem: FloatingElement) -> None:
        """Draw a piece of confetti."""
        x, y = int(elem.x), int(elem.y)
        size = int(elem.size)

        # Rotate rectangle
        angle = elem.rotation
        points = []
        for dx, dy in [(-1, -0.5), (1, -0.5), (1, 0.5), (-1, 0.5)]:
            rx = dx * size * math.cos(angle) - dy * size * math.sin(angle)
            ry = dx * size * math.sin(angle) + dy * size * math.cos(angle)
            points.append((x + rx, y + ry))

        pygame.draw.polygon(surface, elem.color, points)

    def _draw_star(self, surface: pygame.Surface, elem: FloatingElement) -> None:
        """Draw a twinkling star."""
        x, y = int(elem.x), int(elem.y)
        size = int(elem.size)

        # Twinkle effect based on time
        twinkle = (math.sin(self.sparkle_timer * 8 + elem.x + elem.y) + 1) / 2
        if twinkle < 0.3:
            return  # Star is "off"

        alpha = int(twinkle * 255)
        color = tuple(int(c * twinkle) for c in elem.color)

        # Draw star shape (simple cross pattern)
        pygame.draw.line(surface, color, (x - size, y), (x + size, y), 2)
        pygame.draw.line(surface, color, (x, y - size), (x, y + size), 2)
        # Diagonal lines (smaller)
        half = size // 2
        pygame.draw.line(surface, color, (x - half, y - half), (x + half, y + half), 1)
        pygame.draw.line(surface, color, (x - half, y + half), (x + half, y - half), 1)

    def _draw_banner(self, surface: pygame.Surface) -> None:
        """Draw sparkling banner at top of screen."""
        banner_height = 40
        num_sparkles = 20

        for i in range(num_sparkles):
            x = int((i * self.width / num_sparkles + self.banner_offset) % self.width)
            y = int(banner_height / 2 + math.sin(self.sparkle_timer * 4 + i) * 10)

            # Sparkle intensity varies
            intensity = (math.sin(self.sparkle_timer * 6 + i * 0.5) + 1) / 2
            if intensity > 0.5:
                color = (
                    int(255 * intensity),
                    int(215 * intensity),
                    int(50 * intensity),
                )
                size = int(3 + intensity * 3)
                pygame.draw.circle(surface, color, (x, y), size)

    def reset(self) -> None:
        """Reset animation state."""
        self.elements.clear()
        self.spawn_timer = 0.0
        self.banner_offset = 0.0


class VideoPlayer:
    """Plays video files with looping support using OpenCV."""

    def __init__(self, width: int, height: int):
        """Initialize video player.

        Args:
            width: Display width
            height: Display height
        """
        self.logger = get_logger(__name__)
        self.width = width
        self.height = height
        self.cap = None
        self.current_video_path: Optional[str] = None
        self.fps = 30
        self.frame_duration = 1.0 / 30
        self.last_frame_time = 0.0
        self.current_frame: Optional[pygame.Surface] = None

    def load(self, video_path: str) -> bool:
        """Load a video file.

        Args:
            video_path: Path to video file

        Returns:
            True if loaded successfully
        """
        try:
            import cv2
        except ImportError:
            self.logger.error("OpenCV not installed. Run: pip install opencv-python-headless")
            return False

        try:
            self.cap = cv2.VideoCapture(video_path)
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open video: {video_path}")
                return False

            self.current_video_path = video_path
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.frame_duration = 1.0 / self.fps
            self.last_frame_time = 0.0

            # Read first frame
            self._read_next_frame()
            self.logger.info(f"Loaded video: {video_path} ({self.fps:.1f} fps)")
            return True

        except Exception as e:
            self.logger.error(f"Error loading video: {e}")
            return False

    def _read_next_frame(self) -> bool:
        """Read the next frame from the video.

        Returns:
            True if frame was read, False if video ended
        """
        try:
            import cv2
        except ImportError:
            return False

        if self.cap is None:
            return False

        ret, frame = self.cap.read()
        if not ret:
            # Loop back to beginning
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                return False

        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize to display size
        frame = cv2.resize(frame, (self.width, self.height))

        # Convert to pygame surface
        self.current_frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        return True

    def update(self, dt: float, elapsed_time: float) -> None:
        """Update video playback.

        Args:
            dt: Delta time since last frame
            elapsed_time: Total elapsed time since video start
        """
        # Check if it's time for next frame
        if elapsed_time - self.last_frame_time >= self.frame_duration:
            self._read_next_frame()
            self.last_frame_time = elapsed_time

    def render(self, surface: pygame.Surface) -> None:
        """Render current frame to surface.

        Args:
            surface: Pygame surface to render onto
        """
        if self.current_frame:
            surface.blit(self.current_frame, (0, 0))

    def reset(self) -> None:
        """Reset video to beginning."""
        if self.cap:
            try:
                import cv2
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self._read_next_frame()
            except Exception:
                pass
        self.last_frame_time = 0.0

    def release(self) -> None:
        """Release video resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.current_frame = None
        self.current_video_path = None
