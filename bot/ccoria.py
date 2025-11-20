"""Example bot implementation: ccoria.

This bot drifts slowly backwards while sweeping its scan arc.  When it
detects an enemy it attempts to align the front of its hull with the
edge of the scan arc so that the cannon points directly at the target.
It accelerates slowly toward the target, firing whenever possible and
narrowing its scan arc.  If the target is lost it widens the scan arc
again and resumes drifting.
"""

from __future__ import annotations

from pythonbots.constants import (
    PI,
    VISION_RANGE,
    DANGEROUS_TEMPERATURE,
    HEAT_PER_SHOT,
    MAX_TURN_RATE,
)


tracking: bool = False
accel_rate: float = MAX_TURN_RATE * 0.01


def ccoria(handler: "pythonbots.bot.Handler") -> None:
    """Control function for the ccoria bot."""
    global tracking, accel_rate
    distance, _ = handler.scan()
    if distance < VISION_RANGE:
        # Target detected: if we weren't tracking, align hull with scan edge
        if not tracking:
            handler.turn(handler.get_arc() / 2.0 - handler.get_angular_velocity())
        # Accelerate slightly forward
        handler.accelerate(0.1)
        # Fire if cool enough
        if handler.get_temperature() < DANGEROUS_TEMPERATURE - HEAT_PER_SHOT:
            handler.shoot()
        tracking = True
        # Narrow the scan arc to focus on the target
        handler.set_arc(handler.get_arc() - 0.01)
    elif tracking:
        # Lost the target: reset tracking and turn by half the arc
        tracking = False
        handler.turn(handler.get_arc() / 2.0)
        accel_rate = MAX_TURN_RATE * 0.01
    else:
        # No target: drift backwards and sweep the arc
        handler.accelerate(-0.5)
        handler.turn(accel_rate - handler.get_angular_velocity())
        handler.set_arc(PI / 4.0)
        # Slowly increase the turn rate until a maximum
        if accel_rate < MAX_TURN_RATE:
            accel_rate += 0.0001
        else:
            accel_rate = MAX_TURN_RATE * 0.01