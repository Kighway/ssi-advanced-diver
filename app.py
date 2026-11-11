"""Run with: streamlit run app.py"""

from html import escape

import streamlit as st

from compass_visualization import (COLORS, Layers, bezel_figure, compass_figure,
                                   square_figure, track_figure)
from geometry import format_angle, format_bearing, relationships
from navigation_scenarios import bezel_state, current_track, square_course, turn_90
from rectangle_view import render_rectangle_exercise

st.set_page_config(page_title="Compass Geometry Laboratory", page_icon="🧭", layout="wide")

st.markdown("""<style>
.stApp {background: #F6F8FA;}
.block-container {max-width: 1320px; padding: 2rem 2.2rem 2.5rem;}
header[data-testid="stHeader"] {background: transparent;}
[data-testid="stAppDeployButton"] {display:none;}
h1 {letter-spacing:-.045em; font-size:2.65rem !important; padding-top:.1rem !important;}
h3 {letter-spacing:-.02em;}
.eyebrow {color:#007E80; font-size:.73rem; letter-spacing:.17em; font-weight:750; margin:0 0 .55rem;}
.subtitle {color:#596E80; font-size:1.04rem; margin:0 0 1rem;}
.calc-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:10px 0 20px;}
.calc-card {background:white; border:1px solid #DCE5EB; border-top:3px solid var(--accent); border-radius:12px; padding:17px 18px; min-width:0;}
.calc-title {font-size:.85rem; font-weight:700; color:#172B3E;}
.calc-type {font-size:.67rem; letter-spacing:.07em; color:#596E80; margin-top:3px; text-transform:uppercase;}
.calc-value {font-size:2.45rem; line-height:1.3; letter-spacing:-.04em; font-weight:750; color:var(--accent); margin:7px 0;}
.calc-formula {font-size:.8rem; font-family:ui-monospace,monospace; color:#334B60;}
.calc-note {font-size:.75rem; color:#596E80; line-height:1.5; margin-top:8px; min-height:2.25em;}
.readout {display:flex; flex-wrap:wrap; gap:10px 20px; font-size:.83rem; color:#334B60; margin:0 0 12px;}
.readout span {white-space:nowrap;}
.key {display:inline-block; width:24px; margin-right:6px; vertical-align:middle; border-top:3px solid var(--accent);}
.panel-title {font-weight:750; font-size:1.12rem; margin:0;}
.panel-note {font-size:.78rem; color:#596E80; margin:4px 0 8px;}
.lesson {background:#EAF4F4; border-left:3px solid #007E80; border-radius:0 10px 10px 0; padding:16px 18px; color:#213E4D; font-size:.94rem; line-height:1.6;}
.lesson p:last-child {margin-bottom:0;}
.footer {border-top:1px solid #DCE5EB; padding-top:14px; color:#596E80; font-size:.75rem; margin-top:24px;}
div[data-testid="stVerticalBlockBorderWrapper"]>div {border-color:#DCE5EB;}
@media (max-width:900px) {.calc-grid {grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width:600px) {
 .block-container {padding:1rem .85rem 2rem;} h1 {font-size:2rem !important;}
 .calc-card {padding:13px 12px;} .calc-value {font-size:2rem;}
 .calc-formula {font-size:.71rem;} .calc-grid {gap:9px;}
 div[data-testid="stPlotlyChart"] {min-width:0;}
}
@media (prefers-reduced-motion:reduce) {* {scroll-behavior:auto !important;}}
</style>""", unsafe_allow_html=True)


def sync_heading(source: str):
    value = int(st.session_state[source])
    st.session_state.heading = value
    st.session_state.heading_slider = value
    st.session_state.heading_number = value


def reset_heading():
    for key in ("heading", "heading_slider", "heading_number"):
        st.session_state[key] = 40


if "heading" not in st.session_state:
    reset_heading()

st.markdown('<p class="eyebrow">SSI AOW STUDY COMPANION / NAVIGATION LAB</p>', unsafe_allow_html=True)
st.title("Compass Geometry Explorer")
st.markdown('<p class="subtitle">One bearing, four different relationships. Turn a heading into understanding.</p>', unsafe_allow_html=True)

