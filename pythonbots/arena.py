"""Core simulation engine for the PythonBots game.

This module implements the arena where bots and projectiles interact.  It
defines two classes:

* :class:`Shot` – represents a projectile fired by a bot.  A shot
  travels in a straight line at a constant speed until it hits a wall
  or a bot.  Subclasses (e.g. in the pygame front end) may override
  the collision callbacks to provide visual or audio effects.

* :class:`Arena` – manages a collection of bots and shots, updates
  their state each tick, resolves collisions and exposes a scanning
  method used by bots to detect enemies.  All identifiers are
  English‑language; there is no backwards compatibility with the
  original Portuguese API.

The arena is agnostic of the display; the graphical front end is
implemented in :mod:`pythonbots.pgarena`.
"""

from __future__ import annotations

from math import cos, sin, atan2
from typing import List, Sequence, Tuple
import math

from . import bot as bot_module
from .vector import Vector
from .constants import (
    PI,
    TAU,
    RADIUS,
    ARENA_WIDTH,
    ARENA_HEIGHT,
    VISION_RANGE,
    SHOT_SPEED,
    SHOT_DAMAGE,
    SHOT_COLLISION_HEAT,
    SHOT_IMPACT_VEL,
    SHOT_IMPACT_ANG,
    bot_collision_damage,
    bot_collision_heat,
)


class Shot:
    """Projectile fired by a bot.

    Each shot travels at a fixed speed in the direction the firing bot
    was facing when it pulled the trigger.  Shots carry a reference
    back to the firing bot so kills can be credited.  When a shot
    leaves the arena or hits a bot it is removed from the simulation
    and the appropriate callbacks are invoked.
    """

    def __init__(self, bot_instance: "bot_module.Bot") -> None:
        self.bot: bot_module.Bot = bot_instance
        # Velocity is based on the sum of bot heading and cannon angle
        self.velocity: Vector = Vector(
            cos(bot_instance.direction + bot_instance.cannon),
            sin(bot_instance.direction + bot_instance.cannon),
        ) * SHOT_SPEED
        # Spawn slightly ahead of the bot to avoid immediate self‑collision
        self.position: Vector = bot_instance.position + Vector(
            cos(bot_instance.direction + bot_instance.cannon),
            sin(bot_instance.direction + bot_instance.cannon),
        ) * (RADIUS * 1.1)

    def update(self) -> None:
        """Advance the shot's position by one tick."""
        self.position += self.velocity

    # Collision callback placeholders.  Subclasses in pgarena override these.
    def on_bot_collision(self, bot: "bot_module.Bot") -> None:  # pragma: no cover
        pass

    def on_wall_collision(self, arena: "Arena") -> None:  # pragma: no cover
        pass


