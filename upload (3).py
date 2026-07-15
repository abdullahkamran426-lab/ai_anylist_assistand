"""
Explore pages styles (Dataset Preview / Statistics / Visualizations)
====================================================================
Shared styling for the three data-exploration pages: the compact
.explore-hero banner used at the top of each, the .col-chip grid of
per-column detail cards (Dataset Preview -> Column Details), the
.stat-panel container plus its .vc-row/.vc-bar value-count bars
(Statistics), and the .chart-card wrapper around each Plotly chart
(Visualizations).

This module only exports a raw CSS string — no <style> tag wrapper — so it can
be concatenated with the other styles/*.py modules by styles/__init__.py,
which wraps the combined result in a single <style>...</style> block exactly
like the original monolithic styles.py did.
"""

EXPLORE_CSS = """
/* ============================================================================
   EXPLORE PAGES HERO STRIP
   Compact hero banner for explore pages
============================================================================ */
.explore-hero {
    background: linear-gradient(135deg, #1a1d27 0%, #1e2440 65%, #1a1d27 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 26px 30px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.explore-hero .eh-icon {
    width: 46px; height: 46px; border-radius: 12px; flex-shrink: 0;
    background: linear-gradient(135deg, #6366f1, #818cf8);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; box-shadow: 0 8px 20px rgba(99,102,241,.3);
}
.explore-hero .eh-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.3rem; font-weight: 700; color: #fff; }
.explore-hero .eh-sub { color: var(--muted); font-size: .84rem; margin-top: 2px; }

/* ============================================================================
   COLUMN CHIP GRID
   Grid of column detail cards for Dataset Preview -> Column Details tab.
   auto-fill lets as many chips per row as fit at 170px each, so all columns
   are visible with minimal scrolling instead of stacking 1-per-row.
============================================================================ */
.col-chip-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; }
.col-chip {
    background: var(--card); border: 1px solid var(--border); border-radius: 12px;
    padding: 12px 14px; transition: border-color .15s;
    /* Fixed, "normal" height for every card regardless of column-name length —
       content is arranged with flexbox so the health bar always sits at the
       bottom instead of the card stretching to fit long names or wrapped text. */
    height: 108px; box-sizing: border-box;
    display: flex; flex-direction: column; justify-content: space-between;
    overflow: hidden;
}
.col-chip:hover { border-color: var(--accent); }
.col-chip .cc-name {
    font-weight: 700; color: #fff; font-size: .82rem; line-height: 1.2;
    /* Long column names get an ellipsis instead of wrapping and pushing the
       card taller — a tooltip via `title` still shows the full name on hover. */
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.col-chip .cc-type {
    display: inline-block; font-size: .64rem; font-weight: 700; padding: 2px 9px;
    border-radius: 99px; letter-spacing: .03em; text-transform: uppercase; width: fit-content;
}
.col-chip .cc-meta { color: var(--muted); font-size: .72rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.col-chip .cc-bar { background: rgba(255,255,255,.07); border-radius: 99px; height: 4px; overflow: hidden; }
.col-chip .cc-bar-fill { height: 100%; border-radius: 99px; }
.type-num  { background: rgba(99,102,241,.16); color: #818cf8; }
.type-obj  { background: rgba(34,211,165,.16); color: #22d3a5; }
.type-date { background: rgba(251,191,36,.16); color: #fbbf24; }
.type-bool { background: rgba(248,113,113,.16); color: #f87171; }

/* ============================================================================
   STAT / ANALYSIS CARDS
   Cards for statistics and analysis panels
============================================================================ */
.stat-panel {
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 22px; margin-bottom: 18px;
}
.stat-panel h4 {
    font-family: 'Space Grotesk', sans-serif; font-size: .98rem; font-weight: 700;
    color: #fff; margin: 0 0 14px; display: flex; align-items: center; gap: 8px;
}
.vc-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.vc-label { width: 130px; flex-shrink: 0; font-size: .82rem; color: var(--text); word-break: break-all; }
.vc-bar-track { flex: 1; background: rgba(255,255,255,.06); border-radius: 99px; height: 10px; overflow: hidden; }
.vc-bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--accent), var(--accent2)); }
.vc-count { width: 64px; text-align: right; font-size: .78rem; color: var(--muted); flex-shrink: 0; }


/* ============================================================================
   CHART OUTPUT CARD
   Card wrapper for Plotly charts
============================================================================ */
.chart-card {
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 18px 20px 6px; margin-top: 4px;
}
.chart-card .cc-title { color: var(--muted); font-size: .8rem; font-weight: 600; margin-bottom: 4px; }
"""
