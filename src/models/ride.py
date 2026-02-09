"""Data models for rides and parks."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# TEST MODE: Set park slugs to simulate as closed (empty list = normal operation)
# Examples: ["magic_kingdom"], ["magic_kingdom", "epcot"], ["magic_kingdom", "epcot", "hollywood_studios", "animal_kingdom"]
TEST_CLOSED_PARKS: list[str] = []


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
class ClosedPark:
    """Represents a closed park for display purposes."""

    name: str
    slug: str  # e.g., "magic_kingdom"
    opens_at: Optional[str] = None  # e.g., "9:00 AM"

    @property
    def is_closed_park(self) -> bool:
        """Marker to identify this as a closed park display item."""
        return True

    def __repr__(self) -> str:
        return f"ClosedPark({self.name}, opens: {self.opens_at})"


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

    @property
    def closed_parks(self) -> list[ClosedPark]:
        """Get parks that have no open rides (likely closed)."""
        # Typical park opening times (Eastern Time)
        default_opens = {
            "magic_kingdom": "9:00 AM",
            "epcot": "9:00 AM",
            "hollywood_studios": "8:30 AM",
            "animal_kingdom": "8:00 AM",
        }

        closed = []
        for slug, park in self.parks.items():
            # Check if park is actually closed OR in test mode
            is_closed = not park.open_rides or slug in TEST_CLOSED_PARKS
            if is_closed:
                opens_at = default_opens.get(slug, "9:00 AM")
                closed.append(ClosedPark(
                    name=park.name,
                    slug=slug,
                    opens_at=opens_at
                ))
        return closed

    def get_display_items(self) -> list:
        """Get all items to display: open rides + closed parks."""
        items = []
        # Add open rides (excluding test-closed parks)
        for ride in self.all_open_rides:
            # Check if this ride's park is in test closed mode
            park_slug = None
            for slug, park in self.parks.items():
                if park.name == ride.park_name:
                    park_slug = slug
                    break
            if park_slug not in TEST_CLOSED_PARKS:
                items.append(ride)
        # Add closed parks
        items.extend(self.closed_parks)
        return items
