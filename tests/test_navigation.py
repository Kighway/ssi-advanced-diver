import math

import pytest

from geometry import normalize_angle, reciprocal_bearing
from navigation_scenarios import bezel_state, current_track, square_course, turn_90

HEADINGS = [0, 40, 45, 90, 135, 180, 225, 270, 315, 359]


@pytest.mark.parametrize("heading", HEADINGS)
def test_turns(heading):
    assert turn_90(heading) == (heading + 90) % 360
    assert turn_90(heading, False) == (heading - 90) % 360
    assert turn_90(turn_90(heading), False) == heading


@pytest.mark.parametrize("heading", HEADINGS)
@pytest.mark.parametrize("clockwise", [True, False])
def test_square_closes_and_has_equal_lengths(heading, clockwise):
    course = square_course(heading, 20, clockwise)
    assert len(course.points) == 5
    assert course.points[-1] == pytest.approx((0, 0), abs=1e-10)
    for a, b in zip(course.points, course.points[1:]):
        assert math.dist(a, b) == pytest.approx(20)
    assert course.bearings[0] == heading
    assert course.bearings[2] == reciprocal_bearing(heading)


@pytest.mark.parametrize("heading", HEADINGS)
def test_bezel_return_methods_equivalent(heading):
    out = bezel_state(heading)
    reset = bezel_state(heading, "reset")
    south = bezel_state(heading, "south")
    assert out.body_bearing == heading
    assert out.marker_relative == out.north_relative
    assert reset.body_bearing == south.body_bearing == reciprocal_bearing(heading)
    assert reset.marker_relative == reset.north_relative
    assert south.marker_relative == south.south_relative
    assert south.marker_relative == out.marker_relative
    assert reset.marker_relative == normalize_angle(out.marker_relative + 180)


def test_known_square_and_wraparound():
    assert square_course(40).bearings == (40, 130, 220, 310)
    assert square_course(40, clockwise=False).bearings == (40, 310, 220, 130)
    assert turn_90(359) == 89


def test_cross_current_analytic_solution():
    track = current_track(0, .5, 90, .3, 60)
    assert track.displacement == pytest.approx((18, 30))
    assert track.bearing == pytest.approx(math.degrees(math.atan(.3/.5)))
    assert track.ground_speed == pytest.approx(math.hypot(.3, .5))
    assert track.drift_angle == pytest.approx(track.bearing)


@pytest.mark.parametrize("heading", HEADINGS)
def test_still_water_track_matches_heading(heading):
    track = current_track(heading, .5, 90, 0)
    assert track.bearing == pytest.approx(heading)
    assert track.ground_speed == pytest.approx(.5)
    assert track.drift_angle == pytest.approx(0)


def test_opposing_current_and_zero_speed():
    track = current_track(0, .5, 180, .5)
    assert track.bearing is None
    assert track.drift_angle is None
    assert track.ground_speed == pytest.approx(0, abs=1e-12)
    assert current_track(0, 0, 0, 0).bearing is None
    assert current_track(0, .5, 180, 1).bearing == pytest.approx(180)


def test_return_does_not_cancel_current():
    outbound = current_track(0, .5, 90, .3)
    inbound = current_track(180, .5, 90, .3)
    endpoint = tuple(a + b for a, b in zip(outbound.displacement, inbound.displacement))
    assert endpoint == pytest.approx((36, 0), abs=1e-10)


@pytest.mark.parametrize("args", [(0,-1,0,0,60), (0,1,0,-1,60), (0,1,0,1,-1)])
def test_invalid_current_parameters(args):
    with pytest.raises(ValueError):
        current_track(*args)


def test_invalid_scenarios():
    with pytest.raises(ValueError):
        square_course(40, 0)
    with pytest.raises(ValueError):
        bezel_state(40, "invalid")
