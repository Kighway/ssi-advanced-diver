"""Streamlit-only view and widget synchronization for the rectangle exercise."""

import streamlit as st

from geometry import format_bearing, normalize_angle
from navigation_scenarios import current_track
from rectangle_simulation import (DEFAULT_CURRENT_SPEED, calibrate_current_speed,
                                  perpendicular_current, simulate_rectangle)
from rectangle_visualization import (ACTUAL_COLOR, CURRENT_COLOR,
                                     DISPLACEMENT_COLOR, PLANNED_COLOR,
                                     RectangleLayers, rectangle_figure)

DEFAULTS = {
    "rect_heading":60, "rect_length":40.0, "rect_width":20.0,
    "rect_swim_speed":1.0, "rect_current_bearing":150,
    "rect_current_speed":DEFAULT_CURRENT_SPEED, "rect_enabled":True,
    "rect_relative":False, "rect_drift":10.0,
    "rect_planned":True, "rect_actual":True,
    "rect_vectors":True, "rect_headings":True,
}


def refresh_drift():
    state = st.session_state
    if state.rect_relative:
        state.rect_current_bearing = int(normalize_angle(state.rect_heading + 90))
    first = current_track(state.rect_heading, state.rect_swim_speed,
                          state.rect_current_bearing,
                          state.rect_current_speed if state.rect_enabled else 0)
    state.rect_drift = abs(first.drift_angle) if first.drift_angle is not None else 0.0


def update_from_drift():
    state = st.session_state
    if state.rect_enabled and perpendicular_current(state.rect_heading, state.rect_current_bearing):
        state.rect_current_speed = calibrate_current_speed(state.rect_swim_speed, state.rect_drift)
    refresh_drift()


def reset_rectangle():
    st.session_state.update(DEFAULTS)


def signed_drift(value):
    if value is None:
        return "Undefined"
    return "0.0°" if abs(value) < .05 else f"{value:+.1f}°"


