"""
PDF Export
==========
The branded, interactive PDF report engine: ReportPDF (header/footer +
Table-of-Contents renderer), matplotlib chart builders (histogram,
missing-values bar, dtype/category pie, correlation heatmap), the four
report-section helpers (statistics, AI insights, recommendations,
quality-score summary), and the top-level export_dataset_report()/
export_to_pdf() functions that assemble them all in the required order:

    Cover (branding) → Table of Contents → Dataset overview → KPI cards
    → Dataset information → Missing values → Statistical summary
    → Correlation analysis → Histogram → Pie chart → Heatmap
    → AI insights → Recommendations → Dataset quality score
    → Footer (page number + generation date, on every page).

Interactivity
-------------
This isn't just a static document — it uses fpdf2's real PDF navigation
features:
    - A clickable Table of Contents page (`insert_toc_placeholder`):
      every entry jumps straight to its section.
    - Native PDF bookmarks (`start_section`): shows up as a proper
      outline/sidebar panel in Acrobat, Chrome, Preview, etc.
    - "Back to Table of Contents" links under every section heading.
    - Clickable KPI cards on the overview page that jump to their
      corresponding detail section (Rows/Columns → Dataset Information,
      Missing → Missing Values Analysis, Quality → Quality Score).

All of the above is feature-detected at runtime (`hasattr(...)` + a
`SUPPORTS_TOC` flag) and wrapped defensively, so on an older `fpdf`/
`fpdf2` install that lacks these APIs the report still generates
correctly — it just falls back to the plain, non-interactive layout
instead of raising an error. Nothing about the *content* of the report
depends on this; only the navigation layer does.

Depends on statistics.py for calculate_quality_score/get_missing_summary/
get_correlation_insights — those are dataset-description functions, not
PDF-drawing functions, so they stay there and are imported here instead
of duplicated.
"""

import os
import re
import tempfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # headless backend — Streamlit has no display, only saves PNGs to disk
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from fpdf import FPDF

from modules.statistics import calculate_quality_score, get_correlation_insights, get_missing_summary


# ══════════════════════════════════════════════════════════════════════════════
# Report brand colors (RGB tuples — fpdf2's set_fill_color/set_text_color
# both accept *color unpacked like this). Kept as module constants so the
# PDF's palette can be changed in one place.
# ══════════════════════════════════════════════════════════════════════════════
PRIMARY = (67, 97, 238)
SECONDARY = (76, 201, 240)
SUCCESS = (46, 204, 113)
WARNING = (243, 156, 18)
DANGER = (231, 76, 60)
LIGHT = (245, 247, 250)
DARK = (44, 62, 80)

# Whether the installed fpdf/fpdf2 version supports the interactive
# navigation APIs this module uses. Checked once, against the class, so
# every call site can just branch on this flag instead of repeating the
# same hasattr() checks everywhere.
SUPPORTS_TOC = hasattr(FPDF, "insert_toc_placeholder") and hasattr(FPDF, "start_section")
SUPPORTS_LINKS = hasattr(FPDF, "add_link") and hasattr(FPDF, "set_link") and hasattr(FPDF, "link")


