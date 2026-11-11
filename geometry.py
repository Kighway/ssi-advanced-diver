"""Pure compass mathematics. Coordinates are east (x), north (y).

Directions are normalized; angle measures are not. In particular a full-turn
measure of 360 degrees is preserved even though its direction is 000 degrees.
"""

from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, isfinite, radians, sin


def finite_number(value: float, name: str = "angle") -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
    return float(value)


def normalize_angle(angle: float) -> float:
    """Return a direction in [0, 360), accepting negative/multiple turns."""
    return finite_number(angle) % 360.0


def reciprocal_bearing(heading: float) -> float:
    return (normalize_angle(heading) + 180.0) % 360.0


def complementary_angle(angle: float) -> float | None:
    """Nonnegative complement of a raw angle measure, without wrapping."""
    angle = finite_number(angle)
    return 90.0 - angle if 0.0 <= angle <= 90.0 else None


def supplementary_angle(angle: float) -> float | None:
    angle = finite_number(angle)
    return 180.0 - angle if 0.0 <= angle <= 180.0 else None


def explementary_angle(angle: float) -> float:
    angle = finite_number(angle)
    if not 0.0 <= angle <= 360.0:
        raise ValueError("Explementary angle requires a measure in [0, 360]")
    return 360.0 - angle


def compass_to_xy(bearing: float, length: float = 1.0) -> tuple[float, float]:
    """North = (0, +length); east = (+length, 0); clockwise is positive."""
    length = finite_number(length, "length")
    if length < 0:
        raise ValueError("length must be nonnegative")
    theta = radians(normalize_angle(bearing))
    return length * sin(theta), length * cos(theta)


def xy_to_compass(east: float, north: float) -> float | None:
    """Bearing of a vector; a zero vector has no direction."""
    east = finite_number(east, "east")
    north = finite_number(north, "north")
    if hypot(east, north) < 1e-12:
        return None
    return normalize_angle(degrees(atan2(east, north)))


def signed_turn(start: float, end: float) -> float:
    """Shortest signed turn in [-180, 180); clockwise is positive."""
    return (normalize_angle(end) - normalize_angle(start) + 180) % 360 - 180


def format_angle(angle: float | None, decimals: int = 0) -> str:
    """Three integer digits, optionally followed by decimals; never wraps."""
    if angle is None:
        return "N/A"
    angle = finite_number(angle)
    if decimals < 0:
        raise ValueError("decimals must be nonnegative")
    width = 3 if decimals == 0 else 4 + decimals
    return f"{angle:0{width}.{decimals}f}°"


def format_bearing(bearing: float | None, decimals: int = 0) -> str:
    if bearing is None:
        return "Undefined"
    return format_angle(round(normalize_angle(bearing), decimals) % 360, decimals)


@dataclass(frozen=True)
class Relationships:
    heading: float
    reciprocal: float
    complementary: float | None
    supplementary: float | None
    explementary: float

    @property
    def explementary_direction(self) -> float:
        return normalize_angle(self.explementary)


def relationships(heading: float) -> Relationships:
    heading = normalize_angle(heading)
    return Relationships(
        heading, reciprocal_bearing(heading), complementary_angle(heading),
        supplementary_angle(heading), explementary_angle(heading),
    )


def clockwise_arc(start: float, sweep: float, radius: float,
                  segments: int = 180) -> tuple[list[float], list[float]]:
    """Sample an unwrapped clockwise sweep, including a full 360-degree arc."""
    start, sweep = finite_number(start), finite_number(sweep)
    if not 0 <= sweep <= 360:
        raise ValueError("sweep must lie in [0, 360]")
    if isinstance(segments, bool) or not isinstance(segments, int) or segments < 1:
        raise ValueError("segments must be a positive integer")
    points = [compass_to_xy(start + sweep * i / segments, radius)
              for i in range(segments + 1)]
    return [p[0] for p in points], [p[1] for p in points]