def render_rectangle_exercise():
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)
    # This runs before widgets are instantiated; callbacks also update before rerun.
    refresh_drift()
    s = st.session_state
    st.subheader("Rectangle with Current")
    st.caption("Four accurate compass headings. One steady current. Follow what happens on the seabed.")
    with st.container(border=True):
        a, b, c = st.columns(3)
        with a:
            st.number_input("Initial rectangle heading (°)", 0, 359, key="rect_heading",
                            format="%03d", on_change=refresh_drift)
            st.number_input("Rectangle length (m)", 1.0, 500.0, step=5.0, key="rect_length")
        with b:
            st.number_input("Rectangle width (m)", 1.0, 500.0, step=5.0, key="rect_width")
            st.number_input("Diver speed through water (m/s)", .1, 3.0, step=.1,
                            key="rect_swim_speed", on_change=refresh_drift)
        with c:
            st.number_input("Current flows toward (°)", 0, 359, key="rect_current_bearing",
                            format="%03d", disabled=s.rect_relative or not s.rect_enabled,
                            on_change=refresh_drift)
            st.number_input("Current speed (m/s)", min_value=0.0, step=.01, format="%.5f",
                            key="rect_current_speed", disabled=not s.rect_enabled,
                            on_change=refresh_drift)
        a, b = st.columns([1, 2])
        with a:
            st.toggle("Current enabled", key="rect_enabled", on_change=refresh_drift)
        with b:
            st.checkbox("Relative current · keep 90° clockwise from the first heading",
                        key="rect_relative", on_change=refresh_drift)
        perpendicular = perpendicular_current(s.rect_heading, s.rect_current_bearing)
        a, b = st.columns([1, 2], vertical_alignment="bottom")
        with a:
            if perpendicular and s.rect_drift <= 89:
                st.number_input("Initial cross-current drift magnitude (°)", 0.0, 89.0,
                                step=.5, format="%.2f", key="rect_drift",
                                disabled=not s.rect_enabled, on_change=update_from_drift,
                                help="Perpendicular currents only. Current direction determines left/right drift.")
            else:
                st.caption("Initial drift is derived from vector addition; edit current speed and direction.")
        with b:
            if s.rect_relative:
                st.caption("Relative mode is on: changing the first heading rotates the current too. During each simulation the current stays fixed on all four legs.")
            else:
                st.caption("World-fixed current: changing the first heading rotates only the rectangle. The current keeps its bearing and speed.")
        st.button("Reset rectangle to 060° / 10°", key="rect_reset", on_click=reset_rectangle)

    sim = simulate_rectangle(s.rect_heading, s.rect_length, s.rect_width,
                             s.rect_swim_speed, s.rect_current_bearing,
                             s.rect_current_speed, s.rect_enabled)
    first = sim.legs[0]
    st.markdown(f"**Current: {sim.effective_current_speed:.6f} m/s toward {format_bearing(sim.current_bearing)}.** "
                f"First-leg drift: **{signed_drift(first.drift_angle)}** (positive = clockwise).")
    if perpendicular and s.rect_enabled:
        st.caption(f"Perpendicular calibration: current speed = {sim.swim_speed:g} × tan({abs(first.drift_angle):.2f}°) = {sim.effective_current_speed:.6f} m/s. Editing speed updates drift; editing drift recalibrates speed. Changing swimmer speed preserves the chosen current.")
    elif not perpendicular and s.rect_enabled:
        st.caption("The current is not perpendicular to leg 1. Its along-course and cross-course components both affect drift; a fixed angular-offset formula is not used.")

    stats = [
        ("Elapsed time", f"{sim.total_time:.1f} s", "Four complete legs"),
        ("Swimming distance", f"{sim.total_swim_distance:g} m", "Relative to the water"),
        ("Net displacement", f"{sim.displacement_distance:.2f} m", "Start to actual finish"),
        ("Displacement bearing", format_bearing(sim.displacement_bearing, 1),
         "Undefined when displacement is zero" if sim.displacement_bearing is None else "Direction from the start"),
    ]
    st.markdown('<div class="calc-grid rectangle-stats">' + ''.join(
        f'<div class="calc-card" style="--accent:{ACTUAL_COLOR}"><div class="calc-title">{title}</div>'
        f'<div class="calc-value" style="font-size:1.9rem">{value}</div><div class="calc-note">{note}</div></div>'
        for title, value, note in stats) + '</div>', unsafe_allow_html=True)
    with st.expander("Rectangle visual layers"):
        a, b = st.columns(2)
        with a:
            st.checkbox("Display planned path", key="rect_planned")
            st.checkbox("Display actual track", key="rect_actual")
        with b:
            st.checkbox("Display current vectors", key="rect_vectors")
            st.checkbox("Display compass headings", key="rect_headings")
    layers = RectangleLayers(s.rect_planned, s.rect_actual, s.rect_vectors, s.rect_headings)
    st.plotly_chart(rectangle_figure(sim, layers), use_container_width=True, theme=None,
                    key="rectangle_plot", config={"displayModeBar":False, "responsive":True})
    legend = [("Planned · no current",PLANNED_COLOR,"dashed"),
              ("Actual · seabed track",ACTUAL_COLOR,"solid"),
              ("Current · 20 s scale",CURRENT_COLOR,"dotted"),
              ("Net displacement",DISPLACEMENT_COLOR,"dashed")]
    st.markdown('<div class="readout">' + ''.join(
        f'<span><i class="key" style="--accent:{color};border-top-style:{style}"></i>{label}</span>'
        for label,color,style in legend) + '</div>', unsafe_allow_html=True)
    st.caption("North up, east right, equal axis scaling. P1–P3 are planned turns; 1–3 are actual turns; 4 is the actual finish. H = compass heading; T = track. Teal arrows represent the constant current velocity at a 20-second scale on metre axes, not extra legs.")
    st.markdown("**Leg calculations** · time comes from swimming distance ÷ through-water speed.")
    st.dataframe([
        {"Leg":leg.number, "Compass heading":format_bearing(leg.heading),
         "Actual track":format_bearing(leg.track_bearing,1),
         "Swim time (s)":round(leg.duration,2), "Ground speed (m/s)":round(leg.ground_speed,4)}
        for leg in sim.legs
    ], hide_index=True, use_container_width=True, key="rectangle_leg_table")

    headings = " → ".join(format_bearing(leg.heading) for leg in sim.legs)
    drifts = ", ".join(signed_drift(leg.drift_angle) for leg in sim.legs)
    if sim.effective_current_speed == 0:
        closure = "Current is off or zero: the actual track coincides exactly with the planned rectangle and returns to the start. Net displacement is zero, so its bearing is undefined."
    else:
        closure = (f"The swimming vectors close, but the current acts for all {sim.total_time:.1f} seconds. "
                   f"Net displacement = {sim.effective_current_speed:.6f} × {sim.total_time:.1f} = "
                   f"{sim.displacement_distance:.2f} m toward {format_bearing(sim.displacement_bearing,1)}. "
                   "Reciprocal headings reverse swimming velocity; they do not reverse the current.")
    st.markdown(f'''<div class="lesson" aria-live="polite">
<p><b>Why the compass turns are correct.</b> {headings}. Each new heading adds 090° clockwise, wrapping at 360°.</p>
<p><b>Why the track changes.</b> Ground velocity is swimming velocity plus current velocity. The current flows toward {format_bearing(sim.current_bearing)}, not from it. The four signed drift angles are {drifts}; ground-track turns need not be 90°.</p>
<p><b>Why a perfect rectangle can miss the start.</b> {closure}</p>
<p><b>A constant angular heading offset is not equivalent to a constant current vector.</b> The current's along-course and cross-course components change as the diver turns. A following current speeds a leg up; an opposing current slows it, cancels it, or pushes the track backward.</p>
</div>''', unsafe_allow_html=True)
    st.caption("Educational model with constant horizontal current and instantaneous turns. Real dives add depth-dependent currents, swimming-speed variation, buoyancy changes, terrain, poor visibility, and diver reaction time. This is not a substitute for actual dive planning or instructor supervision.")
