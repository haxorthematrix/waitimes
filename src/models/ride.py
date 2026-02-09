"""Data models for rides and parks."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Ride:
    """Represents a single ride/attraction."""

    id: int
    name: str
    wait_time: int  # in minutes
    is_open: bool
    park_id: int
    park_name: str
    last_updated: datetime = field(default_factory=datetime.now)

    # Theme information (populated from theme mappings)
    theme_id: Optional[str] = None  # e.g., "space_mountain", "haunted_mansion"

    @property
    def wait_category(self) -> str:
        """Return wait time category for color coding."""
        if self.wait_time <= 20:
            return "short"
        elif self.wait_time <= 45:
            return "moderate"
        elif self.wait_time <= 75:
            return "long"
        else:
            return "very_long"

    @property
    def display_wait(self) -> str:
        """Format wait time for display."""
        if not self.is_open:
            return "Closed"
        if self.wait_time == 0:
            return "Walk On"
        return f"{self.wait_time} min"

    def __repr__(self) -> str:
        return f"Ride({self.name}, {self.display_wait}, {self.park_name})"


@dataclass
class Park:
    """Represents a Disney park."""

    id: int
    name: str
    slug: str  # e.g., "magic_kingdom"
    rides: list[Ride] = field(default_factory=list)
    last_updated: Optional[datetime] = None

    @property
    def open_rides(self) -> list[Ride]:
        """Return only rides that are currently open with wait times."""
        return [r for r in self.rides if r.is_open and r.wait_time > 0]

    def __repr__(self) -> str:
        return f"Park({self.name}, {len(self.rides)} rides)"


@dataclass
class WaitTimesData:
    """Container for all wait times data."""

    parks: dict[str, Park] = field(default_factory=dict)
    last_fetch: Optional[datetime] = None
    fetch_success: bool = False
    error_message: Optional[str] = None

    @property
    def all_open_rides(self) -> list[Ride]:
        """Get all open rides across all parks, sorted by park then wait time."""
        rides = []
        for park in self.parks.values():
            rides.extend(park.open_rides)
        # Sort by park name, then by wait time descending
        return sorted(rides, key=lambda r: (r.park_name, -r.wait_time))

    @property
    def is_stale(self) -> bool:
        """Check if data is more than 15 minutes old."""
        if self.last_fetch is None:
            return True
        age = datetime.now() - self.last_fetch
        return age.total_seconds() > 900  # 15 minutes

    @property
    def age_minutes(self) -> int:
        """Return age of data in minutes."""
        if self.last_fetch is None:
            return -1
        age = datetime.now() - self.last_fetch
        return int(age.total_seconds() / 60)
