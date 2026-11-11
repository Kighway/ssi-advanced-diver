from dataclasses import replace

import pytest

from rectangle_simulation import simulate_rectangle
from rectangle_visualization import RectangleLayers, rectangle_figure


@pytest.mark.parametrize("enabled", [True,False])
def test_plot_coordinates_match_simulation(enabled):
    sim = simulate_rectangle(current_enabled=enabled)
    fig = rectangle_figure(sim)
    for kind,points in [("planned_path",sim.planned_points),("actual_path",sim.actual_points)]:
        trace = next(t for t in fig.data if t.meta and t.meta.get("kind")==kind)
        assert tuple(zip(trace.x,trace.y)) == points
    assert fig.layout.meta["displacement"] == sim.displacement
    assert fig.layout.yaxis.scaleanchor == "x"
    assert fig.layout.yaxis.scaleratio == 1
    assert fig.layout.xaxis.range[0] < min(p[0] for p in sim.actual_points)
    assert fig.layout.yaxis.range[1] > max(p[1] for p in sim.actual_points)


@pytest.mark.parametrize("layer", ["planned","actual","current","headings"])
def test_each_visual_layer_can_be_hidden(layer):
    fig = rectangle_figure(simulate_rectangle(),replace(RectangleLayers(),**{layer:False}))
    if layer in {"planned","actual"}:
        trace = next(t for t in fig.data if t.meta and t.meta.get("kind")==layer+"_path")
        assert trace.visible is False
    elif layer=="current":
        assert all(t.visible is False for t in fig.data if t.name.startswith("Current at turn"))
    else:
        assert all("H " not in a.text and "T " not in a.text for a in fig.layout.annotations)
    endpoint = next(t for t in fig.data if t.meta and t.meta.get("kind")=="actual_endpoint")
    assert endpoint.x[0] == pytest.approx(simulate_rectangle().displacement[0])


def test_stationary_leg_has_no_invalid_track_arrow():
    fig = rectangle_figure(simulate_rectangle(0,current_bearing=180,current_speed=1))
    assert not any(t.name.startswith("Leg 1 track") for t in fig.data)
    assert "Undefined" in " ".join(a.text for a in fig.layout.annotations)
    fig.to_json()  # JSON serializable even with a zero ground velocity.