with st.container(border=True):
    control, numeric, reset = st.columns([6, 1.7, 1.6], vertical_alignment="bottom")
    with control:
        st.slider("Heading · clockwise from north", 0, 359, key="heading_slider",
                  format="%03d°", on_change=sync_heading, args=("heading_slider",))
    with numeric:
        st.number_input("Heading (degrees)", 0, 359, step=1, format="%03d",
                        key="heading_number", on_change=sync_heading, args=("heading_number",))
    with reset:
        st.button("Reset to 040°", on_click=reset_heading, use_container_width=True)

r = relationships(st.session_state.heading)
h = format_bearing(r.heading)
rec = format_bearing(r.reciprocal)
ex = format_angle(r.explementary)
exdir = format_bearing(r.explementary_direction)


def card(kind, title, value, formula, note, operation="Angle measure"):
    return f'''<div class="calc-card" data-relationship="{kind}" style="--accent:{COLORS[kind]}">
<div class="calc-title">{title}</div><div class="calc-type">{operation}</div>
<div class="calc-value">{format_angle(value)}</div><div class="calc-formula">{escape(formula)}</div>
<div class="calc-note">{escape(note)}</div></div>'''


cards = [
    card("reciprocal", "01 / Reciprocal", r.reciprocal, f"({h} + 180°) mod 360°",
         "Reverse the direction of travel.", "Navigation operation"),
    card("complementary", "02 / Complementary", r.complementary, f"090° − {h}",
         "Together, the angles make 090°." if r.complementary is not None else "N/A: heading exceeds 090°; the difference would be negative."),
    card("supplementary", "03 / Supplementary", r.supplementary, f"180° − {h}",
         "Together, the angles make 180°." if r.supplementary is not None else "N/A: heading exceeds 180°; the difference would be negative."),
    card("explementary", "04 / Explementary", r.explementary, f"360° − {h}",
         f"Full-turn remainder. Plotted direction: {exdir}."),
]
st.markdown('<div class="calc-grid">' + "".join(cards) + '</div>', unsafe_allow_html=True)

chart_col, explanation_col = st.columns([1.65, 1], gap="large")

# Construct layer state before drawing so a single rerun updates every element.
with explanation_col:
    st.markdown('<p class="panel-title">Read the relationships</p>', unsafe_allow_html=True)
    lesson = f"<p>Facing <b>{h}</b>, your reciprocal is <b>{rec}</b>: a half-turn from your original heading.</p>"
    if r.complementary is not None:
        lesson += f"<p><b>{h} + {format_angle(r.complementary)} = 090°.</b> The complementary arc fills the gap from your heading to east.</p>"
    else:
        lesson += f"<p><b>No nonnegative complement:</b> {h} is already greater than 090°.</p>"
    if r.supplementary is not None:
        lesson += f"<p><b>{h} + {format_angle(r.supplementary)} = 180°.</b> The supplementary arc fills the gap to south.</p>"
    else:
        lesson += f"<p><b>No nonnegative supplement:</b> {h} is already greater than 180°.</p>"
    lesson += f"<p>The explement is <b>{ex}</b>. Its arc completes the turn from {h} back to north. The dotted arrow separately plots {ex} clockwise <b>from north</b>, at {exdir}.</p>"
    if r.heading == 0:
        lesson += "<p><b>360° is a full turn, not a zero-sized angle.</b> Its endpoint direction is 000°.</p>"
    if r.reciprocal == r.explementary_direction:
        lesson += f"<p><b>Coincidence at {rec}:</b> reciprocal and explementary direction share a ray here. The longer dashed orange arrow and shorter dotted purple arrow remain separate.</p>"
    st.markdown(f'<div class="lesson" aria-live="polite">{lesson}</div>', unsafe_allow_html=True)
    st.caption("Only the reciprocal is defined as a reversal. Angle measures become compass directions only when you choose a reference and rotation sense.")
    with st.expander("Visual layers", expanded=False):
        st.caption("Arrows · independent directions from north")
        lh = st.checkbox("H · Heading arrow (solid teal)", True, key="layer_heading")
        lr = st.checkbox("R · Reciprocal arrow (dashed orange)", True, key="layer_reciprocal")
        lx = st.checkbox("X · Explementary arrow (dotted purple)", True, key="layer_explementary")
        st.caption("Concentric arcs · clockwise sweeps")
        ha = st.checkbox("Heading arc · N → heading", True, key="arc_heading")
        ra = st.checkbox("Reciprocal arc · heading + 180°", False, key="arc_reciprocal")
        ca = st.checkbox("Complementary arc · heading → E", True, key="arc_complementary")
        sa = st.checkbox("Supplementary arc · heading → S", False, key="arc_supplementary")
        xa = st.checkbox("Explementary arc · heading → N", True, key="arc_explementary")
        st.caption("Unavailable arcs disappear automatically. A zero-sized arc is a point.")
        gr = st.checkbox("Degree graduations", True, key="graduations")
        animate = st.checkbox("Short chart transitions", True, key="animate",
                              help="Updates commit on slider release. Turn off for reduced motion.")
    layers = Layers(lh, lr, lx, ha, ra, ca, sa, xa, gr)

