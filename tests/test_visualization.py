from dataclasses import replace

import pytest

from compass_visualization import Layers, compass_figure
from geometry import compass_to_xy


@pytest.mark.parametrize("heading", [0, 40, 90, 180, 270, 359])
def test_figure_bearings_match_model(heading):
    fig = compass_figure(heading)
    arrows = [t for t in fig.data if t.meta and t.meta.get("kind") == "arrow"]
    bearings = [heading, (heading + 180) % 360, (360 - heading) % 360]
    for trace, bearing, radius in zip(arrows, bearings, [.94, .81, .60]):
        assert trace.meta["bearing"] == bearing
        assert (trace.x[-1], trace.y[-1]) == pytest.approx(compass_to_xy(bearing, radius))
    assert fig.layout.meta["heading"] == heading


@pytest.mark.parametrize("heading", [90, 270])
def test_coincidence_preserves_two_tips(heading):
    fig = compass_figure(heading)
    tips = [t for t in fig.data if t.name and t.name.startswith(("R ·", "X ·")) and t.name.endswith("tip")]
    assert len(tips) == 2
    assert (tips[0].x[0], tips[0].y[0]) != (tips[1].x[0], tips[1].y[0])


def test_zero_full_turn_and_invalid_arcs():
    fig = compass_figure(0)
    arc = next(t for t in fig.data if t.meta and t.meta.get("relationship") == "explementary")
    assert arc.meta["sweep"] == 360
    assert min(arc.x) < -.5 and max(arc.x) > .5
    fig = compass_figure(359, Layers(supplementary_arc=True))
    for t in fig.data:
        if t.meta and t.meta.get("relationship") in {"complementary", "supplementary"}:
            assert not t.visible


@pytest.mark.parametrize("layer", ["heading", "reciprocal", "explementary"])
def test_independent_arrow_layers(layer):
    fig = compass_figure(40, replace(Layers(), **{layer:False}))
    for t in fig.data:
        if t.meta and t.meta.get("kind") == "arrow":
            assert t.visible == (layer.title() not in t.name)
