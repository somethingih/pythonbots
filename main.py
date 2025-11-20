#!/usr/bin/env python3
"""Command line interface for the PythonBots game.

This script allows you to pit one or more Python bot functions against
each other in a simulated arena.  Only a text‑based simulation is
supported; the pygame front end has been removed in this version.  To
play, specify the names of the bot modules (located in the ``bot``
package) after any options.  The number of rounds can be adjusted
with ``-r`` or ``--rounds``.

Example::

    python3 main.py -r 10 ccoria cabello bigodines snitram william

At the end of the tournament a summary table of wins, ties, losses,
kills, shots fired and score is printed.  See the README for details
on writing your own bots.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Callable

from pythonbots.constants import MAX_TIME, score_factor
from pythonbots.arena import Arena as TextArena


def load_bot_function(name: str) -> Callable:
    """Import and return the bot function with the given module name.

    The ``bot`` package must contain a module whose filename matches
    ``name`` and which defines a function of the same name.  If the
    module cannot be imported or the function does not exist a
    ``SystemExit`` is raised with an explanatory message.
    """
    try:
        module = __import__(f"bot.{name}", fromlist=[name])
    except ImportError as exc:
        raise SystemExit(f"Could not load bot module '{name}': {exc}") from exc
    try:
        func = getattr(module, name)
    except AttributeError as exc:
        raise SystemExit(f"Module 'bot.{name}' does not define a function '{name}'.") from exc
    return func


def main(argv: List[str] | None = None) -> None:
    """Entry point for the command line interface."""
    parser = argparse.ArgumentParser(description="Run PythonBots tournaments in text or GUI mode.")
    parser.add_argument(
        "bots",
        nargs='+',
        help="Names of bot modules (without the .py extension) located in the bot/ directory.",
    )
    parser.add_argument(
        "-r",
        "--rounds",
        type=int,
        default=1,
        help="Number of rounds to play (default: 1)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Run the pygame GUI front-end (requires pygame).",
    )
    args = parser.parse_args(argv)

    # Lazy import of pgarena so the module-level future import stays valid
    try:
        import pgarena as pgarena_module  # type: ignore
    except Exception:
        pgarena_module = None

    # Load bot functions
    functions: List[Callable] = [load_bot_function(name) for name in args.bots]
    if not functions:
        raise SystemExit("No bot functions specified.")

    # Initialise score table
    score = [
        {"wins": 0, "losses": 0, "ties": 0, "score": 0.0, "kills": 0, "shots": 0}
        for _ in functions
    ]

    # Run tournament rounds
    for rnd in range(args.rounds):
        if args.gui:
            if pgarena_module is None:
                raise SystemExit("pygame front-end not available. Install pygame or run without --gui.")
            arena = pgarena_module.Arena(False, functions)
        else:
            arena = TextArena(functions)
        arena.score = score
        arena.round = rnd
        arena.rounds = args.rounds
        arena.start()
        # Simulate until one bot remains or the time limit is reached
        if args.gui:
            import pygame
            clock = pygame.time.Clock()
            running = True
            while running and arena.alive_count() > 1 and arena.ticks < MAX_TIME:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            running = False
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                arena.update()
                arena.draw()
                clock.tick(60)
        else:
            while arena.alive_count() > 1 and arena.ticks < MAX_TIME:
                arena.update()
        # Update score after the round
        alive = arena.alive_count()
        tie = alive != 1
        for i, bot_instance in enumerate(arena.bots):
            score[i]["kills"] += len(bot_instance.killed)
            score[i]["shots"] += bot_instance.shots
            if bot_instance.active:
                score[i]["score"] += score_factor(len(functions), alive)
                if tie:
                    score[i]["ties"] += 1
                else:
                    score[i]["wins"] += 1
            else:
                score[i]["losses"] += 1

    # Print summary
    total_rounds = args.rounds
    if total_rounds > 1:
        print(f"{total_rounds} rounds played")
    else:
        print("one round played")

    print(f"{'name':>20}  {'wins':>4} {'ties':>4} {'losses':>6} {'kills':>5} {'shots':>5} score")
    print('-' * 50)
    for i, func in enumerate(functions):
        s = score[i]
        print(
            f"{func.__name__:>20}  {s['wins']:4d} {s['ties']:4d} {s['losses']:6d} {s['kills']:5d} {s['shots']:5d} {s['score']:4.2f}"
        )


if __name__ == '__main__':
    main()