with chart_col:
    with st.container(border=True):
        st.markdown(f'<p class="panel-title">Heading {h}</p><p class="panel-note">NORTH UP · CLOCKWISE POSITIVE · 5° GRADUATIONS</p>', unsafe_allow_html=True)
        st.plotly_chart(compass_figure(r.heading, layers, animate), use_container_width=True,
                        key="compass", theme=None,
                        config={"displayModeBar": False, "scrollZoom": False, "responsive": True})
        legend = []
        for label, value, color, style in [("H · Heading", h, COLORS["heading"], "solid"),
                                          ("R · Reciprocal", rec, COLORS["reciprocal"], "dashed"),
                                          ("X · Explementary direction", exdir, COLORS["explementary"], "dotted")]:
            legend.append(f'<span><i class="key" style="--accent:{color};border-top-style:{style}"></i>{label} <b>{value}</b></span>')
        st.markdown('<div class="readout">' + "".join(legend) + '</div>', unsafe_allow_html=True)
        arc_legend = []
        for kind, value, enabled in [
            ("heading", r.heading, ha), ("reciprocal", 180, ra),
            ("complementary", r.complementary, ca),
            ("supplementary", r.supplementary, sa),
            ("explementary", r.explementary, xa),
        ]:
            if enabled and value is not None:
                arc_legend.append(f'<span><i class="key" style="--accent:{COLORS[kind]}"></i>{kind.title()} arc <b>{format_angle(value)}</b></span>')
        if arc_legend:
            st.markdown('<div class="readout">' + "".join(arc_legend) + '</div>', unsafe_allow_html=True)
        st.caption("H is longest, R is intermediate, X is shortest. Hover over an arrow or arc for its value. Lengths distinguish layers; they do not represent distance.")

with st.expander("Angle measures vs. compass directions"):
    st.markdown(f"""**An angle measure is an amount of rotation; a bearing also specifies a reference.**

| Relationship | What is calculated at {h}? | Arc on the compass |
|---|---|---|
| Reciprocal | Add 180° to the heading, then wrap → **{rec}** | 180° clockwise from the heading |
| Complementary | Nonnegative remainder to 090° → **{format_angle(r.complementary)}** | Heading to east, when available |
| Supplementary | Nonnegative remainder to 180° → **{format_angle(r.supplementary)}** | Heading to south, when available |
| Explementary | Remainder to 360° → **{ex}** | Heading onward to north |

The purple **arrow** uses the explementary *measure* as a new clockwise bearing
from north ({exdir}); it is the reflection of the original direction across the
north–south axis. The purple **arc** starts at the original heading and ends at
north. These are distinct constructions. Reciprocal and explementary directions
coincide only at headings 090° and 270°. No modulo operation is applied to a
negative complement or supplement to make it appear valid.
""")

st.divider()
dive_mode = st.toggle("Dive Navigation Mode", value=False, key="dive_mode",
                      help="Open bezel, turns, square, cross-current, and rectangle experiments below.")