class ReportPDF(FPDF):
    """FPDF subclass with a branded header band, a footer that stamps the
    generation date + page number on every page, and (when supported) a
    Table-of-Contents renderer used by insert_toc_placeholder()."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.toc_page = None  # set once the Table of Contents page exists

    def header(self):
        self.set_fill_color(*PRIMARY)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 16)
        self.cell(0, 12, "DataLens AI Report", ln=True, align="C", fill=True)
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Page {self.page_no()}", align="C")

    def render_toc(self, pdf, outline):
        """Callback fpdf2 invokes exactly once, at output() time — after
        every section's real page number is already known — to draw the
        Table of Contents page reserved by insert_toc_placeholder(). Each
        row is a clickable internal link straight to that section.
        """
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(0, 12, "Table of Contents", ln=True)
        pdf.ln(4)
        pdf.set_text_color(0, 0, 0)

        for section in outline:
            link = pdf.add_link()
            pdf.set_link(link, page=section.page_number)
            pdf.set_font("Arial", "B" if section.level == 0 else "", 11)
            pdf.set_x(15 + section.level * 8)
            pdf.cell(150, 9, ("    " * section.level) + section.name, link=link)
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 9, str(section.page_number), align="R", link=link, ln=True)


def _start_section(pdf, title, level=0):
    """Register `title` as both a PDF bookmark (viewer sidebar outline)
    and a Table-of-Contents entry, via fpdf2's start_section(). Silently
    does nothing if the installed version doesn't support it, so callers
    never need their own feature check."""
    if not SUPPORTS_TOC:
        return
    try:
        pdf.start_section(title, level=level)
    except Exception:
        pass


def _add_back_link(pdf):
    """Small clickable 'Back to Table of Contents' line under a section
    heading. No-op until the TOC page exists and link support is available."""
    if not SUPPORTS_LINKS or getattr(pdf, "toc_page", None) is None:
        return
    try:
        link = pdf.add_link()
        pdf.set_link(link, page=pdf.toc_page)
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(0, 5, "^ Back to Table of Contents", align="R", link=link, ln=True)
        pdf.set_text_color(0, 0, 0)
    except Exception:
        pass


def _section_title(pdf, title, subtitle=None, level=0, toc=True):
    """Filled banner section heading, with an optional muted subtitle line.

    When `toc` is True (the default) this also registers the heading as a
    bookmark/Table-of-Contents entry and adds a "Back to Table of Contents"
    link underneath — see _start_section()/_add_back_link(). Pass
    toc=False for any one-off heading that shouldn't clutter the
    navigation (none of the current report sections need this, but it's
    there for future sub-headings).
    """
    if toc:
        _start_section(pdf, title, level=level)

    pdf.set_fill_color(*PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, title, ln=True, fill=True)
    if subtitle:
        pdf.ln(1)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 5, subtitle, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    if toc:
        _add_back_link(pdf)

    pdf.ln(2)


def _body(pdf, text):
    """Plain wrapped paragraph text."""
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _add_kpi_card(pdf, title, value, color, x, y, w=45, h=20, link=None):
    """One small colored KPI tile (used in a row of 4 across the top of
    page 1). When `link` is provided (an id from pdf.add_link()), the
    whole tile becomes clickable and jumps to whatever section later
    calls pdf.set_link(link) — see export_dataset_report()."""
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, h, style="F")
    pdf.set_xy(x + 3, y + 3)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(w - 6, 4, title, ln=True)
    pdf.set_xy(x + 3, y + 10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(w - 6, 6, str(value), ln=True)
    pdf.set_text_color(0, 0, 0)

    if link is not None and SUPPORTS_LINKS:
        try:
            pdf.link(x, y, w, h, link)
        except Exception:
            pass


def _ensure_space(pdf, needed_height):
    """Force a page break if the remaining vertical space on the current
    page is smaller than `needed_height` (in mm). Used before every chart
    image so charts never get sliced across a page boundary — a real bug
    in the previous version, which placed images at hardcoded (x, y)
    coordinates regardless of how much text came before them."""
    if pdf.get_y() + needed_height > pdf.page_break_trigger:
        pdf.add_page()


def _create_plot(path, draw_fn):
    """Run `draw_fn` (which does all the actual plt.* calls), save the
    current matplotlib figure to `path`, then close it so figures don't
    leak across repeated report generations in the same Streamlit session."""
    draw_fn()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def create_histogram(df):
    """Histogram of the first numeric column found."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return None
    column = numeric.columns[0]
    path = os.path.join(tempfile.gettempdir(), "histogram.png")

    def draw():
        plt.figure(figsize=(5.5, 3.2))
        plt.hist(numeric[column].dropna(), bins=20, color="#6366f1", edgecolor="black")
        plt.title(f"Histogram · {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")

    _create_plot(path, draw)
    return path


def create_missing_chart(df):
    """Bar chart of missing-value counts per affected column."""
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        return None
    path = os.path.join(tempfile.gettempdir(), "missing.png")

    def draw():
        plt.figure(figsize=(5.5, 3.2))
        missing.plot(kind="bar", color="#f87171")
        plt.title("Missing values by column")
        plt.ylabel("Count")

    _create_plot(path, draw)
    return path


def create_dtype_chart(df):
    """Pie chart of column dtypes (int64 / float64 / object / ...)."""
    counts = df.dtypes.astype(str).value_counts()
    if counts.empty:
        return None
    path = os.path.join(tempfile.gettempdir(), "dtype.png")

    def draw():
        plt.figure(figsize=(4.8, 4.2))
        plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90,
                colors=["#6366f1", "#22d3a5", "#f59e0b", "#ef4444", "#818cf8"])
        plt.title("Column dtypes")

    _create_plot(path, draw)
    return path


