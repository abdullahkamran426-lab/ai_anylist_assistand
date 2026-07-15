"""
Sidebar & navigation styles
===========================
Re-skins the sidebar's st.radio() navigation into a modern pill-style
nav list purely with CSS.

This module exports a raw CSS string that is injected by
modules/style/__init__.py.
"""

SIDEBAR_CSS = """
/* ============================================================================
   SIDEBAR STYLING
============================================================================ */

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.4rem;
}

/* Navigation group */
[data-testid="stSidebar"] [data-testid="stRadio"] > div[role="radiogroup"] {
    gap: 3px;
}

/* Navigation item */
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
    transition: all .2s ease;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: var(--card);
    border-color: var(--border);
    transform: translateX(2px);
}

/* Hide radio circle */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none !important;
}

/* Text */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:last-child {
    font-size: .88rem;
    font-weight: 500;
    color: var(--muted);
    letter-spacing: .01em;
}

/* Selected */
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(
        90deg,
        rgba(99,102,241,.22) 0%,
        rgba(99,102,241,.06) 100%
    );
    border-color: rgba(99,102,241,.45);
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked)::before {
    content: "";
    position: absolute;
    left: -1px;
    top: 6px;
    bottom: 6px;
    width: 3px;
    border-radius: 3px;
    background: linear-gradient(
        180deg,
        var(--accent2),
        var(--accent)
    );
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) > div:last-child {
    color: #fff;
    font-weight: 700;
}

/* ==========================================================
   SECTION HEADINGS
========================================================== */

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7),
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(10) {
    margin-top: 20px !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7)::after,
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(10)::after {
    position: absolute;
    top: -18px;
    left: 16px;
    font-size: .66rem;
    font-weight: 700;
    letter-spacing: .12em;
    color: #4b5065;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(3)::after {
    content: "PREPARE";
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(4)::after {
    content: "EXPLORE";
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(7)::after {
    content: "INSIGHTS";
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-of-type(10)::after {
    content: "MORE";
}
"""