if dive_mode:
    st.subheader("From geometry to a dive route")
    st.caption(f"The first three exercises use heading {h}. Rectangle with Current has its own scenario controls. North means magnetic north throughout this lab.")
    exercise = st.radio("Experiment", ["Return & bezel", "90° turns & square", "Heading vs. track", "Rectangle with Current"],
                        horizontal=True, key="exercise")
    if exercise == "Return & bezel":
        st.markdown(f"### Outbound {h} → reciprocal return {rec}")
        st.write("Both return methods require you to turn your body 180°. The lubber line stays aligned with your forward direction. Rotating the bezel alone does not turn the diver.")
        columns = st.columns(3)
        scenes = [("outbound", "1 / Outbound reference", f"Set the index markers around N while facing {h}."),
                  ("reset", "2A / Rotate bezel 180°", f"Shift the markers a half-turn relative to the housing. Face {rec} and place N between them."),
                  ("south", "2B / Keep original bezel", f"Leave the markers where they were. Face {rec} and place S between them.")]
        for col, (method, title, desc) in zip(columns, scenes):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.plotly_chart(bezel_figure(bezel_state(r.heading, method)), use_container_width=True,
                                    theme=None, config={"displayModeBar": False})
                    st.write(desc)
        st.info(f"Same return bearing: {rec}. Reset bezel + N alignment and unchanged bezel + S alignment are equivalent. Neither method uses the complementary angle.")
        st.caption("Instrument view: forward is up, not north. Orange bars are bezel markers; teal N and purple S are opposite ends of an ideal magnetic needle/card. The rose above uses a different, north-up frame.")
    elif exercise == "90° turns & square":
        cw, ccw = turn_90(r.heading), turn_90(r.heading, False)
        a, b = st.columns(2)
        a.metric("90° clockwise (right)", format_bearing(cw))
        b.metric("90° counterclockwise (left)", format_bearing(ccw))
        st.write(f"Right: ({h} + 090°) mod 360° = {format_bearing(cw)}. Left: ({h} − 090°) mod 360° = {format_bearing(ccw)}.")
        st.caption("A 90° turn is an operation on a direction. It is different from the complementary angle 090° − heading.")
        turn = st.radio("Square turn direction", ["Clockwise", "Counterclockwise"], horizontal=True)
        leg = st.slider("Leg length (m)", 5, 50, 20, step=5)
        course = square_course(r.heading, leg, turn == "Clockwise")
        st.plotly_chart(square_figure(course), use_container_width=True, theme=None,
                        config={"displayModeBar": False})
        st.write(" → ".join(format_bearing(bearing) for bearing in course.bearings) + " → start")
        st.caption("Closure assumes equal actual leg distances, exact turns, and still water. Equal swim times or kick counts alone do not guarantee closure in current.")
    elif exercise == "Heading vs. track":
        st.markdown("### Your heading is not necessarily your track")
        left, right = st.columns([1, 1.5])
        with left:
            speed = st.slider("Swimming speed through water (m/s)", .1, 1.5, .5, .1)
            cs = st.slider("Current speed (m/s)", 0.0, 1.5, .3, .1)
            relative = st.checkbox("Keep current 90° to the right of heading", True)
            if relative:
                cb = turn_90(r.heading)
                st.write(f"Cross-current flows **toward {format_bearing(cb)}**.")
            else:
                cb = st.slider("Current flows toward (degrees)", 0, 359, 90, format="%03d°")
            seconds = st.slider("Swim duration (seconds)", 10, 300, 60, 10)
            track = current_track(r.heading, speed, cb, cs, seconds)
            st.metric("Heading through water", h)
            st.metric("Track over ground", format_bearing(track.bearing, 1))
            st.metric("Speed over ground", f"{track.ground_speed:.2f} m/s")
            if track.bearing is None:
                st.info("The velocities cancel: no movement over ground, so track direction is undefined.")
            else:
                st.write(f"Drift angle: **{track.drift_angle:+.1f}°** (positive = clockwise).")
        with right:
            st.plotly_chart(track_figure(track, seconds), use_container_width=True,
                            theme=None, config={"displayModeBar": False})
            st.markdown("**Ground velocity = swim velocity + current velocity.** The dashed vector is your through-water displacement; the dotted vector adds current; the solid vector is the resulting ground track.")
            st.write(f"Endpoint after {seconds} s: **{track.displacement[0]:.1f} m east, {track.displacement[1]:.1f} m north** of the start.")
        st.caption("Idealized constant vectors in a flat local plane. Reversing the heading reverses your swimming vector; it does not reverse the current. A reciprocal heading therefore does not guarantee retracing your ground track.")
    elif exercise == "Rectangle with Current":
        render_rectangle_exercise()

st.markdown('<div class="footer">COMPASS GEOMETRY LABORATORY · Independent SSI AOW study aid, not an SSI course product. All examples use a shared magnetic-north reference; declination and real dive conditions are outside this model.</div>', unsafe_allow_html=True)
