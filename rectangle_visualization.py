"""SVG Plotly presentation for the rectangle model; no Streamlit dependency."""

from dataclasses import dataclass
from math import hypot

import plotly.graph_objects as go

from compass_visualization import COLORS, arrow, ground_axes
from geometry import format_bearing
from rectangle_simulation import RectangleSimulation

PLANNED_COLOR = "#748391"
ACTUAL_COLOR = COLORS["supplementary"]
CURRENT_COLOR = COLORS["heading"]
DISPLACEMENT_COLOR = COLORS["reciprocal"]
CURRENT_VECTOR_SECONDS = 20.0


@dataclass(frozen=True)
class RectangleLayers:
    planned: bool = True
    actual: bool = True
    current: bool = True
    headings: bool = True


def rectangle_figure(sim: RectangleSimulation,
                     layers: RectangleLayers = RectangleLayers()) -> go.Figure:
    fig = go.Figure()
    # Use the same world bounds for all toggle combinations to prevent jumps.
    current_tips = [(p[0] + sim.current_velocity[0] * CURRENT_VECTOR_SECONDS,
                     p[1] + sim.current_velocity[1] * CURRENT_VECTOR_SECONDS)
                    for p in sim.actual_points[1:4]]
    points = list(sim.planned_points) + list(sim.actual_points) + current_tips
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1)
    for kind, route, color, dash, visible, symbol in [
        ("planned", sim.planned_points, PLANNED_COLOR, "dash", layers.planned, "circle-open"),
        ("actual", sim.actual_points, ACTUAL_COLOR, "solid", layers.actual, "circle"),
    ]:
        fig.add_trace(go.Scatter(
            x=[p[0] for p in route], y=[p[1] for p in route],
            mode="lines+markers", name=f"{kind.title()} path", visible=visible,
            line=dict(color=color, width=3, dash=dash),
            marker=dict(size=9, color=color, symbol=symbol),
            customdata=list(range(5)), meta={"kind": f"{kind}_path"},
            hovertemplate=f"{kind.title()} point %{{customdata}}<br>East %{{x:.2f}} m<br>North %{{y:.2f}} m<extra></extra>",
        ))
    for leg in sim.legs:
        for actual, enabled, color in [(False, layers.planned, PLANNED_COLOR),
                                        (True, layers.actual, ACTUAL_COLOR)]:
            start = leg.actual_start if actual else leg.planned_start
            end = leg.actual_end if actual else leg.planned_end
            bearing = leg.track_bearing if actual else leg.heading
            length = hypot(end[0] - start[0], end[1] - start[1])
            if bearing is not None and length > 1e-9:
                origin = tuple(start[j] + .47 * (end[j] - start[j]) for j in (0, 1))
                arrow(fig, bearing, length * .14,
                      f"Leg {leg.number} {'track' if actual else 'heading'} {format_bearing(bearing, 1)}",
                      color, visible=enabled, origin=origin,
                      head_size=min(span * .025, length * .09), width=2)
            # Distance labels are through-water distances on planned legs.
            # Actual labels use T for track; H is reserved for compass heading.
            if not actual or layers.headings:
                label = (f"T {format_bearing(leg.track_bearing, 1)}" if actual else
                         f"{leg.swim_distance:g} m swim" +
                         (f"<br>H {format_bearing(leg.heading)}" if layers.headings else ""))
                fig.add_annotation(
                    x=(start[0]+end[0])/2, y=(start[1]+end[1])/2,
                    text=label, showarrow=False, visible=enabled,
                    yshift=-22 if actual else 23, bgcolor="rgba(255,255,255,0.9)",
                    font=dict(size=10, color=color),
                )
        if leg.number < 4:
            for p, label, enabled, color, shift in [
                (leg.planned_end, f"P{leg.number}", layers.planned, PLANNED_COLOR, 14),
                (leg.actual_end, str(leg.number), layers.actual, ACTUAL_COLOR, -16),
            ]:
                fig.add_annotation(x=p[0], y=p[1], text=f"<b>{label}</b>",
                                   showarrow=False, visible=enabled, xshift=shift,
                                   yshift=16 if label.startswith("P") else -14,
                                   bgcolor="rgba(255,255,255,0.95)",
                                   font=dict(color=color, size=12))
    # These are velocity vectors drawn at a stated time scale on metre axes.
    for i, p in enumerate(sim.actual_points[1:4], 1):
        if sim.effective_current_speed > 0:
            arrow(fig, sim.current_bearing, sim.effective_current_speed * CURRENT_VECTOR_SECONDS,
                  f"Current at turn {i}: {sim.effective_current_speed:.4f} m/s toward {format_bearing(sim.current_bearing)} (20 s scale)",
                  CURRENT_COLOR, "dot", layers.current, origin=p,
                  head_size=min(span * .02, sim.effective_current_speed * 4), width=2)

    if sim.displacement_bearing is not None:
        arrow(fig, sim.displacement_bearing, sim.displacement_distance,
              f"Net displacement: {sim.displacement_distance:.2f} m toward {format_bearing(sim.displacement_bearing, 1)}",
              DISPLACEMENT_COLOR, "dashdot", head_size=min(span * .035, sim.displacement_distance * .15), width=3)
        fig.add_trace(go.Scatter(
            x=[sim.displacement[0]], y=[sim.displacement[1]], mode="markers+text",
            marker=dict(symbol="diamond", color=DISPLACEMENT_COLOR, size=12),
            text=["4 / finish"], textposition="bottom center",
            name="Actual endpoint", meta={"kind":"actual_endpoint"},
            hovertemplate="Finish<br>East %{x:.2f} m<br>North %{y:.2f} m<extra></extra>",
        ))
    fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text",
                            marker=dict(size=10, color=COLORS["ink"]),
                            text=["0 / start" if sim.displacement_bearing is not None else "0 / start = 4 / finish"],
                            textposition="top left", name="Start", hoverinfo="name"))
    ground_axes(fig, "Planned rectangle & actual seabed track")
    padding = span * .20
    fig.update_layout(
        height=560, margin=dict(l=48, r=24, t=48, b=45), showlegend=False,
        xaxis=dict(range=[min(xs)-padding, max(xs)+padding], fixedrange=True,
                   constrain="domain"),
        yaxis=dict(range=[min(ys)-padding, max(ys)+padding], fixedrange=True,
                   scaleanchor="x", scaleratio=1, constrain="domain"),
        meta={"kind":"rectangle", "heading":sim.initial_heading,
              "current_bearing":sim.current_bearing,
              "current_speed":sim.effective_current_speed,
              "displacement":sim.displacement, "total_time":sim.total_time},
    )
    fig.add_annotation(xref="paper", yref="paper", x=1, y=1,
                       text="<b>N ↑</b><br>E →", showarrow=False,
                       font=dict(color=COLORS["ink"], size=12), bgcolor="white")
    return fig
