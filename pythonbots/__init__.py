"""Top‑level package for the PythonBots game.

This package exposes the core classes used by the game.  Import from
this package if you need direct access to the engine or bot classes.

Available objects:

* :class:`pythonbots.constants` – game tuning constants and helper functions.
* :class:`pythonbots.vector.Vector` – 2‑D vector implementation.
* :class:`pythonbots.bot.Handler` – interface for user‑authored bot code.
* :class:`pythonbots.bot.Bot` – robot representation.
* :class:`pythonbots.arena.Shot` – projectile representation.
* :class:`pythonbots.arena.Arena` – simulation engine.
"""

from . import constants  # noqa: F401
from .vector import Vector  # noqa: F401
from .bot import Handler, Bot  # noqa: F401
from .arena import Shot, Arena  # noqa: F401