class Arena:
    """Simulated arena containing bots and projectiles."""

    bots: List[bot_module.Bot] = []
    shots: List[Shot] = []
    ticks: int = 0

    def __init__(self, functions: Sequence) -> None:
        """Create a new arena given a list of bot functions.

        Parameters
        ----------
        functions : sequence of callables
            A sequence of callables implementing bot strategies.  Each
            callable will be invoked with a :class:`pythonbots.bot.Handler`
            instance when the arena starts.
        """
        self.functions = list(functions)

    def start(self) -> None:
        """Reset internal state and spawn bots for a new round."""
        self.shots = []
        self.bots = []
        self.ticks = 0
        # Reset global bot index counter
        bot_module.bot_index_count = 0
        for func in self.functions:
            self.bots.append(bot_module.Bot(self, func))

    def add_shot(self, bot_instance: "bot_module.Bot") -> None:
        """Create and register a new shot fired by ``bot_instance``."""
        self.shots.append(Shot(bot_instance))

    def alive_count(self) -> int:
        """Return the number of bots still alive."""
        return len([b for b in self.bots if b.active])

    # Portuguese alias
    def vivos(self) -> int:
        return self.alive_count()

    def scan(self, bot_instance: "bot_module.Bot") -> Tuple[float, int]:
        """Detect another bot within the scanning arc of ``bot_instance``.

        Returns a tuple ``(distance, index)`` where ``distance`` is the
        distance to the nearest detected bot (up to
        :data:`pythonbots.constants.VISION_RANGE`) and ``index`` is the
        index of the detected bot or -1 if none is within the scan arc.
        """
        nearest: float = VISION_RANGE
        found_index: int = -1
        for other in self.bots:
            if other is bot_instance or not other.active:
                continue
            distance = (bot_instance.position - other.position).length()
            if distance - RADIUS <= VISION_RANGE and distance < nearest:
                cannon_vec = Vector(
                    cos(bot_instance.direction + bot_instance.cannon),
                    sin(bot_instance.direction + bot_instance.cannon),
                )
                target_vec = other.position - bot_instance.position
                angle = cannon_vec.angle(target_vec)
                # Determine if the angle is within the scan arc plus the target size
                # Compute the maximum detectable angle.  Add half the
                # scan arc to the apparent size of the target and wrap
                # around PI in case the sum exceeds half a turn.  Use
                # the modulo operator on floats rather than numpy.mod
                # to avoid requiring the numpy dependency.
                max_angle = (
                    bot_instance.scan_arc / 2.0
                    + math.atan2(RADIUS, (bot_instance.position - other.position).length())
                ) % PI
                if angle <= max_angle:
                    found_index = other.index
                    nearest = distance
        return nearest, found_index

    def update(self) -> None:
        """Advance the simulation by one tick.

        Updates projectiles and bots, resolves collisions and applies
        damage, heat and momentum transfers.  The order of operations
        loosely follows the original AT‑Robots logic but uses English
        names and modern Python constructs.
        """
        self.ticks += 1
        # Update shots and remove those leaving the arena bounds
        for shot in list(self.shots):
            if not (0.0 <= shot.position.x <= ARENA_WIDTH) or not (
                0.0 <= shot.position.y <= ARENA_HEIGHT
            ):
                shot.on_wall_collision(self)  # callback
                self.shots.remove(shot)
            else:
                shot.update()
        # Iterate over bots and update physics
        for b in self.bots:
            b.update()  # update physics and wall collisions
            # Check collisions with other bots
            for c in self.bots:
                if c is b:
                    continue
                distance = (b.position - c.position).length()
                if distance != 0.0 and distance <= RADIUS * 2:
                    # trigger collision callbacks
                    b.on_bot_collision(c)
                    c.on_bot_collision(b)
                    collision_vec = b.position - c.position
                    # Project velocities onto collision vector
                    trans_b = b.velocity.projection(collision_vec)
                    trans_c = c.velocity.projection(collision_vec)
                    # Correct positions to avoid overlap
                    r = (collision_vec.unit() * (RADIUS * 2)) - collision_vec
                    b.position += r / 2.0
                    c.position -= r / 2.0
                    # Swap translational components
                    b.velocity += trans_c - trans_b
                    c.velocity += trans_b - trans_c
                    # Exchange angular velocity
                    b.angular_velocity -= c.angular_velocity * 2.0
                    c.angular_velocity -= b.angular_velocity * 2.0
                    # Inflict damage
                    damage = bot_collision_damage((b.velocity - c.velocity).length())
                    if b.active:
                        b.health -= damage
                    if c.active:
                        c.health -= damage
                    # Apply heat
                    heat = bot_collision_heat((b.velocity - c.velocity).length())
                    b.temperature += heat
                    c.temperature += heat
            # Check collisions with shots
            for shot in list(self.shots):
                distance = (shot.position - b.position).length()
                if distance < RADIUS:
                    b.on_shot_collision(shot)
                    shot.on_bot_collision(b)
                    if b.active:
                        b.health -= SHOT_DAMAGE
                    b.temperature += SHOT_COLLISION_HEAT
                    # Transfer momentum
                    b.velocity += shot.velocity * SHOT_IMPACT_VEL
                    if not b.active:
                        # Add angular impulse to corpses
                        b.angular_velocity += shot.velocity.length() * SHOT_IMPACT_ANG
                    elif b.health <= 0.0:
                        # If bot died now, update stats
                        b.killed_by = shot.bot
                        shot.bot.killed.append(b)
                    # Remove the shot after collision
                    self.shots.remove(shot)