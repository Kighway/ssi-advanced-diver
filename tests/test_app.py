import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def figure(at):
    return json.loads(at.get("plotly_chart")[0].proto.spec)


def assert_synced(at, heading):
    assert not at.exception
    assert at.slider(key="heading_slider").value == heading
    assert at.number_input(key="heading_number").value == heading
    assert at.session_state["heading"] == heading
    meta = figure(at)["layout"]["meta"]
    assert meta["heading"] == heading
    assert meta["reciprocal"] == (heading + 180) % 360
    assert meta["explementary_measure"] == 360 - heading
    return " ".join(m.value for m in at.markdown)


def test_initial_dashboard():
    at = AppTest.from_file(str(APP)).run(timeout=20)
    markup = assert_synced(at, 40)
    for result in ["220°", "050°", "140°", "320°"]:
        assert result in markup
    assert at.toggle(key="dive_mode").value is False


@pytest.mark.parametrize("heading", [0, 40, 90, 180, 270, 359])
def test_slider_updates_all(heading):
    at = AppTest.from_file(str(APP)).run(timeout=20)
    at.slider(key="heading_slider").set_value(heading).run()
    assert_synced(at, heading)


def test_numeric_sync_reset_and_boundaries():
    at = AppTest.from_file(str(APP)).run(timeout=20)
    for heading in [91, 181, 359, 0]:
        at.number_input(key="heading_number").set_value(heading).run()
        markup = assert_synced(at, heading)
        if heading > 180:
            assert markup.count('class="calc-value">N/A') == 2
        elif heading > 90:
            assert markup.count('class="calc-value">N/A') == 1
        if heading == 0:
            assert 'class="calc-value">360°' in markup
    at.button[0].click().run()
    assert_synced(at, 40)


def test_layers_and_exercises():
    at = AppTest.from_file(str(APP)).run(timeout=20)
    at.checkbox(key="layer_reciprocal").uncheck().run()
    reciprocal = next(t for t in figure(at)["data"] if t.get("meta", {}).get("kind") == "arrow" and t["name"].startswith("R ·"))
    assert reciprocal["visible"] is False
    at.toggle(key="dive_mode").set_value(True).run()
    assert not at.exception
    assert len(at.get("plotly_chart")) == 4
    for experiment in ["90° turns & square", "Heading vs. track"]:
        at.radio(key="exercise").set_value(experiment).run()
        assert not at.exception
        assert len(at.get("plotly_chart")) == 2
    at.number_input(key="heading_number").set_value(270).run()
    assert_synced(at, 270)
