"""Example bot implementation: bigodines.

This bot roams the arena at a steady pace while periodically rotating
its body.  When an enemy is detected it stops, narrows its scan arc
and attempts to lock on to the target before firing.  If it takes
damage it assumes the attack came from the direction of its cannon
and accelerates away to avoid the shot stream.  It also tries to
avoid walls by turning when it gets too close to the arena edges.

The original version of this bot used Portuguese variable names and
relied on the backwards‑compatibility API.  This rewrite uses only
English names and the modern :class:`pythonbots.bot.Handler` API.
"""

from __future__ import annotations

import random
from pythonbots.constants import (
    PI,
    TAU,
    VISION_RANGE,
    MIN_SCAN_ARC,
    DANGEROUS_TEMPERATURE,
    HEAT_PER_SHOT,
    MAX_TURN_RATE,
    MAX_ACCELERATION,
    RADIUS,
    ARENA_WIDTH,
    ARENA_HEIGHT,
)
from pythonbots.constants import velocity_heat


# Module‑level state.  Bots in this game are expected to maintain
# persistent variables between ticks via module globals.  Each bot
# function is loaded in its own module so there is no interference.
last_health: float = 0.0
target_locked: bool = False
turn_rate: float = 0.1


def bigodines(handler: "pythonbots.bot.Handler") -> None:
    """Control function for the bigodines bot.

    The ``handler`` exposes methods to read the bot's state and issue
    commands.  See ``pythonbots.constants`` for definitions of the
    constants used here.
    """
    global last_health, target_locked, turn_rate

    # If health increased (e.g. from a bug or negative damage) rotate
    # the cannon 90 degrees.  This behaviour has no strategic impact
    # but mirrors the original implementation.
    if handler.get_health() > last_health:
        handler.rotate_cannon(PI / 2.0)

    # Scan for enemies
    distance, _ = handler.scan()

    if distance < VISION_RANGE:
        # Enemy detected – lock on and narrow scan arc
        target_locked = True
        handler.set_arc(handler.get_arc() - 0.05)
        # Fire if sufficiently cool and the arc is small
        if handler.get_temperature() < DANGEROUS_TEMPERATURE - HEAT_PER_SHOT and \
           random.uniform(MIN_SCAN_ARC, TAU) > handler.get_arc():
            handler.shoot()
    else:
        # No target detected
        if target_locked:
            target_locked = False
        # Occasionally change turn rate randomly
        if random.randint(0, 100) == 0:
            turn_rate = random.uniform(-0.1, 0.1)
        # Gradually widen the scan arc up to 60 degrees
        if handler.get_arc() < PI / 3.0:
            handler.set_arc(handler.get_arc() + 0.05)
        # Continue moving and turning
        handler.turn(turn_rate)
        handler.accelerate(1.0)

    # If we just took damage, attempt to dodge by accelerating away
    if handler.get_health() < last_health:
        # Accelerate opposite the incoming fire direction if cool enough
        if handler.get_temperature() < DANGEROUS_TEMPERATURE - velocity_heat(
            abs(handler.get_velocity().length()) + MAX_ACCELERATION * 2
        ):
            handler.accelerate(MAX_ACCELERATION * random.choice((-2, 2)))

    # Avoid walls by turning when too close to the edges
    pos = handler.get_position()
    if not target_locked and (
        pos.x >= ARENA_WIDTH - (RADIUS * 4) or pos.x <= RADIUS * 4 or
        pos.y >= ARENA_HEIGHT - (RADIUS * 4) or pos.y <= RADIUS * 4
    ):
        handler.turn(MAX_TURN_RATE)

    # Remember health for next tick
    last_health = handler.get_health()