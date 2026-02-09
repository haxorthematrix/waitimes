"""Events module for fireworks and parade scheduling."""

from src.events.scheduler import EventScheduler, ScheduledEvent
from src.events.animations import FireworksAnimation, ParadeAnimation, VideoPlayer

__all__ = [
    "EventScheduler",
    "ScheduledEvent",
    "FireworksAnimation",
    "ParadeAnimation",
    "VideoPlayer",
]
