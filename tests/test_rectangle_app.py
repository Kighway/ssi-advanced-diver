import json
from math import atan, degrees, radians, tan
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1]/"app.py"


def start():
    at = AppTest.from_file(str(APP)).run(timeout=20)
    at.toggle(key="dive_mode").set_value(True).run()
    at.radio(key="exercise").set_value("Rectangle with Current").run()
    assert not at.exception
    return at


def plot(at):
    assert not at.exception
    return json.loads(at.get("plotly_chart")[-1].proto.spec)


def test_rectangle_defaults_preserve_original_explorer():
    at = start()
    assert at.slider(key="heading_slider").value == 40
    assert at.number_input(key="rect_heading").value == 60
    table = at.dataframe[0].value
    assert table["Compass heading"].tolist() == ["060°","150°","240°","330°"]
    assert table["Actual track"].tolist() == ["070.0°","150.0°","230.0°","330.0°"]
    assert table["Swim time (s)"].tolist() == [40,20,40,20]
    assert plot(at)["layout"]["meta"]["total_time"] == 120
    assert "-0.0°" not in " ".join(m.value for m in at.markdown)


def test_drift_and_speed_synchronize_both_directions():
    at = start()
    at.number_input(key="rect_drift").set_value(20.0).run()
    assert at.number_input(key="rect_current_speed").value == pytest.approx(tan(radians(20)))
    at.number_input(key="rect_current_speed").set_value(.5).run()
    assert at.number_input(key="rect_drift").value == pytest.approx(degrees(atan(.5)))
    at.number_input(key="rect_swim_speed").set_value(2.0).run()
    assert at.number_input(key="rect_current_speed").value == .5
    assert at.number_input(key="rect_drift").value == pytest.approx(degrees(atan(.25)))
    assert plot(at)["layout"]["meta"]["total_time"] == 60


def test_world_current_is_independent_until_relative_mode_selected():
    at = start()
    at.number_input(key="rect_heading").set_value(100).run()
    assert at.number_input(key="rect_current_bearing").value == 150
    assert "rect_drift" not in [w.key for w in at.number_input]
    at.checkbox(key="rect_relative").check().run()
    assert at.number_input(key="rect_current_bearing").value == 190
    at.number_input(key="rect_heading").set_value(359).run()
    assert at.number_input(key="rect_current_bearing").value == 89
    assert at.number_input(key="rect_current_bearing").disabled
    assert at.slider(key="heading_slider").value == 40
    assert plot(at)["layout"]["meta"]["heading"] == 359


def test_zero_current_plot_table_and_restore():
    at = start()
    configured = at.number_input(key="rect_current_speed").value
    at.toggle(key="rect_enabled").set_value(False).run()
    traces = plot(at)["data"]
    planned = next(t for t in traces if t.get("meta",{}).get("kind")=="planned_path")
    actual = next(t for t in traces if t.get("meta",{}).get("kind")=="actual_path")
    assert planned["x"] == actual["x"] and planned["y"] == actual["y"]
    assert at.dataframe[0].value["Ground speed (m/s)"].tolist() == [1,1,1,1]
    assert at.number_input(key="rect_current_speed").value == configured
    at.toggle(key="rect_enabled").set_value(True).run()
    assert plot(at)["layout"]["meta"]["current_speed"] == configured


def test_reset_lengths_layers_and_existing_heading_are_independent():
    at = start()
    at.number_input(key="rect_length").set_value(80.0).run()
    assert plot(at)["layout"]["meta"]["total_time"] == 200
    at.checkbox(key="rect_actual").uncheck().run()
    assert next(t for t in plot(at)["data"] if t.get("meta",{}).get("kind")=="actual_path")["visible"] is False
    at.number_input(key="heading_number").set_value(270).run()
    assert at.number_input(key="rect_heading").value == 60
    at.button(key="rect_reset").click().run()
    assert not at.exception
    assert at.number_input(key="rect_length").value == 40
    assert at.number_input(key="rect_drift").value == pytest.approx(10)
    assert at.checkbox(key="rect_actual").value is True
    assert at.slider(key="heading_slider").value == 270


def test_oblique_and_opposing_current_render_without_errors():
    at = start()
    at.number_input(key="rect_current_bearing").set_value(240).run()
    at.number_input(key="rect_current_speed").set_value(1.0).run()
    assert at.dataframe[0].value["Actual track"].iloc[0] == "Undefined"
    at.number_input(key="rect_current_speed").set_value(2.0).run()
    assert at.dataframe[0].value["Actual track"].iloc[0] == "240.0°"
    assert not at.exception
