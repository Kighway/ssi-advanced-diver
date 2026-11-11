"""Idealized, local-plane navigation models, independent of Streamlit/Plotly."""

from dataclasses import dataclass
from math import hypot

from geometry import (compass_to_xy, finite_number, normalize_angle,
                      reciprocal_bearing, signed_turn, xy_to_compass)


def turn_90(heading: float, clockwise: bool = True) -> float:
    return normalize_angle(normalize_angle(heading) + (90 if clockwise else -90))


@dataclass(frozen=True)
class SquareCourse:
    bearings: tuple[float, ...]
    points: tuple[tuple[float, float], ...]


def square_course(heading: float, leg_length: float = 20,
                  clockwise: bool = True) -> SquareCourse:
    leg_length = finite_number(leg_length, "leg length")
    if leg_length <= 0:
        raise ValueError("leg length must be positive")
    step = 90 if clockwise else -90
    bearings = tuple(normalize_angle(heading + step * i) for i in range(4))
    points = [(0.0, 0.0)]
    for bearing in bearings:
        dx, dy = compass_to_xy(bearing, leg_length)
        x, y = points[-1]
        points.append((x + dx, y + dy))
    return SquareCourse(bearings, tuple(points))


@dataclass(frozen=True)
class BezelState:
    body_bearing: float
    marker_relative: float
    north_relative: float
    south_relative: float
    aligned_end: str


def bezel_state(outbound: float, method: str = "outbound") -> BezelState:
    """Angles in the diver's frame; lubber line is always up.

    Turning the diver changes the needle/card relative to the housing.
    The bezel markers stay fixed to the housing unless explicitly reset.
    """
    outbound = normalize_angle(outbound)
    if method not in {"outbound", "reset", "south"}:
        raise ValueError("method must be outbound, reset, or south")
    body = outbound if method == "outbound" else reciprocal_bearing(outbound)
    marker = normalize_angle(-body if method == "reset" else -outbound)
    return BezelState(body, marker, normalize_angle(-body),
                      normalize_angle(180 - body), "S" if method == "south" else "N")


@dataclass(frozen=True)
class Track:
    swim_velocity: tuple[float, float]
    current_velocity: tuple[float, float]
    ground_velocity: tuple[float, float]
    displacement: tuple[float, float]
    ground_speed: float
    bearing: float | None
    drift_angle: float | None


def current_track(heading: float, swim_speed: float, current_bearing: float,
                  current_speed: float, seconds: float = 60) -> Track:
    """Vector addition: ground velocity = through-water swim + current.

    Current bearing is where water flows TO, not a wind-style FROM direction.
    Speeds are m/s; duration is seconds. No drag, shear, or tidal variation.
    """
    swim_speed = finite_number(swim_speed, "swim speed")
    current_speed = finite_number(current_speed, "current speed")
    seconds = finite_number(seconds, "seconds")
    if min(swim_speed, current_speed, seconds) < 0:
        raise ValueError("speeds and duration must be nonnegative")
    swim = compass_to_xy(heading, swim_speed)
    current = compass_to_xy(current_bearing, current_speed)
    ground = (swim[0] + current[0], swim[1] + current[1])
    speed = hypot(*ground)
    bearing = xy_to_compass(*ground)
    return Track(swim, current, ground,
                 (ground[0] * seconds, ground[1] * seconds), speed,
                 bearing, None if bearing is None else signed_turn(heading, bearing))
