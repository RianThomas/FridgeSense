"""Look and feel.

Palette (named so the CSS reads like a design, not a pile of hex codes):
  mist      #F3F7F4  page background, a cool pale green rather than cream
  pine      #14352A  text
  moss      #5A7066  secondary text
  rule      #D9E5DD  borders
  leaf      #1F7A45  the one brand green (buttons, rings, "Safe")
  tomato    #C23B2E  Priority
  squash    #9A6700  Moderate

Type: Bricolage Grotesque for headings and big numbers, Figtree for
everything else. Both are bundled in static/fonts (SIL Open Font License, see
the licence files beside them) and served by Streamlit, so the app needs no
internet connection and sends nothing to a font CDN.

Surfaces are flat and bordered, not shadowed, so the six rings on the Home
screen are the only thing that draws the eye.
"""
import streamlit as st

CSS = """
<style>
@font-face { font-family: 'Bricolage Grotesque'; font-style: normal; font-weight: 200 800; font-display: swap;
  src: url('app/static/fonts/bricolage-grotesque.woff2') format('woff2'); }
@font-face { font-family: 'Figtree'; font-style: normal; font-weight: 300 900; font-display: swap;
  src: url('app/static/fonts/figtree.woff2') format('woff2'); }

:root {
    --fs-bg: #FAF7F2; --fs-surface: #FFFFFF; --fs-ink: #2B2220; --fs-muted: #7A6A64;
    --fs-rule: #E8DFD8;
    --fs-accent: #B8404F; --fs-accent-soft: #FBE3E0;   /* buttons and rings */
    --fs-leaf: #1F7A45; --fs-leaf-soft: #E3F1E8;       /* now only "Safe" */
    --fs-priority: #9E2A22; --fs-priority-soft: #FBE7E4;
    --fs-moderate: #9A6700; --fs-moderate-soft: #FBF0D5;
    --fs-head: 'Bricolage Grotesque', 'Figtree', system-ui, sans-serif;
    --fs-body: 'Figtree', system-ui, sans-serif;
}

html, body, .stApp, [data-testid="stAppViewContainer"] { font-family: var(--fs-body); }
.stApp { background: var(--fs-bg); }
h1, h2, h3, h4 { font-family: var(--fs-head) !important; color: var(--fs-ink); letter-spacing: -0.01em; }
.stApp .stDeployButton, .stApp [data-testid="stAppDeployButton"], #MainMenu { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { padding-top: 2.2rem; max-width: 1100px; }

/* Surfaces */
.fs-card { background: var(--fs-surface); border: 1px solid var(--fs-rule); border-radius: 14px; padding: 1rem 1.2rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px !important; }
.fs-muted { color: var(--fs-muted); font-size: 0.92rem; }
.fs-center { text-align: center; }

/* Top bar */
.fs-brand-title { font-family: var(--fs-head); font-weight: 700; font-size: 1.9rem; text-align: center;
  color: var(--fs-ink); line-height: 1.1; margin: 0.15rem 0 0; }
.fs-page-title { font-family: var(--fs-head); font-weight: 700; font-size: 1.5rem; text-align: center;
  color: var(--fs-ink); margin: 0.2rem 0 1.4rem; }

/* Ripeness: always a word, never colour alone */
.fs-chip { display: inline-block; padding: 0.12rem 0.65rem; border-radius: 999px; font-size: 0.8rem;
  font-weight: 600; border: 1px solid transparent; }
.fs-chip.priority { background: var(--fs-priority-soft); color: var(--fs-priority); border-color: #F2C4BE; }
.fs-chip.moderate { background: var(--fs-moderate-soft); color: var(--fs-moderate); border-color: #EBD59A; }
.fs-chip.safe { background: var(--fs-leaf-soft); color: var(--fs-leaf); border-color: #BFDFCB; }
.fs-useby.priority { color: var(--fs-priority); font-weight: 600; }
.fs-useby.moderate { color: var(--fs-moderate); font-weight: 600; }

/* Nutrient rings (Home) */
.fs-rings { display: flex; flex-wrap: wrap; justify-content: center; gap: 1.6rem 1rem; margin: 0.4rem auto 1.6rem; }
.fs-ring { width: 23%; min-width: 150px; text-align: center; }
.fs-ring svg { width: 132px; height: 132px; display: block; margin: 0 auto 0.5rem; }
.fs-ring .track { stroke: #DDE8E0; }
.fs-ring .bar { stroke: var(--fs-accent); transition: stroke-dasharray .5s ease; }
.fs-ring.over .bar { stroke: var(--fs-moderate); }
.fs-ring .pct { font-family: var(--fs-head); font-weight: 700; font-size: 25px; fill: var(--fs-ink); }
.fs-ring-name { font-weight: 600; color: var(--fs-ink); }
.fs-ring-val { color: var(--fs-muted); font-size: 0.9rem; }
.fs-ring-flag { font-size: 0.8rem; font-weight: 600; color: var(--fs-moderate); }
.fs-ring.met .fs-ring-flag { color: var(--fs-leaf); }

/* Impact numbers */
.fs-impact { display: flex; justify-content: center; gap: 3.5rem; flex-wrap: wrap; margin-top: 0.4rem; }
.fs-impact-item { text-align: center; }
.fs-impact-num { font-family: var(--fs-head); font-weight: 700; font-size: 2.3rem; color: var(--fs-ink); line-height: 1.1; }
.fs-impact-label { color: var(--fs-muted); font-size: 0.92rem; }

/* Recipe cards */
.fs-photo { width: 100%; aspect-ratio: 4 / 3; border-radius: 10px; display: flex; align-items: center;
  justify-content: center; font-size: 3.4rem; margin-bottom: 0.5rem; }
.fs-photo.hero { aspect-ratio: 16 / 5; font-size: 5rem; border-radius: 14px; }
.st-key-hero img { width: 100%; max-height: 320px; object-fit: cover; border-radius: 14px; }
.st-key-rec_heart_detail { margin-left: auto; }  /* the key class is on the button's own wrapper */
.fs-recipe-name { font-weight: 600; color: var(--fs-ink); line-height: 1.25; min-height: 2.5em; }
.fs-why { font-size: 0.84rem; color: var(--fs-priority); font-weight: 600; min-height: 3.3em; margin: 0.15rem 0 0.6rem; }

/* Nutrition panel */
.fs-nutri-row { display: flex; justify-content: space-between; padding: 0.55rem 0; border-bottom: 1px solid var(--fs-rule); }
.fs-nutri-row:last-child { border-bottom: 0; }
.fs-nutri-row span:first-child { color: var(--fs-muted); }
.fs-nutri-row span:last-child { font-weight: 600; color: var(--fs-ink); }
.fs-score { font-family: var(--fs-head); font-weight: 700; font-size: 3.6rem; line-height: 1; color: var(--fs-ink); }
.fs-score small { font-size: 1.1rem; color: var(--fs-muted); font-weight: 500; }
.fs-rating { display: flex; justify-content: space-between; padding: 0.3rem 0; }
.fs-rating b.Excellent, .fs-rating b.Good { color: var(--fs-leaf); }
.fs-rating b.Moderate { color: var(--fs-moderate); }
.fs-rating b.Needs { color: var(--fs-priority); }

/* Big numbers from st.metric (cooked screen, history) match the Home numbers */
[data-testid="stMetricValue"] { font-family: var(--fs-head); font-weight: 700; color: var(--fs-ink); }
[data-testid="stMainBlockContainer"] h4 { margin-top: 1.2rem; }

/* Table header row (Upload / Pantry) */
.fs-th { font-weight: 600; color: var(--fs-muted); font-size: 0.88rem; padding-bottom: 0.2rem; }

/* Buttons */
.stButton > button, .stDownloadButton > button { border-radius: 10px; font-weight: 600; }
button[kind="secondary"] { background: var(--fs-surface); border-color: var(--fs-rule); }

/* Sidebar */
section[data-testid="stSidebar"] { border-right: 1px solid var(--fs-rule); }
/* On desktop the app has its own collapse button, so Streamlit's is hidden. On a phone the
   sidebar is an overlay that starts closed, and Streamlit's own open/close buttons are the
   only way to reach it, so they stay. */
@media (min-width: 769px) {
  [data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"],
  [data-testid="stExpandSidebarButton"] { display: none !important; }
  [data-testid="stSidebarHeader"] { display: none; }
}
@media (max-width: 768px) {
  /* Solid header so Streamlit's floating open-menu button doesn't sit on top of page text */
  header[data-testid="stHeader"] { background: var(--fs-bg); }
  .st-key-sb_toggle { display: none; }
  [data-testid="stSidebarHeader"] { padding-bottom: 0; }
}
.fs-sb-brand { font-family: var(--fs-head); font-weight: 700; font-size: 1.25rem; color: var(--fs-ink);
  display: flex; align-items: center; gap: 0.5rem; margin: 0.4rem 0 1.2rem 0.2rem; }
/* Descendant selectors on purpose: with a help tooltip Streamlit wraps the button. */
section[data-testid="stSidebar"] .stButton button { border: 0; background: transparent;
  color: var(--fs-ink); padding: 0.55rem 0.8rem; box-shadow: none; }
section[data-testid="stSidebar"] .stButton button > div { width: 100%; justify-content: flex-start; }
section[data-testid="stSidebar"] .stButton button:hover { background: var(--fs-leaf-soft); }
section[data-testid="stSidebar"] .stButton button[kind="primary"] { background: var(--fs-leaf-soft) !important;
  color: var(--fs-leaf) !important; box-shadow: inset 3px 0 0 var(--fs-leaf); }
/* Pin the collapse toggle to the bottom of the sidebar. */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]:has(> [data-testid="stLayoutWrapper"] > .st-key-sb_bottom) {
  min-height: calc(100vh - 6.1rem); }  /* sidebar content has 6rem of bottom padding */
section[data-testid="stSidebar"] [data-testid="stLayoutWrapper"]:has(> .st-key-sb_bottom) { margin-top: auto; }

/* These two hold only small scripts (close the phone overlay, scroll to top) */
[data-testid="stLayoutWrapper"]:has(> .st-key-nav_closer),
[data-testid="stLayoutWrapper"]:has(> .st-key-scroll_top) { display: none; }

/* Login */
.fs-avatar { width: 84px; height: 84px; border-radius: 50%; background: var(--fs-leaf-soft); color: var(--fs-leaf);
  display: flex; align-items: center; justify-content: center; margin: 0.6rem auto 0.8rem; }
</style>
"""

EXPANDED = """
<style>
section[data-testid="stSidebar"] { width: 236px !important; min-width: 236px !important; }
</style>
"""

# Icon-only rail: desktop only. On a phone the sidebar is a full overlay, so it always
# shows labels.
COLLAPSED = """
<style>
@media (min-width: 769px) {
  section[data-testid="stSidebar"] { width: 78px !important; min-width: 78px !important; }
  section[data-testid="stSidebar"] .stButton button { padding: 0.6rem 0; }
  section[data-testid="stSidebar"] .stButton button > div { justify-content: center; }
  section[data-testid="stSidebar"] .stButton button [data-testid="stMarkdownContainer"] { display: none; }
  .fs-sb-brand span.t, .fs-sb-note { display: none; }
  .fs-sb-brand { justify-content: center; margin-left: 0; }
}
</style>
"""


def inject(collapsed=False):
    st.markdown(CSS + (COLLAPSED if collapsed else EXPANDED), unsafe_allow_html=True)
