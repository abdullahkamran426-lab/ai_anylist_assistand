"""
Custom layout primitives
========================
Hand-rolled layout classes (rendered via st.markdown(..., unsafe_allow_html=True))
that show up on more than one page: the big gradient .hero band and
.section-label/.section-title heading pattern (Home + every page header),
.feat-card (Home's feature grid), .pill status badges (used throughout
Clean Data), the numbered .step badge, the reusable .clean-panel container,
and the plain .div horizontal divider.

This module only exports a raw CSS string — no <style> tag wrapper — so it can
be concatenated with the other styles/*.py modules by styles/__init__.py,
which wraps the combined result in a single <style>...</style> block exactly
like the original monolithic styles.py did.
"""

LAYOUT_CSS = """
/* ============================================================================
   HERO BAND
   Large gradient banner for landing page and section headers
============================================================================ */
.hero {
    background: linear-gradient(135deg, #1a1d27 0%, #1e2040 60%, #1a1d27 100%);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 52px 48px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(99,102,241,.18) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    letter-spacing: -.02em;
    line-height: 1.15;
    color: #fff;
    margin: 0 0 12px;
}
.hero-title span { color: var(--accent2); }
.hero-sub { color: var(--muted); font-size: 1.05rem; max-width: 540px; line-height: 1.65; }

/* ============================================================================
   SECTION HEADERS
   Consistent heading pattern: small uppercase label + large title
============================================================================ */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--accent2);
    margin-bottom: 4px;
}
.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.55rem;
    font-weight: 700;
    color: #fff;
    margin: 0 0 24px;
}

/* ============================================================================
   FEATURE CARDS
   Cards used on home page to showcase app capabilities
============================================================================ */
.feat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 24px;
    height: 100%;
    transition: border-color .2s;
}
.feat-card:hover { border-color: var(--accent); }
.feat-icon { font-size: 1.8rem; margin-bottom: 10px; }
.feat-title { font-weight: 700; font-size: 1rem; color: #fff; margin-bottom: 6px; }
.feat-desc { color: var(--muted); font-size: 0.87rem; line-height: 1.6; }

/* ============================================================================
   CLEAN TAG PILLS
   Small pill badges for status indicators
============================================================================ */
.pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px;
}
.pill-green  { background: rgba(34,211,165,.12); color: var(--success); }
.pill-yellow { background: rgba(251,191,36,.12);  color: var(--warning); }
.pill-red    { background: rgba(248,113,113,.12); color: var(--danger);  }
.pill-blue   { background: rgba(99,102,241,.12);  color: var(--accent2); }

/* ============================================================================
   STEP BADGE
   Numbered badges for workflow steps
============================================================================ */
.step {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px; height: 32px;
    background: rgba(99,102,241,.2);
    color: var(--accent2);
    border-radius: 50%;
    font-weight: 700;
    font-size: 0.85rem;
    margin-right: 10px;
    flex-shrink: 0;
}
.step-row { display: flex; align-items: flex-start; gap: 0; margin-bottom: 14px; }
.step-content { color: var(--text); font-size: 0.95rem; padding-top: 5px; }
.step-content small { display: block; color: var(--muted); font-size: 0.82rem; margin-top: 2px; }

/* ============================================================================
   CLEAN PANEL
   Panel component for cleaning tools and other sections
============================================================================ */
.clean-panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 26px;
    margin-bottom: 20px;
}
.clean-panel h4 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    margin: 0 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ============================================================================
   DIVIDER
   Horizontal separator line
============================================================================ */
.div { border-top: 1px solid var(--border); margin: 32px 0; }
"""
