"""
Sidebar & navigation styles
===========================
Re-skins the sidebar's st.radio() navigation into a modern pill-style
nav list purely with CSS — no Python logic is touched. Targets
Streamlit's internal [data-testid="stSidebar"] / [data-testid="stRadio"]
attributes, which are stable across Streamlit widget versions even
though they're not a public API.

Note: the section-group labels (PREPARE / EXPLORE / INSIGHTS / MORE)
are positioned with :nth-of-type(3/4/7/9), which assumes the sidebar's
st.radio() options list keeps its current order. If a page is added,
removed, or reordered in main.py's navigation list, update the
nth-of-type indices (and the ::after content) below to match.

This module only exports a raw CSS string — no <style> tag wrapper — so it can
be concatenated with the other styles/*.py modules by styles/__init__.py,
which wraps the combined result in a single <style>...</style> block exactly
like the original monolithic styles.py did.
"""

SIDEBAR_CSS = """
/* ============================================================================
   SIDEBAR STYLING
   The navigation is a st.radio() widget in the sidebar.
   We re-skin the radio labels into modern nav items without touching Python logic.
============================================================================ */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.4rem; }

/* Nav radio group container */
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] {
    gap: 3px;
}

/* Each nav item label */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    position: relative;
    display: flex !important;
    align-items: center;
    width: 100%;
    padding: 10px 14px 10px 16px !important;
    margin: 0 !important;
    border-radius: 10px;
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
    transition: background .15s ease, border-color .15s ease, transform .1s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: var(--card);
    border-color: var(--border);
    transform: translateX(2px);
}

/* Hide the native radio dot - we show selection via background/border instead */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none !important;
}

/* Label text styling */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:last-child {
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--muted);
    letter-spacing: .01em;
}

/* Selected item state - uses :has() to react to hidden radio input */
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(90deg, rgba(99,102,241,.22) 0%, rgba(99,102,241,.06) 100%);
    border-color: rgba(99,102,241,.45);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked)::before {
    content: '';
    position: absolute;
    left: -1px; top: 6px; bottom: 6px;
    width: 3px;
    border-radius: 3px;
    background: linear-gradient(180deg, var(--accent2), var(--accent));
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) > div:last-child {
    color: #fff;
    font-weight: 700;
}

/* Section group labels - injected above specific nav items
   nth-of-type targets specific positions to draw section captions */
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9) {
    margin-top: 20px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9)::after {
    position: absolute;
    top: -18px; left: 16px;
    font-size: .66rem;
    font-weight: 700;
    letter-spacing: .12em;
    color: #4b5065;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3)::after { content: 'PREPARE'; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4)::after { content: 'EXPLORE'; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7)::after { content: 'INSIGHTS'; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(9)::after { content: 'MORE'; }
"""
