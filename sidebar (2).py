"""
Base styles
===========
Foundational styling that every other module builds on: Google Font
imports, the CSS custom-property (variable) palette used everywhere
else via var(--name), and the base html/body rules. Load this module
first — sidebar.py, widgets.py, layout.py, upload.py and explore.py
all reference the --accent/--card/--border/etc. variables defined here.

This module only exports a raw CSS string — no <style> tag wrapper — so it can
be concatenated with the other styles/*.py modules by styles/__init__.py,
which wraps the combined result in a single <style>...</style> block exactly
like the original monolithic styles.py did.
"""

BASE_CSS = """
/* ============================================================================
   FONTS
   Import Google Fonts: Inter for body text, Space Grotesk for headings
============================================================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

/* ============================================================================
   ROOT PALETTE - CSS Custom Properties
   Define all colors once and reuse via var(--name) throughout the app.
   Change values here to re-theme the entire application.
============================================================================ */
:root {
    --bg:        #0f1117;      /* Main background color */
    --surface:   #1a1d27;      /* Sidebar/surface background */
    --card:      #21253a;      /* Card/panel background */
    --border:    #2e3354;      /* Border color */
    --accent:    #6366f1;      /* Primary accent color */
    --accent2:   #818cf8;      /* Secondary accent color */
    --success:   #22d3a5;      /* Success/green color */
    --warning:   #fbbf24;      /* Warning/yellow color */
    --danger:    #f87171;      /* Danger/red color */
    --text:      #e2e8f0;      /* Primary text color */
    --muted:     #94a3b8;      /* Muted/secondary text color */
    --radius:    14px;         /* Default border radius */
}

/* ============================================================================
   BASE STYLES
   Apply font and background color to all elements
============================================================================ */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
"""
