"""Pure, local-plane rectangle model. Distances are through water, in metres.

North is +y, east is +x. All bearings share one north reference. A current
bearing is the direction water flows TOWARD. No UI or plotting dependencies.
"""

from dataclasses import dataclass
from math import hypot, radians, tan

from geometry import (compass_to_xy, finite_number, normalize_angle, signed_turn,
                      xy_to_compass)
from navigation_scenarios import current_track

Point = tuple[float, float]


def perpendicular_current(heading: float, current_bearing: float) -> bool:
    return abs(abs(signed_turn(heading, current_bearing)) - 90) < 1e-9


def calibrate_current_speed(swim_speed: float, drift_angle: float = 10) -> float:
    """Speed for a perpendicular current and |drift| < 90 degrees.

    The current bearing determines which side the drift is on. The sign of
    drift_angle is immaterial to the nonnegative speed returned here.
    This formula must not be used for oblique or along-course currents.
    """
    swim_speed = finite_number(swim_speed, "swim speed")
    drift_angle = finite_number(drift_angle, "drift angle")
    if swim_speed <= 0:
        raise ValueError("swim speed must be positive")
    if abs(drift_angle) >= 90:
        raise ValueError("perpendicular drift magnitude must be less than 90°")
    return swim_speed * tan(radians(abs(drift_angle)))


DEFAULT_CURRENT_SPEED = calibrate_current_speed(1.0, 10)


@dataclass(frozen=True)
class RectangleLeg:
    number: int
    heading: float
    swim_distance: float
    duration: float
    elapsed_time: float
    swim_velocity: Point
    ground_velocity: Point
    ground_speed: float
    track_bearing: float | None
    drift_angle: float | None
    planned_start: Point
    planned_end: Point
    actual_start: Point
    actual_end: Point

    @property
    def ground_distance(self) -> float:
        return self.ground_speed * self.duration


@dataclass(frozen=True)
class RectangleSimulation:
    initial_heading: float
    length: float
    width: float
    swim_speed: float
    current_bearing: float
    configured_current_speed: float
    current_enabled: bool
    current_velocity: Point
    legs: tuple[RectangleLeg, ...]
    planned_points: tuple[Point, ...]
    actual_points: tuple[Point, ...]

    @property
    def total_time(self) -> float:
        return self.legs[-1].elapsed_time

    @property
    def total_swim_distance(self) -> float:
        return 2 * (self.length + self.width)

    @property
    def effective_current_speed(self) -> float:
        return self.configured_current_speed if self.current_enabled else 0.0

    @property
    def displacement(self) -> Point:
        return self.actual_points[-1]

    @property
    def displacement_distance(self) -> float:
        return hypot(*self.displacement)

    @property
    def displacement_bearing(self) -> float | None:
        return xy_to_compass(*self.displacement)


def simulate_rectangle(initial_heading: float = 60, length: float = 40,
                       width: float = 20, swim_speed: float = 1.0,
                       current_bearing: float = 150,
                       current_speed: float = DEFAULT_CURRENT_SPEED,
                       current_enabled: bool = True) -> RectangleSimulation:
    """Integrate four clockwise legs with instantaneous turns.

    t_i = swim_distance_i / swim_speed; ground velocity = swim + current.
    The exact closed planned polygon is constructed from two perpendicular
    basis vectors. Actual vertices are planned vertices + current * elapsed
    time, algebraically equivalent to integrating each ground-velocity leg.
    This avoids trigonometric closure residue and guarantees exact identical
    planned/actual points when current is zero or disabled.
    """
    initial_heading = normalize_angle(initial_heading)
    current_bearing = normalize_angle(current_bearing)
    length = finite_number(length, "length")
    width = finite_number(width, "width")
    swim_speed = finite_number(swim_speed, "swim speed")
    current_speed = finite_number(current_speed, "current speed")
    if min(length, width, swim_speed) <= 0:
        raise ValueError("length, width and swim speed must be positive")
    if current_speed < 0:
        raise ValueError("current speed must be nonnegative")
    if not isinstance(current_enabled, bool):
        raise TypeError("current_enabled must be a boolean")

    bearings = tuple(normalize_angle(initial_heading + 90 * i) for i in range(4))
    a = compass_to_xy(bearings[0], length)
    b = compass_to_xy(bearings[1], width)
    planned = ((0.0, 0.0), a, (a[0] + b[0], a[1] + b[1]), b, (0.0, 0.0))
    effective_speed = current_speed if current_enabled else 0.0
    current = compass_to_xy(current_bearing, effective_speed)
    actual = [(0.0, 0.0)]
    legs = []
    elapsed = 0.0
    for i, distance in enumerate((length, width, length, width)):
        duration = distance / swim_speed
        elapsed += duration
        velocity = current_track(bearings[i], swim_speed, current_bearing,
                                 effective_speed, duration)
        end = (planned[i + 1][0] + current[0] * elapsed,
               planned[i + 1][1] + current[1] * elapsed)
        legs.append(RectangleLeg(
            i + 1, bearings[i], distance, duration, elapsed,
            velocity.swim_velocity, velocity.ground_velocity,
            velocity.ground_speed, velocity.bearing, velocity.drift_angle,
            planned[i], planned[i + 1], actual[-1], end,
        ))
        actual.append(end)
    return RectangleSimulation(initial_heading, length, width, swim_speed,
                               current_bearing, current_speed, current_enabled,
                               current, tuple(legs), planned, tuple(actual))
