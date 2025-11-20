"""Robot and player API for PythonBots.

This module defines two core classes:

* :class:`Handler` provides the interface exposed to user‑authored bot
  functions. It allows reading the game state (position, velocity,
  temperature, etc.) and issuing commands (accelerate, turn, rotate
  cannon, adjust scan arc and shoot).  All methods are named in
  English; no backwards‑compatible Portuguese aliases are provided.

* :class:`Bot` encapsulates the physical state of a robot. Each
  ``Bot`` instance maintains its position, heading, cannon angle,
  temperature, health and other internal values.  The ``update``
  method advances the simulation by one tick, applying physics and
  calling the player‑supplied bot function if the bot is alive.

This file replaces the original ``bot.py`` which used Portuguese
identifiers.  All identifiers have been renamed for clarity and the
logic has been adjusted to call into :mod:`pythonbots.constants` for
configuration values.
"""

from __future__ import annotations

import random
from math import sin, cos
from typing import Callable, Optional, List, Tuple, Any

from .constants import (
    PI,
    TAU,
    MAX_HEALTH,
    NORMAL_TEMPERATURE,
    MAX_TEMPERATURE,
    DANGEROUS_TEMPERATURE,
    TEMPERATURE_DAMAGE,
    COOLING_RATE,
    MAX_ACCELERATION,
    MAX_TURN_RATE,
    MAX_CANNON_TURN_RATE,
    MIN_SCAN_ARC,
    EXPLOSION_IMPACT,
    RADIUS,
    ARENA_WIDTH,
    ARENA_HEIGHT,
    VISION_RANGE,
    MAX_TIME,
    SHOT_DAMAGE,
    SHOT_COLLISION_HEAT,
    HEAT_PER_SHOT,
    SHOT_IMPACT_VEL,
    SHOT_IMPACT_ANG,
    FRICTION,
    ANGULAR_FRICTION,
    wall_collision_damage,
    wall_collision_heat,
    bot_collision_damage,
    bot_collision_heat,
    velocity_heat,
    minabs,
)
from .vector import Vector


# Module level counter to assign unique indices to bots.  This value
# increments each time a new bot is created.
bot_index_count: int = 0


class Handler:
    """Interface presented to user‑authored bot functions.

    A ``Handler`` wraps a :class:`Bot` instance and exposes a set of
    methods that the user can call each tick to implement their
    strategy.  Reading methods return information about the bot or the
    arena, while action methods modify the bot's state (subject to
    physical constraints).  Bot functions receive a single ``Handler``
    argument and must not retain references to it outside of the
    current tick.
    """

    def __init__(self, bot: "Bot") -> None:
        self._bot = bot

    # Reading methods
    def is_active(self) -> bool:
        """Return ``True`` if this bot is still alive."""
        return self._bot.active

    def get_velocity(self) -> Vector:
        """Return the current velocity vector."""
        return self._bot.velocity

    def get_position(self) -> Vector:
        """Return the current position vector."""
        return self._bot.position

    def get_direction(self) -> float:
        """Return the bot's heading in radians."""
        return self._bot.direction

    def get_cannon(self) -> float:
        """Return the cannon's relative angle in radians."""
        return self._bot.cannon

    def get_arc(self) -> float:
        """Return the current scan arc width in radians."""
        return self._bot.scan_arc

    def get_angular_velocity(self) -> float:
        """Return the current angular velocity in radians per tick."""
        return self._bot.angular_velocity

    def get_health(self) -> float:
        """Return the remaining health points."""
        return self._bot.health

    def get_temperature(self) -> float:
        """Return the current temperature."""
        return self._bot.temperature

    def get_index(self) -> int:
        """Return the unique index assigned to this bot."""
        return self._bot.index

    # Perception methods
    def scan(self) -> Tuple[float, int]:
        """Scan for the nearest enemy within the current scan arc.

        Returns a tuple ``(distance, index)`` where ``distance`` is the
        distance to the nearest detected bot (up to
        :data:`pythonbots.constants.VISION_RANGE`) and ``index`` is the
        index of the detected bot or -1 if none is within the scan arc.
        """
        return self._bot.arena.scan(self._bot)

    def get_alive_count(self) -> int:
        """Return the number of bots still alive in the arena."""
        return self._bot.arena.alive_count()

    # Action methods
    def accelerate(self, accel: float) -> None:
        """Adjust the bot's forward/backward acceleration by ``accel``.

        The supplied value is added to the bot's current acceleration and
        will be clamped to the maximum allowed acceleration during the
        physics update.  Positive values accelerate forward while
        negative values accelerate backward.
        """
        self._bot.acceleration += accel

    def turn(self, angle: float) -> None:
        """Rotate the bot by ``angle`` radians.

        The supplied value is added to the bot's angular acceleration and
        will be clamped to the maximum turn rate during the physics
        update.  Positive values rotate counter‑clockwise and negative
        values rotate clockwise.
        """
        self._bot.angular_acceleration += angle

    def rotate_cannon(self, angle: float) -> None:
        """Rotate the cannon by ``angle`` radians.

        Positive values rotate the cannon counter‑clockwise relative to
        the bot's heading.  The cannon rotation is clamped to
        ``MAX_CANNON_TURN_RATE`` per tick.
        """
        self._bot.cannon_acceleration += angle

    def set_arc(self, arc: float) -> None:
        """Set the width of the scan arc in radians.

        The value will be clamped between ``MIN_SCAN_ARC`` and ``TAU``
        during the physics update.  A smaller arc makes scanning more
        precise but harder to align.
        """
        self._bot.target_arc = arc

    def shoot(self) -> None:
        """Fire the cannon once if possible.

        A bot may only shoot once per tick.  Firing adds heat and
        increments the bot's shot counter.  If the bot is allowed to
        shoot it will ask the arena to create a new projectile.
        """
        if not self._bot.has_shot:
            self._bot.arena.add_shot(self._bot)
            self._bot.shots += 1
            self._bot.temperature += HEAT_PER_SHOT
            self._bot.has_shot = True


