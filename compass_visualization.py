"""Plotly SVG figures. Geometry lives in geometry/navigation_scenarios."""

from dataclasses import dataclass

import plotly.graph_objects as go

from geometry import (clockwise_arc, compass_to_xy, format_angle,
                      format_bearing, relationships)
from navigation_scenarios import BezelState, SquareCourse, Track

COLORS = {
    "heading": "#007E80", "reciprocal": "#C35B14", "complementary": "#35773D",
    "supplementary": "#286AB4", "explementary": "#8054B7", "ink": "#172B3E",
    "muted": "#596E80", "grid": "#DCE5EB",
}


@dataclass(frozen=True)
class Layers:
    heading: bool = True
    reciprocal: bool = True
    explementary: bool = True
    heading_arc: bool = True
    reciprocal_arc: bool = False
    complementary_arc: bool = True
    supplementary_arc: bool = False
    explementary_arc: bool = True
    graduations: bool = True


def base_figure(height: int = 500, bound: float = 1.3) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white", plot_bgcolor="white", showlegend=False,
        font=dict(family="Arial, sans-serif", color=COLORS["ink"], size=12),
        xaxis=dict(range=[-bound, bound], visible=False, fixedrange=True,
                   constrain="domain"),
        yaxis=dict(range=[-bound, bound], visible=False, fixedrange=True,
                   scaleanchor="x", scaleratio=1, constrain="domain"),
        hoverlabel=dict(bgcolor="white", font_color=COLORS["ink"]),
        dragmode=False,
    )
    return fig


def line(fig: go.Figure, x, y, name: str, color: str, width: float = 2,
         dash: str = "solid", visible: bool = True, meta=None):
    fig.add_trace(go.Scatter(
        x=x, y=y, name=name, mode="lines", line=dict(color=color, width=width, dash=dash),
        visible=visible, hovertemplate=name + "<extra></extra>", meta=meta,
    ))


def arrow(fig: go.Figure, bearing: float, length: float, name: str,
          color: str, dash: str = "solid", visible: bool = True,
          origin=(0.0, 0.0), head_size: float = .065, width: float = 3):
    """A shaft and vector polygon head, with separate tips at coincidences."""
    dx, dy = compass_to_xy(bearing, length)
    tip = (origin[0] + dx, origin[1] + dy)
    line(fig, [origin[0], tip[0]], [origin[1], tip[1]], name, color,
         width, dash, visible, {"bearing": bearing, "kind": "arrow"})
    back = compass_to_xy(bearing, max(0, length - head_size))
    side = compass_to_xy(bearing + 90, head_size * .52)
    bx, by = origin[0] + back[0], origin[1] + back[1]
    fig.add_trace(go.Scatter(
        x=[tip[0], bx + side[0], bx - side[0], tip[0]],
        y=[tip[1], by + side[1], by - side[1], tip[1]],
        mode="lines", fill="toself", fillcolor=color,
        line=dict(color=color, width=1), name=name + " tip", visible=visible,
        hovertemplate=name + "<extra></extra>",
    ))


def compass_figure(heading: float, layers: Layers = Layers(),
                   animate: bool = True) -> go.Figure:
    r = relationships(heading)
    fig = base_figure()
    circle_x, circle_y = clockwise_arc(0, 360, 1.025)
    line(fig, circle_x, circle_y, "Compass rose", COLORS["grid"], 2)
    line(fig, [0, 0, None, -1, 1], [-1, 1, None, 0, 0],
         "North / east reference axes", COLORS["grid"], 1, "dot")
    ticks_x, ticks_y = [], []
    for d in range(0, 360, 5):
        a = compass_to_xy(d, .94 if d % 30 == 0 else .98)
        b = compass_to_xy(d, 1.025)
        ticks_x.extend([a[0], b[0], None])
        ticks_y.extend([a[1], b[1], None])
    line(fig, ticks_x, ticks_y, "5° graduations", COLORS["muted"], 1,
         visible=layers.graduations)
    for d in range(0, 360, 30):
        x, y = compass_to_xy(d, 1.145)
        cardinal = {0: "N", 90: "E", 180: "S", 270: "W"}.get(d)
        fig.add_annotation(
            x=x, y=y, text=f"<b>{cardinal}</b><br>{d:03d}°" if cardinal else f"{d:03d}°",
            font=dict(size=15 if cardinal else 11, color=COLORS["ink"] if cardinal else COLORS["muted"]),
            showarrow=False, visible=bool(cardinal) or layers.graduations,
        )
    # Arc endpoints represent sums. They are NOT arrows at the resulting measures.
    arcs = [
        ("heading", 0, r.heading, .87, layers.heading_arc, "N → heading"),
        ("reciprocal", r.heading, 180, .79, layers.reciprocal_arc, "heading → reciprocal"),
        ("complementary", r.heading, r.complementary, .71, layers.complementary_arc, "heading → E"),
        ("supplementary", r.heading, r.supplementary, .63, layers.supplementary_arc, "heading → S"),
        ("explementary", r.heading, r.explementary, .51, layers.explementary_arc, "heading → N, completing a turn"),
    ]
    for name, start, sweep, radius, enabled, description in arcs:
        x, y = clockwise_arc(start, sweep or 0, radius)
        label = f"{name.title()} arc: {format_angle(sweep)} · {description}"
        line(fig, x, y, label, COLORS[name], 3, "dot" if name == "explementary" else "solid",
             enabled and sweep is not None, {"kind": "arc", "relationship": name,
                                           "start": start, "sweep": sweep})
        # A point also makes zero-degree arcs discoverable through hover.
        fig.add_trace(go.Scatter(x=[x[-1]], y=[y[-1]], mode="markers",
                                marker=dict(color=COLORS[name], size=6),
                                name=label + " end", hovertemplate=label + "<extra></extra>",
                                visible=enabled and sweep is not None))
    # Distinct radii and stroke styles preserve identity when directions coincide.
    arrow(fig, r.heading, .94, f"H · Heading {format_bearing(r.heading)}",
          COLORS["heading"], visible=layers.heading, width=4)
    arrow(fig, r.reciprocal, .81, f"R · Reciprocal {format_bearing(r.reciprocal)}",
          COLORS["reciprocal"], "dash", layers.reciprocal)
    arrow(fig, r.explementary_direction, .60,
          f"X · Explementary direction {format_bearing(r.explementary_direction)}",
          COLORS["explementary"], "dot", layers.explementary, head_size=.08, width=3)
    fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers", marker=dict(
        size=11, color=COLORS["ink"], line=dict(color="white", width=2)), hoverinfo="skip"))
    fig.update_layout(
        uirevision="compass-fixed-frame",
        transition=dict(duration=180 if animate else 0, easing="cubic-in-out"),
        meta={"heading": r.heading, "reciprocal": r.reciprocal,
              "explementary_measure": r.explementary,
              "explementary_direction": r.explementary_direction},
    )
    return fig


