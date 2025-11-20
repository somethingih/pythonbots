"""Example bot implementation: snitram.

This bot moves erratically with a constant forward acceleration and
rotates its cannon rapidly.  It maintains a fixed scan arc while
searching.  Upon detecting an enemy it slows the cannon rotation and
begins firing continuously.  When it bumps into a wall it reverses
direction for a short time to avoid getting stuck.
"""

from __future__ import annotations

from pythonbots.constants import (
    PI,
    VISION_RANGE,
    DANGEROUS_TEMPERATURE,
    HEAT_PER_SHOT,
    ARENA_WIDTH,
    ARENA_HEIGHT,
    RADIUS,
)


wait_counter: int = 0


def snitram(handler: "pythonbots.bot.Handler") -> None:
    """Control function for the snitram bot."""
    global wait_counter
    distance, _ = handler.scan()
    if distance < VISION_RANGE:
        # Target detected: slow the cannon and fire continuously
        handler.rotate_cannon(0.01)
        if handler.get_temperature() < DANGEROUS_TEMPERATURE - HEAT_PER_SHOT:
            handler.shoot()
    else:
        # Sweep with a wide arc and move quickly forward while rotating
        handler.set_arc(PI / 8.0)
        handler.accelerate(0.8)
        handler.turn(0.002)
        handler.rotate_cannon(0.05)
    # Countdown for collision handling
    wait_counter = wait_counter - 1 if wait_counter > 0 else 0
    pos = handler.get_position()
    # If time elapsed and we are near a wall, reverse direction
    if wait_counter == 0 and (
        pos.x >= ARENA_WIDTH - (RADIUS * 2)
        or pos.x <= RADIUS * 2
        or pos.y >= ARENA_HEIGHT - (RADIUS * 2)
        or pos.y <= RADIUS * 2
    ):
        wait_counter = 100
        handler.accelerate(-1.0)
        handler.turn(PI)