def create_pie_chart(df):
    """Pie chart of the top categories in the dataset's most useful
    categorical column (highest cardinality under 12 unique values, so the
    chart stays readable). Falls back to the dtype breakdown if no such
    column exists — this is what satisfies the report's dedicated
    "Pie chart" section, distinct from the dtype-only chart above."""
    categorical = df.select_dtypes(exclude=np.number)
    candidate = None
    for column in categorical.columns:
        nunique = df[column].nunique(dropna=True)
        if 1 < nunique <= 12:
            candidate = column
            break

    if candidate is None:
        return create_dtype_chart(df)

    counts = df[candidate].value_counts(dropna=False).head(8)
    path = os.path.join(tempfile.gettempdir(), "pie.png")

    def draw():
        plt.figure(figsize=(4.8, 4.2))
        plt.pie(counts.values, labels=[str(v) for v in counts.index], autopct="%1.1f%%", startangle=90,
                colors=["#6366f1", "#22d3a5", "#f59e0b", "#ef4444", "#818cf8", "#a78bfa", "#f472b6", "#34d399"])
        plt.title(f"Proportion of {candidate}")

    _create_plot(path, draw)
    return path


def create_heatmap(df):
    """Correlation heatmap across all numeric columns."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.shape[1] < 2:
        return None
    corr = numeric.corr()
    path = os.path.join(tempfile.gettempdir(), "heatmap.png")

    def draw():
        plt.figure(figsize=(5.5, 4.2))
        plt.imshow(corr, cmap="coolwarm")
        plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right", fontsize=8)
        plt.yticks(range(len(corr.columns)), corr.columns, fontsize=8)
        plt.colorbar()
        plt.title("Correlation heatmap")

    _create_plot(path, draw)
    return path


def add_statistics(pdf, df):
    """'Statistical summary' section: per-numeric-column describe() table."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return

    _section_title(pdf, "Statistical Summary", "Descriptive statistics for every numeric column")
    stats = numeric.describe().round(2)

    for column in stats.columns:
        _ensure_space(pdf, 8 + len(stats.index) * 7)

        pdf.set_fill_color(*PRIMARY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, column, ln=True, fill=True)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 9)
        for idx in stats.index:
            pdf.cell(40, 7, str(idx), border=1)
            pdf.cell(40, 7, str(stats.loc[idx, column]), border=1, ln=True)
        pdf.ln(4)


def add_ai_insights(pdf, ai_text):
    """'AI insights' section: the AI assistant's most recent answer, boxed."""
    _ensure_space(pdf, 40)
    _section_title(pdf, "AI Insights", "Generated by the AI Assistant from this dataset's summary")

    clean_text = re.sub(r"[^\x00-\x7F]+", " ", ai_text or "No AI insights were generated for this dataset.")
    pdf.set_font("Arial", "", 10)
    pdf.set_fill_color(*LIGHT)
    pdf.multi_cell(0, 8, clean_text[:1200], border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)


