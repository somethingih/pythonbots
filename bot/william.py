"""Example bot implementation: william.

This bot alternates between scanning for targets and adjusting its
heading to face potential threats.  When a target is detected it
accelerates toward it, fires and narrows its scan arc.  If no target
is detected it slowly rotates and accelerates with varying thrust to
search the arena.  After bumping into a wall or taking a hit it
performs evasive manoeuvres.
"""

from __future__ import annotations

import random

from pythonbots.constants import (
    PI,
    VISION_RANGE,
    DANGEROUS_TEMPERATURE,
    HEAT_PER_SHOT,
    MAX_TURN_RATE,
    MAX_ACCELERATION,
    RADIUS,
    ARENA_WIDTH,
    ARENA_HEIGHT,
    SHOT_DAMAGE,
)


state: str = 'searching'
thrust: float = 0.01
count: int = 10
wait_timer: int = 10
last_health: float = 0.0


def william(handler: "pythonbots.bot.Handler") -> None:
    """Control function for the william bot."""
    global state, thrust, count, wait_timer, last_health

    distance, _ = handler.scan()
    # Target detected
    if distance < VISION_RANGE:
        if handler.get_temperature() < DANGEROUS_TEMPERATURE - HEAT_PER_SHOT:
            handler.shoot()
        handler.set_arc(handler.get_arc() - 0.01)
        handler.accelerate(0.6 if distance > VISION_RANGE / 2.0 else 0.4)
        state = 'locked'
    elif state == 'locked':
        # Lost the target, begin searching to the right
        state = 'try-right'

    # Handle turning states
    if state == 'try-right':
        if count - 1 > 0:
            count -= 1
            handler.turn(MAX_TURN_RATE / 2.0)
        else:
            state = 'try-left'
            count = 10
    elif state == 'try-left':
        if count + 9 > 0:
            count -= 1
            handler.turn(-MAX_TURN_RATE / 2.0)
        else:
            state = 'searching'
            count = 10

    if state == 'searching':
        # Rotate slowly while accelerating at a varying rate
        handler.turn(MAX_TURN_RATE / 6.0)
        handler.accelerate(thrust)
        # Pulse between slow and fast thrust
        thrust = 0.1 if thrust >= MAX_ACCELERATION / 2.0 else 0.002
        handler.set_arc(0.5)

    # Countdown for collision handling
    wait_timer = wait_timer - 1 if wait_timer > 0 else 0

    pos = handler.get_position()
    if wait_timer == 0 and (
        pos.x >= ARENA_WIDTH - (RADIUS * 2)
        or pos.x <= RADIUS * 2
        or pos.y >= ARENA_HEIGHT - (RADIUS * 2)
        or pos.y <= RADIUS * 2
    ):
        # Bounce off a wall: turn around and reset timer
        wait_timer = int(PI / MAX_TURN_RATE) * 2
        handler.turn(random.choice([PI, -PI]))
    elif wait_timer == 0 and handler.get_health() <= last_health - SHOT_DAMAGE:
        # Took a hit: surge forward briefly
        thrust = MAX_ACCELERATION / 2.5
        wait_timer = 100

    # Remember health for next tick
    last_health = handler.get_health()