class Bot:
    """Represents a single autonomous robot in the arena.

    Bot instances are created by :class:`pythonbots.arena.Arena` and
    advanced each tick by calling :meth:`update`.  User‑authored bot
    functions are passed a :class:`Handler` instance to interact with
    their bot.  The Bot class maintains physical state such as
    position, velocity, temperature and health, and exposes callback
    methods that subclasses or front ends (e.g. the pygame arena) can
    override to implement effects.
    """

    # Default state values.  These are class attributes so they are
    # documented in one place; they will be copied onto each instance
    # during initialisation.
    velocity: Vector = Vector(0.0, 0.0)
    position: Vector = Vector(0.0, 0.0)
    direction: float = 0.0
    cannon: float = 0.0
    scan_arc: float = MIN_SCAN_ARC
    angular_velocity: float = 0.0
    health: float = MAX_HEALTH
    temperature: float = NORMAL_TEMPERATURE
    index: int = 0
    active: bool = True
    has_shot: bool = False

    # Mutable state values that vary over time
    acceleration: float = 0.0
    angular_acceleration: float = 0.0
    cannon_acceleration: float = 0.0
    target_arc: float = scan_arc

    # Statistics
    shots: int = 0
    killed_by: Optional["Bot"] = None

    def __init__(self, arena: "pythonbots.arena.Arena", func: Callable[[Handler], None]):
        global bot_index_count
        # Save arena and user function
        self.arena = arena
        self.func = func

        # Assign a unique index and increment the counter
        self.index = bot_index_count
        bot_index_count += 1

        # Initialise position and heading randomly within the arena
        self.position = Vector(
            random.uniform(RADIUS, ARENA_WIDTH - RADIUS),
            random.uniform(RADIUS, ARENA_HEIGHT - RADIUS),
        )
        self.direction = random.uniform(0.0, TAU)
        self.angular_velocity = random.uniform(0.0, TAU)

        # Reset other state values
        self.velocity = Vector(0.0, 0.0)
        self.cannon = 0.0
        self.scan_arc = MIN_SCAN_ARC
        self.angular_acceleration = 0.0
        self.cannon_acceleration = 0.0
        self.acceleration = 0.0
        self.target_arc = self.scan_arc
        self.health = MAX_HEALTH
        self.temperature = NORMAL_TEMPERATURE
        self.active = True
        self.has_shot = False
        self.shots = 0
        self.killed = []  # type: List[Bot]
        self.killed_by = None

        # Create a handler for the user function
        self.handler = Handler(self)

    def __str__(self) -> str:
        return self.func.__name__

    def update(self) -> None:
        """Advance the simulation for this bot by one tick.

        Updates position, velocity, temperature and handles collisions.
        Executes the user‑supplied bot function if the bot is alive.
        """
        # Update position and direction based on current velocities
        self.position += self.velocity
        self.velocity *= FRICTION if self.active else 0.8
        self.direction += self.angular_velocity
        self.angular_velocity *= ANGULAR_FRICTION if self.active else 0.9

        # Let the cannon spin freely if dead
        if not self.active:
            self.cannon += self.angular_velocity * 2.0

        # Update velocities based on accelerations
        self.velocity += Vector(cos(self.direction), sin(self.direction)) * minabs(
            self.acceleration, MAX_ACCELERATION
        )
        self.acceleration -= minabs(self.acceleration, MAX_ACCELERATION)

        self.angular_velocity += minabs(self.angular_acceleration, MAX_TURN_RATE)
        self.angular_acceleration -= minabs(self.angular_acceleration, MAX_TURN_RATE)

        self.cannon += minabs(self.cannon_acceleration, MAX_CANNON_TURN_RATE)
        self.cannon_acceleration -= minabs(self.cannon_acceleration, MAX_CANNON_TURN_RATE)

        self.scan_arc = self.target_arc  # apply requested scan arc

        # Check for death
        if self.health <= 0 and self.active:
            self.active = False
            self.health = 0
            # Apply explosion impulse
            self.velocity *= EXPLOSION_IMPACT
            self.angular_velocity = random.uniform(-PI / 2.0, PI / 2.0)
            self.temperature = MAX_TEMPERATURE
            # Notify via callback
            self.die()

        # Temperature handling
        if self.temperature >= DANGEROUS_TEMPERATURE and self.active:
            self.health -= TEMPERATURE_DAMAGE
        # Cool down
        if self.temperature > NORMAL_TEMPERATURE:
            self.temperature -= COOLING_RATE
        # Heat from movement
        self.temperature += velocity_heat(self.velocity.length())
        # Clamp temperature
        self.temperature = min(self.temperature, MAX_TEMPERATURE)

        # Handle wall collisions
        def handle_wall():
            # Inflict damage and heat based on current speed
            self.health -= wall_collision_damage(self.velocity.length())
            self.temperature += wall_collision_heat(self.velocity.length())
            # Trigger callback
            self.on_wall_collision()

        if self.position.x < RADIUS:
            handle_wall()
            self.position.x = RADIUS
            self.velocity.x *= -1
        elif self.position.x > ARENA_WIDTH - RADIUS:
            handle_wall()
            self.position.x = ARENA_WIDTH - RADIUS
            self.velocity.x *= -1

        if self.position.y < RADIUS:
            handle_wall()
            self.position.y = RADIUS
            self.velocity.y *= -1
        elif self.position.y > ARENA_HEIGHT - RADIUS:
            handle_wall()
            self.position.y = ARENA_HEIGHT - RADIUS
            self.velocity.y *= -1

        # Execute player code if alive
        if self.active:
            # Invoke the user function
            self.func(self.handler)
            # Clamp requested scan arc between limits
            self.target_arc = max(min(self.target_arc, TAU), MIN_SCAN_ARC)
            # Allow shooting again next tick
            self.has_shot = False

    # Callback hooks.  These methods are meant to be overridden by
    # subclasses (e.g. in the pygame front end) to provide visual or
    # audio effects.  They are no‑ops here.
    def on_wall_collision(self) -> None:
        """Called when the bot collides with a wall."""
        pass

    def on_bot_collision(self, other: "Bot") -> None:
        """Called when the bot collides with another bot."""
        pass

    def on_shot_collision(self, shot: Any) -> None:
        """Called when the bot is hit by a projectile."""
        pass

    def die(self) -> None:
        """Called when the bot's health reaches zero."""
        pass