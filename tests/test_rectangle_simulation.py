from math import atan2, degrees, hypot, radians, tan

import pytest

from geometry import compass_to_xy, normalize_angle
from rectangle_simulation import (DEFAULT_CURRENT_SPEED, calibrate_current_speed,
                                  perpendicular_current, simulate_rectangle)


@pytest.mark.parametrize("heading,expected", [
    (60,(60,150,240,330)), (330,(330,60,150,240)),
    (359,(359,89,179,269)), (-1,(359,89,179,269)), (400,(40,130,220,310)),
])
def test_clockwise_progression_and_wraparound(heading, expected):
    assert tuple(leg.heading for leg in simulate_rectangle(heading).legs) == expected


@pytest.mark.parametrize("heading", [0,40,60,90,180,270,359])
@pytest.mark.parametrize("enabled,speed", [(False,.8),(True,0)])
def test_exact_closure_without_current(heading, enabled, speed):
    sim = simulate_rectangle(heading, current_speed=speed, current_enabled=enabled)
    assert sim.planned_points[-1] == (0,0)
    assert sim.actual_points == sim.planned_points
    assert sim.displacement == (0,0)
    assert sim.displacement_distance == 0
    assert sim.displacement_bearing is None
    assert sim.effective_current_speed == 0


def test_default_scenario_analytic_values():
    sim = simulate_rectangle()
    assert DEFAULT_CURRENT_SPEED == pytest.approx(.17632698070846498)
    assert [leg.swim_distance for leg in sim.legs] == [40,20,40,20]
    assert [leg.duration for leg in sim.legs] == [40,20,40,20]
    assert [leg.track_bearing for leg in sim.legs] == pytest.approx([70,150,230,330])
    assert [leg.drift_angle for leg in sim.legs] == pytest.approx([10,0,-10,0])
    assert [leg.ground_speed for leg in sim.legs] == pytest.approx([
        hypot(1,DEFAULT_CURRENT_SPEED),1+DEFAULT_CURRENT_SPEED,
        hypot(1,DEFAULT_CURRENT_SPEED),1-DEFAULT_CURRENT_SPEED])
    assert sim.total_time == 120
    assert sim.total_swim_distance == 120
    assert sim.displacement_distance == pytest.approx(21.1592376850158)
    assert sim.displacement_bearing == pytest.approx(150)
    assert sim.displacement == pytest.approx((10.5796188425079,-18.3244373599367))


@pytest.mark.parametrize("heading", [0,17,60,200,359])
@pytest.mark.parametrize("current_bearing", [0,37,90,180,333])
def test_arbitrary_vectors_integrate_using_actual_leg_time(heading,current_bearing):
    sim = simulate_rectangle(heading,23,7,.7,current_bearing,.4)
    for leg in sim.legs:
        assert leg.duration == pytest.approx(leg.swim_distance/.7)
        planned_delta = tuple(b-a for a,b in zip(leg.planned_start,leg.planned_end))
        ground_delta = tuple(b-a for a,b in zip(leg.actual_start,leg.actual_end))
        assert planned_delta == pytest.approx(compass_to_xy(leg.heading,leg.swim_distance))
        assert ground_delta == pytest.approx(tuple(v*leg.duration for v in leg.ground_velocity))
        assert leg.ground_velocity == pytest.approx(tuple(a+b for a,b in zip(leg.swim_velocity,sim.current_velocity)))
        assert hypot(*ground_delta) == pytest.approx(leg.ground_distance)
    assert sim.displacement == pytest.approx(tuple(v*sim.total_time for v in sim.current_velocity))
    assert sim.displacement_bearing == pytest.approx(current_bearing)


def test_all_integer_headings_close_and_do_not_rotate_world_current():
    for heading in range(360):
        sim = simulate_rectangle(heading)
        assert sim.planned_points[-1] == (0,0)
        assert sim.current_bearing == 150
        assert sim.displacement_distance == pytest.approx(120*DEFAULT_CURRENT_SPEED)
        assert sim.displacement_bearing == pytest.approx(150)


def test_perpendicular_calibration_left_right_and_oblique_drift():
    assert calibrate_current_speed(1,10) == pytest.approx(DEFAULT_CURRENT_SPEED)
    assert calibrate_current_speed(1,-10) == pytest.approx(DEFAULT_CURRENT_SPEED)
    assert perpendicular_current(60,150)
    assert perpendicular_current(60,330)
    assert perpendicular_current(359,89)
    assert not perpendicular_current(60,120)
    left = simulate_rectangle(current_bearing=330)
    assert left.legs[0].drift_angle == pytest.approx(-10)
    oblique = simulate_rectangle(current_bearing=120)
    expected = degrees(atan2(DEFAULT_CURRENT_SPEED*3**.5/2,1+DEFAULT_CURRENT_SPEED/2))
    assert oblique.legs[0].drift_angle == pytest.approx(expected)
    assert oblique.legs[0].drift_angle != pytest.approx(10)


@pytest.mark.parametrize("speed,ground_speed,track", [(.5,.5,0),(1,0,None),(2,1,180)])
def test_opposing_current_slows_stops_and_reverses(speed,ground_speed,track):
    sim = simulate_rectangle(0,current_bearing=180,current_speed=speed)
    leg = sim.legs[0]
    assert leg.ground_speed == pytest.approx(ground_speed,abs=1e-12)
    if track is None:
        assert leg.track_bearing is None
        assert leg.drift_angle is None
    else:
        assert leg.track_bearing == pytest.approx(track)
    assert leg.actual_end[1] == pytest.approx(40*(1-speed))


def test_speed_distance_and_elapsed_time_scaling():
    slow = simulate_rectangle(swim_speed=.5)
    fast = simulate_rectangle(swim_speed=2)
    assert slow.total_time == 240
    assert fast.total_time == 60
    assert slow.displacement_distance == pytest.approx(fast.displacement_distance*4)
    doubled = simulate_rectangle(length=80,width=40)
    default = simulate_rectangle()
    assert doubled.total_time == default.total_time*2
    assert doubled.displacement_distance == pytest.approx(default.displacement_distance*2)
    # Recalibrating the current to preserve 10° is a different experiment.
    calibrated = simulate_rectangle(swim_speed=2,current_speed=calibrate_current_speed(2,10))
    assert calibrated.legs[0].drift_angle == pytest.approx(10)
    assert calibrated.displacement_distance == pytest.approx(default.displacement_distance)


@pytest.mark.parametrize("change", [17,90,180,359])
def test_rotating_heading_and_current_rotates_entire_solution(change):
    default = simulate_rectangle()
    rotated = simulate_rectangle(60+change,current_bearing=150+change)
    for a,b in zip(default.legs,rotated.legs):
        assert b.track_bearing == pytest.approx(normalize_angle(a.track_bearing+change))
        assert b.ground_speed == pytest.approx(a.ground_speed)
        assert b.drift_angle == pytest.approx(a.drift_angle)
    assert rotated.displacement_bearing == pytest.approx(normalize_angle(150+change))


@pytest.mark.parametrize("kwargs", [
    {"length":0}, {"width":-1}, {"swim_speed":0}, {"current_speed":-1},
    {"length":float("nan")}, {"current_bearing":float("inf")},
])
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        simulate_rectangle(**kwargs)


@pytest.mark.parametrize("angle", [-90,90,120,float("nan")])
def test_invalid_drift_calibration(angle):
    with pytest.raises(ValueError):
        calibrate_current_speed(1,angle)