def bezel_figure(state: BezelState) -> go.Figure:
    fig = base_figure(height=300, bound=1.25)
    x, y = clockwise_arc(0, 360, 1)
    line(fig, x, y, "Housing / rotating bezel", COLORS["grid"], 3)
    line(fig, [0, 0], [-.9, .9], "Lubber line (body forward)", COLORS["ink"], 1, "dot")
    arrow(fig, 0, 1.08, "Body forward", COLORS["ink"], width=1, head_size=.08)
    for offset in [-7, 7]:
        a, b = compass_to_xy(state.marker_relative + offset, .82), compass_to_xy(state.marker_relative + offset, 1.07)
        line(fig, [a[0], b[0]], [a[1], b[1]], "Bezel index markers", COLORS["reciprocal"], 5)
    arrow(fig, state.north_relative, .74, "N end → magnetic north", COLORS["heading"], width=4)
    arrow(fig, state.south_relative, .74, "S end → magnetic south", COLORS["explementary"], "dash", width=4)
    for label, angle, color in [("N", state.north_relative, COLORS["heading"]), ("S", state.south_relative, COLORS["explementary"])]:
        x, y = compass_to_xy(angle, .56)
        fig.add_annotation(x=x, y=y, text=f"<b>{label}</b>", showarrow=False,
                           bgcolor="white", font=dict(color=color, size=15))
    fig.add_annotation(x=0, y=1.18, text="FORWARD", showarrow=False, font=dict(size=10))
    return fig


def square_figure(course: SquareCourse) -> go.Figure:
    fig = go.Figure()
    for i, bearing in enumerate(course.bearings):
        a, b = course.points[i], course.points[i + 1]
        color = list(COLORS.values())[i]
        line(fig, [a[0], b[0]], [a[1], b[1]], f"Leg {i+1}: {format_bearing(bearing)}", color, 4)
        dx, dy = b[0] - a[0], b[1] - a[1]
        origin = (a[0] + dx * .46, a[1] + dy * .46)
        arrow(fig, bearing, (dx*dx + dy*dy)**.5 * .12, f"Leg {i+1}", color,
              origin=origin, head_size=(dx*dx + dy*dy)**.5 * .06)
        fig.add_annotation(x=(a[0]+b[0])/2, y=(a[1]+b[1])/2,
                           text=f"{i+1} · {format_bearing(bearing)}", showarrow=False,
                           yshift=17, bgcolor="white")
    fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text", text=["Start / finish"],
                            textposition="bottom center", marker=dict(size=12, color=COLORS["ink"])))
    return ground_axes(fig, "Equal legs • still water")


def ground_axes(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(height=420, title=dict(text=title, font_size=15), showlegend=False,
                      paper_bgcolor="white", plot_bgcolor="white",
                      margin=dict(l=50, r=30, t=50, b=50),
                      xaxis=dict(title="East (m)", zerolinecolor=COLORS["grid"], gridcolor="#EEF3F6"),
                      yaxis=dict(title="North (m)", scaleanchor="x", scaleratio=1,
                                 zerolinecolor=COLORS["grid"], gridcolor="#EEF3F6"),
                      font=dict(color=COLORS["ink"]), dragmode=False)
    return fig


def track_figure(track: Track, seconds: float) -> go.Figure:
    fig = go.Figure()
    sx, sy = (v * seconds for v in track.swim_velocity)
    cx, cy = (v * seconds for v in track.current_velocity)
    gx, gy = track.displacement
    for x, y, label, color, dash in [
        ([0, sx], [0, sy], "H · Swim through water", COLORS["heading"], "dash"),
        ([sx, sx+cx], [sy, sy+cy], "C · Current displacement", COLORS["explementary"], "dot"),
        ([0, gx], [0, gy], "T · Track over ground", COLORS["reciprocal"], "solid"),
    ]:
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=label,
                                line=dict(color=color, width=4, dash=dash),
                                marker=dict(size=7), hovertemplate=label + "<br>E %{x:.1f} m, N %{y:.1f} m<extra></extra>"))
    ground_axes(fig, f"Displacement after {seconds:g} s")
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-.28, x=0),
                      margin=dict(l=50, r=25, t=50, b=110), height=460)
    return fig
