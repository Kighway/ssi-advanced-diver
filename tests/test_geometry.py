import math

import pytest

from geometry import (clockwise_arc, compass_to_xy, complementary_angle,
                      explementary_angle, format_angle, format_bearing,
                      normalize_angle, reciprocal_bearing, relationships,
                      signed_turn, supplementary_angle, xy_to_compass)


@pytest.mark.parametrize("heading,rec,comp,supp,ex", [
    (0, 180, 90, 180, 360), (40, 220, 50, 140, 320),
    (45, 225, 45, 135, 315), (90, 270, 0, 90, 270),
    (91, 271, None, 89, 269), (135, 315, None, 45, 225),
    (180, 0, None, 0, 180), (181, 1, None, None, 179),
    (225, 45, None, None, 135), (270, 90, None, None, 90),
    (315, 135, None, None, 45), (359, 179, None, None, 1),
])
def test_relationships(heading, rec, comp, supp, ex):
    r = relationships(heading)
    assert (r.reciprocal, r.complementary, r.supplementary, r.explementary) == (rec, comp, supp, ex)
    assert r.explementary_direction == ex % 360


@pytest.mark.parametrize("angle,expected", [(-721, 359), (-360, 0), (-1, 359),
                                         (0, 0), (360, 0), (400, 40), (721, 1), (359.5, 359.5)])
def test_normalization(angle, expected):
    assert normalize_angle(angle) == expected


@pytest.mark.parametrize("heading,expected", [(0, (0,1)), (90,(1,0)), (180,(0,-1)),
                                            (270,(-1,0)), (45,(math.sqrt(.5),math.sqrt(.5))),
                                            (135,(math.sqrt(.5),-math.sqrt(.5))),
                                            (225,(-math.sqrt(.5),-math.sqrt(.5))),
                                            (315,(-math.sqrt(.5),math.sqrt(.5)))])
def test_navigation_coordinates(heading, expected):
    assert compass_to_xy(heading) == pytest.approx(expected, abs=1e-12)


def test_every_integer_heading_invariants():
    for h in range(360):
        r = relationships(h)
        assert reciprocal_bearing(r.reciprocal) == h
        assert r.heading + r.explementary == 360
        assert xy_to_compass(*compass_to_xy(h, 10)) == pytest.approx(h, abs=1e-10)
        assert compass_to_xy(r.reciprocal) == pytest.approx(tuple(-v for v in compass_to_xy(h)), abs=1e-12)
        if r.complementary is not None:
            assert h + r.complementary == 90
        if r.supplementary is not None:
            assert h + r.supplementary == 180


def test_angle_measures_never_wrap():
    assert complementary_angle(360) is None
    assert complementary_angle(-1) is None
    assert supplementary_angle(360) is None
    assert supplementary_angle(-1) is None
    assert explementary_angle(0) == 360
    assert explementary_angle(360) == 0
    assert relationships(360).explementary == 360  # direction is normalized first


@pytest.mark.parametrize("fn", [normalize_angle, reciprocal_bearing, complementary_angle,
                               supplementary_angle, explementary_angle, compass_to_xy])
@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_reject_nonfinite(fn, value):
    with pytest.raises(ValueError):
        fn(value)


@pytest.mark.parametrize("value", [True, "40", None])
def test_reject_non_numbers(value):
    with pytest.raises(TypeError):
        normalize_angle(value)


@pytest.mark.parametrize("angle", [-1, 361])
def test_explement_requires_valid_measure(angle):
    with pytest.raises(ValueError):
        explementary_angle(angle)


def test_formatting():
    assert format_bearing(40) == "040°"
    assert format_bearing(360) == "000°"
    assert format_bearing(359.99, 1) == "000.0°"
    assert format_angle(360) == "360°"
    assert format_angle(50) == "050°"
    assert format_angle(None) == "N/A"
    assert format_bearing(None) == "Undefined"


def test_arc_endpoints_and_full_circle():
    x, y = clockwise_arc(40, 50, .5)
    assert (x[0], y[0]) == pytest.approx(compass_to_xy(40, .5))
    assert (x[-1], y[-1]) == pytest.approx((.5, 0), abs=1e-12)
    x, y = clockwise_arc(0, 360, .5)
    assert len(x) == 181
    assert min(x) < -.49 and max(x) > .49
    assert (x[0], y[0]) == pytest.approx((x[-1], y[-1]), abs=1e-12)
    x, y = clockwise_arc(90, 0, .5)
    assert min(x) == max(x)


def test_zero_vectors_negative_lengths_and_signed_turns():
    assert xy_to_compass(0, 0) is None
    with pytest.raises(ValueError):
        compass_to_xy(40, -1)
    assert signed_turn(359, 1) == 2
    assert signed_turn(1, 359) == -2
    assert signed_turn(40, 130) == 90
    assert signed_turn(40, 310) == -90
