# PythonBots

![screenshot](img/screenshot.png "Screenshot")

PythonBots is a programming contest in which players write small
Python functions that control autonomous robots. Each robot operates in
a 2‑D arena where it can move, turn, scan for opponents and fire.
The last robot left alive at the end of the round wins.  This
repository contains an updated implementation of the classic AT‑Robots
idea rewritten for Python 3 and translated entirely into English.

## Requirements

* Python 3.9 or later.

There are no external dependencies; the simulation uses only the
Python standard library.  The original project included a pygame
front end and sound effects, but this version provides a text‑only
simulation for simplicity and portability.

## Running the game

From the root of the repository, invoke the game with the names of
your bots:

```bash
python3 main.py [-r NUM_ROUNDS] bot1 bot2 ...
```

* Each positional argument is the name of a module inside the
  `bot/` directory (without the `.py` extension).  The module must
  define a function with the same name as the file.  See the examples in
  the `bot/` directory.
* Use the `-r` or `--rounds` option to specify how many rounds to play
  (default is 1).  The game plays out until only one robot remains or
  until the time limit is reached.

Example: run a 10‑round tournament with five example bots:

```bash
python3 main.py -r 10 ccoria cabello bigodines snitram william
```

At the end of the tournament a summary table of wins, ties, losses,
kills, shots fired and score is printed.

## Writing your own bot

To create your own robot:

1. Create a new Python file in the `bot/` directory.  The filename
   (without `.py`) will be the robot's name.
2. Define a function whose name matches the filename.  This function
   will be called once per simulation tick and receives a single
   argument, `handler`, which is an instance of
   `pythonbots.bot.Handler`.

Bots are stateless functions by design, but you may use module‑level
variables to store state between calls.  For example, you might keep
track of whether you have recently seen an opponent or whether you are
currently scanning or firing.

### The Handler API

The `handler` object exposes methods to read the state of your robot and
the arena and to issue commands.  All methods are named in English.

#### Reading state

| Method            | Description                                                       |
| ----------------- | ----------------------------------------------------------------- |
| `is_active()`     | Returns `True` if the bot is still alive.                         |
| `get_velocity()`  | Returns the current velocity (`Vector`).                          |
| `get_position()`  | Returns the bot's position (`Vector`).                            |
| `get_direction()` | Returns the bot's heading in radians.                             |
| `get_cannon()`    | Returns the relative cannon angle in radians.                     |
| `get_arc()`       | Returns the current scan arc width in radians.                    |
| `get_angular_velocity()` | Returns the current angular velocity in radians per tick.  |
| `get_health()`    | Returns the current health points.                                |
| `get_temperature()`| Returns the current temperature.                                  |
| `get_index()`     | Returns the unique index of this bot (useful for identifying
                       specific opponents).                                              |
| `scan()`          | Returns `(distance, index)` of the nearest enemy within the
                       current scan arc and up to the vision range.  If no enemy is
                       detected the index will be `-1` and the distance will be the
                       maximum vision range.                                             |
| `get_alive_count()`| Returns the number of bots still alive in the arena.             |

#### Issuing actions

| Method           | Description                                                        |
| ---------------- | ------------------------------------------------------------------ |
| `accelerate(x)`  | Adjusts the forward/backward acceleration by `x` (positive values
                      accelerate forward, negative values reverse).                      |
| `turn(a)`        | Rotate the bot's body by `a` radians (positive is counter‑clockwise).|
| `rotate_cannon(a)`| Rotate the cannon by `a` radians relative to the body.            |
| `set_arc(a)`     | Set the width of the scan arc to `a` radians (clamped to a sensible
                      range).  A narrow arc makes scanning more precise but harder to
                      align.                                                             |
| `shoot()`        | Fire the cannon once (consumes energy and heats up the bot).       |

Only one shot may be fired per tick.  Firing raises your bot's
temperature; if it overheats it will take damage each tick until it
cools down.

### Strategy and game physics

The arena is a rectangle defined by the constants `ARENA_WIDTH`
and `ARENA_HEIGHT` in `pythonbots.constants`.  Robots have a circular
body of radius `RADIUS` and begin at random positions and headings.
They bounce off the walls and off each other.  Your bot can see up to
`VISION_RANGE` units ahead through its current scan arc; use
`handler.scan()` to detect the nearest opponent.

Key points to consider when designing your bot:

* **Temperature** – Moving, colliding and firing generate heat.  If
  your bot's temperature exceeds the `DANGEROUS_TEMPERATURE` constant it
  will begin to take damage.  Use `handler.get_temperature()` to
  monitor your heat and decide when to slow down or stop firing.
* **Health** – Bots start with `MAX_HEALTH` points.  Collisions and
  projectiles reduce health.  When health reaches zero, the bot
  explodes, imparting a small impulse to nearby robots.
* **Scanning** – Adjust your scan arc with `handler.set_arc()`.
  A wider arc increases your chances of spotting an enemy but yields a
  less precise distance; a narrow arc requires more aiming.  The
  `handler.scan()` method returns the distance and index of the
  detected bot if any.
* **Movement** – `handler.accelerate()` controls forward and backward
  acceleration and is capped at a maximum value per tick.  Use
  `handler.turn()` to change your heading and
  `handler.rotate_cannon()` to aim the gun independently of the body.

For a complete list of constants and helper functions see
`pythonbots/constants.py`.  Study the example bots in the `bot/`
directory for inspiration.

## License

This project is licensed under the MIT License.  See `LICENSE` for
details.

## License

This project is licensed under the MIT License. See `LICENSE` for details.