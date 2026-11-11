# Verification record

Date: **11 November 2026**. Updated for Rectangle with Current.

## Automated execution

Environment: Python 3.12.14, Streamlit 1.50.0, Plotly 6.3.1, pytest 8.4.2,
Linux. Complete installed dependency pins: `requirements-lock.txt`.

```text
python -m pytest -q --junitxml=verification/pytest-results.xml
213 passed in 5.90s

python -m pip check
No broken requirements found.
```

Tests include every integer heading for reciprocal/coordinate invariants,
explicit cardinal and intercardinal cases, 040°/359°, zero/full-turn handling,
nonfinite inputs, two bezel methods, both square directions, and analytic
velocity checks. Streamlit's AppTest executes the actual `app.py` and checks
shared widget state, rendered card text, Plotly figure metadata, and all four
navigation views. The original 135 tests remain unchanged; 78 tests were added
for the rectangle model, plot, and UI. The original geometry, navigation,
visualization modules and dependency pins were byte-compared with the previous
delivered archive and are unchanged. `app.py` only adds the new view import and
fourth navigation option, with explanatory captions.

## Rectangle with Current: numerical results

Default inputs: 060°, 40 m × 20 m, swimmer 1.0 m/s, current toward 150° at
`tan(10°) = 0.17632698070846498 m/s`.

| Leg | Heading | Track | Duration | Ground speed |
|---|---|---|---|---|
| 1 | 060° | 070.0° | 40 s | 1.0154 m/s |
| 2 | 150° | 150.0° | 20 s | 1.1763 m/s |
| 3 | 240° | 230.0° | 40 s | 1.0154 m/s |
| 4 | 330° | 330.0° | 20 s | 0.8237 m/s |

Total time: 120 s. Swimming distance: 120 m. Final position:
**(10.5796188425 m east, −18.3244373599 m north)**. Net displacement:
**21.1592376850 m toward 150°**. First-leg drift: **+10° clockwise**.

Model tests independently check these numerical values, clockwise/wraparound
headings, all 360 initial headings, arbitrary current directions, velocity
addition and leg durations, exact zero-current closure, distance/time/speed
scaling, left and right perpendicular calibration, and oblique-current drift.
An opposing current at 0.5, 1, or 2 times swimmer speed respectively slows,
stops, or reverses the first ground track. Stationary tracks have undefined
bearings. Plot tests compare coordinates directly with model vertices and
check independent layer visibility and equal axis scaling.

Streamlit AppTest additionally verifies bidirectional speed/drift controls,
fixed versus relative current, no-current table/plot agreement, complete reset,
and independence from the original explorer's heading.

## Rectangle browser checks

Actual running Streamlit UI in Chromium, at 1280 and 390 CSS pixels:

1. Selected **Dive Navigation Mode → Rectangle with Current**. Initial heading
   was 060° while the original explorer remained at 040°. Cards displayed
   120.0 s, 120 m, 21.16 m and 150.0°; the plot and leg table matched.
2. Edited drift to 20°: current speed became 0.36397 m/s. Edited current speed
   to 0.5 m/s: drift became 26.57°.
3. Changed initial heading to 100°: current stayed at 150°. Explicitly enabled
   relative current: its bearing became 190°.
4. Turned current off: the planned and actual SVG path data were identical and
   displacement was zero. Re-enabling and resetting restored the default.
5. Hid the actual-track layer independently and restored it.
6. At 390 px, entered 359°: planned headings became 359°, 089°, 179°, 269° and
   current remained at 150°. Verified current-off path coincidence, then reset
   to 060° / 10° through the mobile controls.
7. Plot, cards, legend and explanation bounds stayed inside both viewport
   widths. The leg table scrolls horizontally within its container on mobile.
   Turn labels were adjusted after visual inspection for narrow-screen clarity.

Machine-readable observations: `verification/rectangle-browser-checks.json`.
Direct browser captures of the final default exercise:

