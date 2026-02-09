"""Event scheduler for fireworks and parades."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Optional
import re

from src.utils.logging_config import get_logger


class EventType(Enum):
    FIREWORKS = "fireworks"
    PARADE = "parade"


@dataclass
class ScheduledEvent:
    """Represents a scheduled event (fireworks or parade)."""

    event_type: EventType
    park_name: str
    park_slug: str
    start_time: time
    duration_seconds: int

    def is_active_at(self, check_time: datetime) -> bool:
        """Check if this event is active at the given time."""
        event_start = datetime.combine(check_time.date(), self.start_time)
        event_end = event_start + timedelta(seconds=self.duration_seconds)
        return event_start <= check_time < event_end

    def time_remaining(self, check_time: datetime) -> int:
        """Return seconds remaining in this event, or 0 if not active."""
        if not self.is_active_at(check_time):
            return 0
        event_start = datetime.combine(check_time.date(), self.start_time)
        event_end = event_start + timedelta(seconds=self.duration_seconds)
        return int((event_end - check_time).total_seconds())

    def elapsed_seconds(self, check_time: datetime) -> int:
        """Return seconds elapsed since event start, or 0 if not active."""
        if not self.is_active_at(check_time):
            return 0
        event_start = datetime.combine(check_time.date(), self.start_time)
        return int((check_time - event_start).total_seconds())


# Mapping from config park names to display names and slugs
PARK_MAPPING = {
    "magic_kingdom": ("Magic Kingdom", "magic-kingdom"),
    "epcot": ("EPCOT", "epcot"),
    "hollywood_studios": ("Hollywood Studios", "hollywood-studios"),
    "animal_kingdom": ("Animal Kingdom", "animal-kingdom"),
}


class EventScheduler:
    """Manages scheduled events for all parks."""

    def __init__(self, config: dict):
        """Initialize scheduler with events configuration.

        Args:
            config: Events configuration dict from config.yaml
        """
        self.logger = get_logger(__name__)
        self.events: list[ScheduledEvent] = []
        self._parse_config(config)

    def _parse_config(self, config: dict) -> None:
        """Parse events configuration into scheduled events."""
        # Parse fireworks
        fireworks_config = config.get("fireworks", {})
        if fireworks_config.get("enabled", False):
            duration = fireworks_config.get("duration", 240)  # 4 minutes default
            schedule = fireworks_config.get("schedule", {})

            for park_key, times in schedule.items():
                if park_key not in PARK_MAPPING:
                    self.logger.warning(f"Unknown park in fireworks schedule: {park_key}")
                    continue

                park_name, park_slug = PARK_MAPPING[park_key]
                for time_str in times:
                    event_time = self._parse_time(time_str)
                    if event_time:
                        self.events.append(
                            ScheduledEvent(
                                event_type=EventType.FIREWORKS,
                                park_name=park_name,
                                park_slug=park_slug,
                                start_time=event_time,
                                duration_seconds=duration,
                            )
                        )
                        self.logger.info(
                            f"Scheduled fireworks: {park_name} at {time_str} ({duration}s)"
                        )

        # Parse parades
        parade_config = config.get("parades", {})
        if parade_config.get("enabled", False):
            duration = parade_config.get("duration", 120)  # 2 minutes default
            schedule = parade_config.get("schedule", {})

            for park_key, times in schedule.items():
                if park_key not in PARK_MAPPING:
                    self.logger.warning(f"Unknown park in parade schedule: {park_key}")
                    continue

                park_name, park_slug = PARK_MAPPING[park_key]
                for time_str in times:
                    event_time = self._parse_time(time_str)
                    if event_time:
                        self.events.append(
                            ScheduledEvent(
                                event_type=EventType.PARADE,
                                park_name=park_name,
                                park_slug=park_slug,
                                start_time=event_time,
                                duration_seconds=duration,
                            )
                        )
                        self.logger.info(
                            f"Scheduled parade: {park_name} at {time_str} ({duration}s)"
                        )

    def _parse_time(self, time_str: str) -> Optional[time]:
        """Parse time string in HH:MM format."""
        match = re.match(r"(\d{1,2}):(\d{2})", time_str)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)
        self.logger.warning(f"Invalid time format: {time_str}")
        return None

    def get_active_event(self, check_time: Optional[datetime] = None) -> Optional[ScheduledEvent]:
        """Get the currently active event, if any.

        Args:
            check_time: Time to check (defaults to now)

        Returns:
            Active ScheduledEvent or None
        """
        if check_time is None:
            check_time = datetime.now()

        for event in self.events:
            if event.is_active_at(check_time):
                return event
        return None

    def get_next_event(self, check_time: Optional[datetime] = None) -> Optional[tuple[ScheduledEvent, int]]:
        """Get the next upcoming event and seconds until it starts.

        Args:
            check_time: Time to check from (defaults to now)

        Returns:
            Tuple of (event, seconds_until_start) or None
        """
        if check_time is None:
            check_time = datetime.now()

        next_event = None
        min_seconds = float("inf")

        for event in self.events:
            event_start = datetime.combine(check_time.date(), event.start_time)

            # If event already passed today, check tomorrow
            if event_start <= check_time:
                event_start = datetime.combine(
                    check_time.date() + timedelta(days=1), event.start_time
                )

            seconds_until = (event_start - check_time).total_seconds()
            if seconds_until < min_seconds:
                min_seconds = seconds_until
                next_event = event

        if next_event:
            return (next_event, int(min_seconds))
        return None