def add_recommendations(pdf, df):
    """'Smart recommendations' section: a short checklist derived from
    simple, explainable rules about the dataset's current state."""
    _ensure_space(pdf, 60)
    _section_title(pdf, "Smart Recommendations", "Suggested next steps before modeling")

    recommendations = []
    if df.isna().sum().sum() > 0:
        recommendations.append("Fill or drop missing values before training ML models.")
    if df.duplicated().sum() > 0:
        recommendations.append("Remove duplicate records to avoid biased statistics.")
    if len(df) < 500:
        recommendations.append("More rows would likely improve prediction accuracy.")
    if df.select_dtypes(include=np.number).shape[1] > 1:
        recommendations.append("Review highly correlated features for possible feature selection.")
    recommendations += [
        "Normalize or scale numerical features for distance-based models.",
        "Encode categorical variables (one-hot or ordinal, depending on cardinality).",
        "Always split data into train/test sets before evaluating a model.",
    ]

    pdf.set_font("Arial", "", 10)
    for rec in recommendations:
        pdf.multi_cell(0, 7, f"-  {rec}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)


def add_summary(pdf, df, link=None):
    """'Dataset quality score' closing section: the headline score plus a
    one-line verdict on how ready the data is for analysis/modeling.

    Unlike the other add_* helpers this doesn't go through
    _section_title() (it draws its own big banner instead), so it
    registers its own bookmark/TOC entry and back-link, and — if `link`
    is provided (the KPI card's link id) — binds that link to this
    section so the "Quality" KPI card on page 1 jumps here.
    """
    _ensure_space(pdf, 45)
    _start_section(pdf, "Dataset Quality Score", level=0)

    if link is not None and SUPPORTS_LINKS:
        try:
            pdf.set_link(link, page=pdf.page_no())
        except Exception:
            pass

    score = calculate_quality_score(df)

    pdf.set_fill_color(*PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 12, f"Overall Dataset Quality: {score}/100", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    _add_back_link(pdf)
    pdf.ln(3)

    if score >= 90:
        verdict = "Excellent - this dataset is ready for machine learning with minimal prep."
    elif score >= 70:
        verdict = "Good - minor cleaning is recommended before modeling."
    else:
        verdict = "Needs work - address missing values and duplicates before deeper analysis."

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, verdict, new_x="LMARGIN", new_y="NEXT")


def export_dataset_report(df, ai_text=""):
    """Build the full branded, interactive PDF report and return the path
    it was saved to.

    Section order matches the product spec: cover → table of contents →
    overview → KPI cards → dataset info → missing values → statistics →
    correlation → histogram → pie chart → heatmap → AI insights →
    recommendations → quality score. Auto page-breaking (`_ensure_space`
    + fpdf2's own `set_auto_page_break`) is used throughout instead of
    hardcoded (x, y) image coordinates, so sections never overlap
    regardless of how much text precedes them.
    """
    pdf = ReportPDF()
    pdf.set_auto_page_break(True, margin=15)

    try:
        filename = st.session_state.get("filename", "Dataset")
    except Exception:
        filename = "Dataset"

    score = calculate_quality_score(df)
    missing_total = int(df.isna().sum().sum())
    duplicate_total = int(df.duplicated().sum())
    missing_df = get_missing_summary(df)
    quality_subtitle = f"{df.shape[0]:,} rows | {df.shape[1]} columns | {score}/100 quality score"

    # ── Page 1: cover band + overview + KPI cards + dataset info ──
    pdf.add_page()
    pdf.set_fill_color(*PRIMARY)
    pdf.rect(0, 0, 210, 55, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(15, 15)
    pdf.set_font("Arial", "B", 22)
    pdf.cell(0, 10, "DataLens AI Report")
    pdf.set_xy(15, 30)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, "Professional dataset analysis with AI-ready insights")
    pdf.set_xy(15, 43)
    pdf.set_font("Arial", "", 9)
    nav_hint = ("Dataset: " + filename + "   |   Use the Table of Contents or your PDF "
                "viewer's bookmark panel to navigate.") if SUPPORTS_TOC else f"Dataset: {filename}"
    pdf.cell(0, 6, nav_hint)
    pdf.set_text_color(0, 0, 0)

    pdf.set_xy(15, 65)
    _section_title(pdf, "Dataset Overview", quality_subtitle)
    _body(pdf, f"The uploaded dataset contains {df.shape[0]:,} rows and {df.shape[1]} columns. "
                f"The quality score is {score}/100, with {missing_total} missing values and "
                f"{duplicate_total} duplicate rows.")

    # Pre-create link targets for the KPI cards below — the sections they
    # jump to don't exist yet, so we only know *that* a link should exist
    # here; pdf.set_link() binds each one to its real page once that
    # section is actually drawn further down.
    info_link = pdf.add_link() if SUPPORTS_LINKS else None
    missing_link = pdf.add_link() if SUPPORTS_LINKS else None
    quality_link = pdf.add_link() if SUPPORTS_LINKS else None

    kpi_y = pdf.get_y() + 4
    _add_kpi_card(pdf, "Rows", f"{df.shape[0]:,}", PRIMARY, 15, kpi_y, 40, 24, link=info_link)
    _add_kpi_card(pdf, "Columns", df.shape[1], SUCCESS, 60, kpi_y, 40, 24, link=info_link)
    _add_kpi_card(pdf, "Quality", f"{score}%", WARNING, 105, kpi_y, 40, 24, link=quality_link)
    _add_kpi_card(pdf, "Missing", missing_total, DANGER, 150, kpi_y, 40, 24, link=missing_link)
    pdf.set_y(kpi_y + 30)

    _section_title(pdf, "Dataset Information")
    if info_link is not None and SUPPORTS_LINKS:
        try:
            pdf.set_link(info_link, page=pdf.page_no())
        except Exception:
            pass
    info_rows = [
        ("Rows", df.shape[0]),
        ("Columns", df.shape[1]),
        ("Memory usage", f"{round(df.memory_usage(deep=True).sum() / 1024, 2)} KB"),
        ("Duplicate rows", duplicate_total),
        ("Missing cells", missing_total),
    ]
    pdf.set_font("Arial", "", 10)
    for key, value in info_rows:
        pdf.cell(60, 7, str(key), border=1)
        pdf.cell(100, 7, str(value), border=1, ln=True)

    # ── Table of Contents page ──
    # Reserved right after page 1 (so it reads Cover → Contents → rest of
    # the report). insert_toc_placeholder() leaves this page blank and
    # fills it in automatically at pdf.output() time, once every section
    # below has been drawn and its real page number is known.
    if SUPPORTS_TOC:
        try:
            pdf.add_page()
            pdf.toc_page = pdf.page_no()
            pdf.insert_toc_placeholder(pdf.render_toc)
        except Exception:
            pdf.toc_page = None

    # ── Page 3+ (or 2+ without TOC support): missing values → statistics → correlation → charts ──
    pdf.add_page()
    _section_title(pdf, "Missing Values Analysis", "Columns most affected by nulls")
    if missing_link is not None and SUPPORTS_LINKS:
        try:
            pdf.set_link(missing_link, page=pdf.page_no())
        except Exception:
            pass
    if not missing_df.empty:
        pdf.set_font("Arial", "", 9)
        for name, row in missing_df.head(8).iterrows():
            pdf.cell(80, 6, str(name), border=1)
            pdf.cell(30, 6, str(int(row["missing_count"])), border=1)
            pdf.cell(25, 6, f"{row['share']}%", border=1, ln=True)
        pdf.ln(3)
        missing_chart = create_missing_chart(df)
        if missing_chart:
            _ensure_space(pdf, 90)
            pdf.image(missing_chart, w=140)
            pdf.ln(4)
    else:
        _body(pdf, "No missing values were found in this dataset.")

    # Statistical summary — delegated to the (previously unused) helper.
    add_statistics(pdf, df)

    # Correlation analysis
    _ensure_space(pdf, 30)
    corr_pairs = get_correlation_insights(df)
    _section_title(pdf, "Correlation Analysis")
    if corr_pairs:
        pdf.set_font("Arial", "", 10)
        for a, b, value in corr_pairs[:8]:
            pdf.cell(0, 6, f"-  {a} and {b} show a strong correlation ({value})", ln=True)
        pdf.ln(2)
    else:
        _body(pdf, "No strong numeric correlations (|r| >= 0.7) were detected in this dataset.")

    # Histogram, pie chart, heatmap — each guarded by _ensure_space so a
    # chart is never split across a page boundary.
    hist_path = create_histogram(df)
    if hist_path:
        _ensure_space(pdf, 95)
        _section_title(pdf, "Histogram")
        pdf.image(hist_path, w=150)
        pdf.ln(4)

    pie_path = create_pie_chart(df)
    if pie_path:
        _ensure_space(pdf, 100)
        _section_title(pdf, "Pie Chart")
        pdf.image(pie_path, w=120)
        pdf.ln(4)

    heatmap_path = create_heatmap(df)
    if heatmap_path:
        _ensure_space(pdf, 100)
        _section_title(pdf, "Correlation Heatmap")
        pdf.image(heatmap_path, w=150)
        pdf.ln(4)

    # AI insights, recommendations, and the closing quality-score verdict —
    # each of these was previously a dead/unused function; now wired in.
    add_ai_insights(pdf, ai_text)
    add_recommendations(pdf, df)
    add_summary(pdf, df, link=quality_link)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        output_path = tmp.name
    pdf.output(output_path)
    return output_path


def export_to_pdf(ai_text=""):
    """Convenience wrapper used by the Export Report page: reads the current
    dataset out of session_state so callers don't need to pass it explicitly."""
    df = st.session_state.get("df")
    if df is None:
        raise ValueError("No dataset loaded")
    return export_dataset_report(df, ai_text=ai_text)