- `screenshots/rectangle-060-desktop.jpg` — 1280 × 2105
- `screenshots/rectangle-060-mobile.jpg` — 390 × 3366

These captures crop to the rectangle exercise within the actual app. They are
not generated mockups. Phone-width Chromium checks do not assert physical
iPhone, touch, or Safari testing.

## Original explorer: boundary values checked in the rendered browser

| Heading | Reciprocal | Complementary | Supplementary | Explementary measure | Explementary direction |
|---|---|---|---|---|---|
| 000° | 180° | 090° | 180° | 360° | 000° |
| 040° | 220° | 050° | 140° | 320° | 320° |
| 090° | 270° | 000° | 090° | 270° | 270° |
| 180° | 000° | N/A | 000° | 180° | 180° |
| 270° | 090° | N/A | N/A | 090° | 090° |
| 359° | 179° | N/A | N/A | 001° | 001° |

## Original explorer: browser interaction evidence

Actual Chromium UI, running `streamlit run app.py` locally:

1. Initial page displayed exactly 040° and 220° / 050° / 140° / 320°.
2. Numeric input moved through 000°, 090°, 180°, 270°, 359°; all four cards and
   the slider matched each value.
3. An arrow-key movement from 359° to 358° synchronized the numeric input.
4. A real pointer drag from 040° to 163° produced 343° / N/A / 017° / 197°,
   numeric input 163, and changed rendered SVG path geometry after release.
5. Reset returned to 040°. Hiding R removed its orange SVG path while the other
   layers remained; re-enabling restored it.
6. All original three dive views rendered. Square turns at 040° displayed 130° and 310°.
   The default current exercise displayed heading 040°, track 071.0°, ground
   speed 0.58 m/s, drift +31.0°, and endpoint 33.1 m east / 11.4 m north at 60 s.
7. Real iframe browsing contexts at 1280, 768, and 390 CSS pixels displayed the
   same application. Card, plot, legend and explanation bounds stayed inside
   their viewport. At 390px, numeric input and reset were also exercised.

The machine-readable observation log is `verification/browser-checks.json`.
The responsive harness only supplies viewport sizes; it does not change the app.
Screenshots are direct browser captures, not generated mockups:

- `screenshots/dashboard-040-desktop.jpg` — 1280 × 1620
- `screenshots/dashboard-040-tablet.jpg` — 768 × 2000
- `screenshots/dashboard-040-mobile.jpg` — 390 × 2800

The long image heights capture the full dashboard; mobile-width verification
does not imply testing a particular physical device or touch browser.

## Acceptance summary

| Criterion | Evidence |
|---|---|
| Starts with `streamlit run app.py` | Local running app opened in Chromium |
| Initial 040° and four correct values | AppTest plus desktop screenshot |
| North-up / clockwise geometry | Analytic coordinate tests, figure tests, rendered rose |
| Invalid complementary/supplementary results | 091°/181° tests and rendered 270°/359° checks |
| 360° measure retained at 000° | Unit, figure, AppTest and browser checks |
| Coincident R/X arrows remain distinct | Different radii/strokes, figure tests at 090°/270° |
| Control/visual synchronization | AppTest plus actual pointer drag and numeric/keyboard entry |
| Desktop and mobile layout | Direct captures and bounding-box checks at three widths |
| Rectangle default drift and displacement | Analytic tests, AppTest, browser plot/table/cards and screenshots |
| Current stays independent of heading | Unit tests, AppTest and browser checks; explicit relative-mode option |
| Exact no-current closure | Exact model equality, AppTest and identical browser SVG paths |
| Opposing current can stop/reverse travel | Unit tests, AppTest and zero-velocity figure serialization |
| Unit tests pass | 213 passed; attached console output and JUnit XML |
| No paid services/API keys | Local Streamlit and bundled Plotly; no external data calls |

Slider values commit on release. Plotly requests short transitions when enabled;
continuous animation during a drag is not asserted. Safari, Firefox, Windows,
macOS, and Python versions newer than 3.12.14 were not executed in this run.
