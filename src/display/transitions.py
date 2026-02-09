"""Transition effects for display animations."""

from enum import Enum
from typing import Callable

import pygame


class TransitionType(Enum):
    """Available transition types."""

    CROSSFADE = "crossfade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"


def crossfade(
    prev_surface: pygame.Surface,
    next_surface: pygame.Surface,
    progress: float,
    target: pygame.Surface,
):
    """Crossfade between two surfaces.

    Args:
        prev_surface: The outgoing surface
        next_surface: The incoming surface
        progress: Transition progress from 0.0 to 1.0
        target: Surface to render the result to
    """
    target.blit(prev_surface, (0, 0))
    alpha = int(255 * progress)
    next_surface.set_alpha(alpha)
    target.blit(next_surface, (0, 0))
    next_surface.set_alpha(255)


def slide_left(
    prev_surface: pygame.Surface,
    next_surface: pygame.Surface,
    progress: float,
    target: pygame.Surface,
    width: int,
):
    """Slide transition from right to left.

    Args:
        prev_surface: The outgoing surface
        next_surface: The incoming surface
        progress: Transition progress from 0.0 to 1.0
        target: Surface to render the result to
        width: Screen width for calculating offset
    """
    offset = int(width * progress)
    target.blit(prev_surface, (-offset, 0))
    target.blit(next_surface, (width - offset, 0))


def ease_in_out(t: float) -> float:
    """Smooth easing function for transitions.

    Args:
        t: Linear progress from 0.0 to 1.0

    Returns:
        Eased progress value
    """
    if t < 0.5:
        return 2 * t * t
    return 1 - pow(-2 * t + 2, 2) / 2


def get_transition_func(
    transition_type: TransitionType,
) -> Callable:
    """Get the transition function for a given type.

    Args:
        transition_type: The type of transition

    Returns:
        Transition function
    """
    transitions = {
        TransitionType.CROSSFADE: crossfade,
        TransitionType.SLIDE_LEFT: slide_left,
    }
    return transitions.get(transition_type, crossfade)
