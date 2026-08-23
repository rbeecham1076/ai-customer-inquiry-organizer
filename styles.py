"""
The visual design layer: custom fonts, the hero banner, stat cards, and badges.

Streamlit gives you working components but a fairly generic look. This
file adds a bold, warm, high-contrast layer on top using CSS.

Two deliberate choices worth knowing:

1. Every CSS rule here targets a class name we invented ourselves
   (.hero, .stage-pill, .badge). It would also be possible to target
   Streamlit's own internal class names, but those change between
   Streamlit versions and would silently break the design on an upgrade.
   Styling only our own markup keeps this stable.

2. The look leans on three things rather than lots of fussy detail:
   heavy geometric type, chunky ink borders, and hard offset shadows
   (a solid shadow with no blur). That combination is what gives it
   personality instead of default-dashboard blandness.
"""

import html

from constants import PRIORITY_COLORS, STATUS_COLORS

# Core palette, kept here so the CSS below and any inline styles agree.
INK = "#1E1B2E"
CORAL = "#FF5A36"
MUSTARD = "#FFC145"
MINT = "#0FA47F"
CREAM = "#FFF8F0"

# The <style> block is injected once at the top of the page.
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextInput, .stTextArea, .stSelectbox {
    font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Chunkier, friendlier form controls to match the rest of the design. */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    border-radius: 12px !important;
    border-width: 2px !important;
}

.stButton button {
    border-radius: 14px !important;
    border-width: 2px !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
    padding: 0.6rem 1.2rem !important;
    transition: transform 0.08s ease, box-shadow 0.08s ease;
}

.stButton button:active {
    transform: translate(2px, 2px);
}

/* ---------- Hero ---------- */

.hero {
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at 88% 18%, #FFD9A8 0%, rgba(255,217,168,0) 46%),
        radial-gradient(circle at 12% 88%, #FFC7B8 0%, rgba(255,199,184,0) 52%),
        linear-gradient(135deg, #FFF1E2 0%, #FFE4D3 100%);
    border: 3px solid #1E1B2E;
    border-radius: 28px;
    box-shadow: 10px 10px 0 #1E1B2E;
    padding: 2.9rem 2.6rem 2.4rem 2.6rem;
    margin: 0.25rem 0 2.4rem 0;
}

.hero-eyebrow {
    display: inline-block;
    background: #1E1B2E;
    color: #FFF8F0;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    margin-bottom: 1.15rem;
}

.hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: 3.5rem;
    font-weight: 900;
    line-height: 0.98;
    letter-spacing: -0.035em;
    color: #1E1B2E;
    margin: 0 0 1rem 0;
}

.hero-title .hl {
    position: relative;
    display: inline-block;
    color: #FF5A36;
}

/* A hand-drawn-feeling underline sitting behind the highlighted words. */
.hero-title .hl::after {
    content: "";
    position: absolute;
    left: -2px;
    right: -2px;
    bottom: 0.07em;
    height: 0.19em;
    background: #FFC145;
    border-radius: 999px;
    z-index: -1;
}

.hero-sub {
    font-size: 1.1rem;
    font-weight: 500;
    line-height: 1.5;
    color: #4A4358;
    max-width: 33rem;
    margin: 0;
}

/* Streamlit adds a clickable anchor link to any heading it renders. That's
   useful for long documents but it puts a stray chain icon in the middle of
   our hero, so hide it on the headings we style ourselves. */
.hero-title a,
.section-title a {
    display: none !important;
}

/* ---------- Workflow stage pills ---------- */

.workflow {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.45rem;
    margin-top: 1.9rem;
}

.stage-pill {
    display: inline-block;
    padding: 0.45rem 1rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.75);
    border: 2px solid #1E1B2E;
    color: #1E1B2E;
    opacity: 0.5;
}

.stage-pill.is-active {
    background: #FF5A36;
    color: #FFFFFF;
    opacity: 1;
    box-shadow: 3px 3px 0 #1E1B2E;
}

.stage-arrow {
    color: #1E1B2E;
    font-weight: 800;
    opacity: 0.35;
}

/* ---------- Section headings ---------- */

.section-label {
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #FF5A36;
    margin: 0 0 0.5rem 0;
}

.section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    letter-spacing: -0.028em;
    line-height: 1.15;
    color: #1E1B2E;
    margin: 0 0 0.5rem 0;
}

/* ---------- Badges ---------- */

.badge {
    display: inline-block;
    padding: 0.26rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 800;
    border: 2px solid #1E1B2E;
}

/* ---------- Stat cards ---------- */

.stat-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.9rem;
    margin-bottom: 0.5rem;
}

