"""Example bot implementation: cabello.

This bot moves horizontally across the arena, oscillating between east
and west.  It continually rotates its cannon and maintains a wide
scan arc until a target is detected.  Upon detection it narrows its
scan arc and begins firing while rotating the cannon slowly.  When
approaching the arena walls it pauses briefly before reversing
direction.
"""

from __future__ import annotations

import random
from pythonbots.constants import (
    PI,
    VISION_RANGE,
    DANGEROUS_TEMPERATURE,
    HEAT_PER_SHOT,
    MAX_TURN_RATE,
    ARENA_WIDTH,
    RADIUS,
)


moving_right: bool = False
wait_counter: int = 30


def cabello(handler: "pythonbots.bot.Handler") -> None:
    """Control function for the cabello bot."""
    global moving_right, wait_counter

    # Align body direction to either 0 (east) or π (west)
    # If the heading deviates more than ~0.1 rad, rotate towards the closest axis
    direction = handler.get_direction()
    if direction > 0.1 or direction < -0.1:
        if direction < 0:
            handler.turn(min(MAX_TURN_RATE, -direction))
        else:
            handler.turn(max(-MAX_TURN_RATE, -direction))

    # Scan for enemies
    distance, _ = handler.scan()
    if distance < VISION_RANGE:
        # Rotate the cannon slowly and fire if cool enough
        handler.rotate_cannon(0.01)
        if handler.get_temperature() < DANGEROUS_TEMPERATURE - HEAT_PER_SHOT:
            handler.shoot()
        # Narrow the scan arc to focus on the target
        handler.set_arc(handler.get_arc() - 0.05)
    else:
        # Restore a moderate scan arc and keep moving horizontally
        handler.set_arc(PI / 4.0)
        handler.accelerate(0.5 if moving_right else -0.5)
        handler.rotate_cannon(0.05)

    # Countdown until it is time to check wall proximity
    wait_counter = wait_counter - 1 if wait_counter > 0 else 0
    pos = handler.get_position()
    if wait_counter == 0 and (pos.x >= ARENA_WIDTH - (RADIUS * 2) or pos.x <= RADIUS * 2):
        # Turn around and reset the wait counter
        moving_right = not moving_right
        wait_counter = 30