.stat-card {
    flex: 1 1 150px;
    background: #FFFFFF;
    border: 3px solid #1E1B2E;
    border-radius: 20px;
    box-shadow: 5px 5px 0 #1E1B2E;
    padding: 1.15rem 1.25rem;
}

.stat-value {
    font-size: 2.5rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    line-height: 1;
    color: #1E1B2E;
    margin-bottom: 0.3rem;
}

.stat-label {
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #7A7189;
}

/* ---------- Guardrail note ---------- */

.guardrail {
    background: #FFFFFF;
    border: 3px solid #1E1B2E;
    border-radius: 18px;
    box-shadow: 5px 5px 0 #FFC145;
    padding: 1.1rem 1.3rem;
    font-size: 0.95rem;
    font-weight: 500;
    line-height: 1.5;
    color: #4A4358;
    margin-bottom: 1.4rem;
}

.guardrail strong {
    color: #1E1B2E;
    font-weight: 800;
}

/* ---------- Review card wrapper ---------- */

.review-flag {
    display: inline-block;
    background: #FFC145;
    border: 2px solid #1E1B2E;
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #1E1B2E;
    margin-bottom: 0.7rem;
}

/* ---------- Footer ---------- */

.site-footer {
    border-top: 3px solid #1E1B2E;
    margin-top: 2.5rem;
    padding-top: 1.2rem;
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.6rem;
    font-size: 0.86rem;
    color: #7A7189;
}

.site-footer .built-by {
    font-weight: 700;
    color: #1E1B2E;
}

.site-footer a {
    color: #FF5A36;
    font-weight: 700;
    text-decoration: none;
    border-bottom: 2px solid rgba(255, 90, 54, 0.35);
}

.site-footer a:hover {
    border-bottom-color: #FF5A36;
}

.site-footer .stack {
    font-weight: 500;
}
</style>
"""


def render_hero(active_stage: str) -> str:
    """
    Build the hero banner, highlighting whichever workflow stage the user
    is currently in.

    Returns an HTML string so app.py can hand it straight to st.markdown.
    """
    stages = ["New Inquiry", "AI Analysis", "Human Review", "Approved Task"]

    pills = []
    for index, stage in enumerate(stages):
        if index > 0:
            pills.append('<span class="stage-arrow">→</span>')
        active_class = " is-active" if stage == active_stage else ""
        pills.append(f'<span class="stage-pill{active_class}">{stage}</span>')

    return f"""
<div class="hero">
  <div class="hero-eyebrow">Customer Ops, Handled</div>
  <h1 class="hero-title">Messy inbox in.<br><span class="hl">Real work</span> out.</h1>
  <p class="hero-sub">
    Drop in any customer email, DM, or order note. It gets sorted, ranked,
    routed, and answered &mdash; then lands on your desk for a yes or no.
  </p>
  <div class="workflow">{"".join(pills)}</div>
</div>
"""


def render_footer(name: str, links: dict, stack: str) -> str:
    """
    Build the footer credit line.

    `links` maps a label to a URL, for example {"GitHub": "https://..."}.
    Any link left as an empty string is skipped, so the footer still
    renders cleanly before every profile URL is filled in.
    """
    link_html = " &middot; ".join(
        f'<a href="{html.escape(url)}" target="_blank">{html.escape(label)}</a>'
        for label, url in links.items()
        if url
    )

    left = f'<span class="built-by">Built by {html.escape(name)}</span>'
    if link_html:
        left += f" &nbsp;{link_html}"

    return (
        f'<div class="site-footer">{left}'
        f'<span class="stack">{html.escape(stack)}</span></div>'
    )


def stat_cards(stats: list) -> str:
    """
    Render a row of big number cards.

    `stats` is a list of (label, value) pairs. Used instead of Streamlit's
    built-in st.metric so the numbers match the rest of the design.
    """
    cards = "".join(
        f'<div class="stat-card">'
        f'<div class="stat-value">{html.escape(str(value))}</div>'
        f'<div class="stat-label">{html.escape(str(label))}</div>'
        f"</div>"
        for label, value in stats
    )
    return f'<div class="stat-row">{cards}</div>'


def badge(text: str, colors: dict) -> str:
    """
    Render one colored pill. `colors` maps a value to a
    (background, text color) pair - see constants.py.

    html.escape() is used because this text can come from an AI response
    or a human edit; escaping it means a stray character like "<" is
    displayed as text instead of being treated as markup.
    """
    background, foreground = colors.get(text, ("#EFE7DA", "#4A4358"))
    safe_text = html.escape(text)
    return (
        f'<span class="badge" style="background:{background};color:{foreground};">'
        f"{safe_text}</span>"
    )


def priority_badge(priority: str) -> str:
    return badge(priority, PRIORITY_COLORS)


def status_badge(status: str) -> str:
    return badge(status, STATUS_COLORS)
