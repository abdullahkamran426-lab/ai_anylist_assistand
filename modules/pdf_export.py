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

Educational Note for Students:
-----------------------------
Generating PDFs dynamically in Python involves a few key software engineering principles:
1. Document Subclassing: We extend the `FPDF` class so we can override the `header()` and `footer()`
   methods. FPDF calls these hooks automatically whenever a new page is added or a page break occurs.
2. Headless Chart Plotting: Web servers do not have physical displays. We use `matplotlib.use("Agg")`
   to render charts in memory as PNG files, and then insert those files into the PDF.
3. Memory Management: Always call `plt.close()` after generating a chart. Otherwise, figures accumulate
   in memory, leading to memory leaks and resource exhaustion.
4. Character Encoding: Standard PDF fonts (like Arial) only support standard ASCII characters. We strip
   non-ASCII/Unicode characters (e.g., emojis or specialized symbols) from AI text to prevent PDF crashes.
5. Defensive Height Checking: Rather than drawing at static coordinates, we check if there is enough
   height remaining on the current page (`_ensure_space()`) before adding tables or images, forcing a page
   break if needed to keep the document clean.
"""

import os
import re
import tempfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # Headless backend — streamlit runs without a display. Saves plots to disk instead.
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

# Check if the installed FPDF version supports interactive bookmarks and Table of Contents (TOC)
SUPPORTS_TOC = hasattr(FPDF, "insert_toc_placeholder") and hasattr(FPDF, "start_section")
SUPPORTS_LINKS = hasattr(FPDF, "add_link") and hasattr(FPDF, "set_link") and hasattr(FPDF, "link")


class ReportPDF(FPDF):
    """
    Subclass of FPDF to handle custom page styling and layout.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.toc_page = None  # Page number of the Table of Contents

    def header(self):
        """
        FPDF hook called automatically at the start of every page.
        Draws the colored header banner.
        """
        self.set_fill_color(*PRIMARY)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 16)
        self.cell(0, 12, "DataLens AI Report", ln=True, align="C", fill=True)
        self.ln(2)
        # Reset text color back to default black for the page body
        self.set_text_color(0, 0, 0)

    def footer(self):
        """
        FPDF hook called automatically at the bottom of every page.
        Stamps the date and the page number.
        """
        self.set_y(-15)  # Position 15 mm from bottom of page
        self.set_font("Arial", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Page {self.page_no()}", align="C")

    def render_toc(self, pdf, outline):
        """
        Callback invoked by fpdf2 during final output compilation.
        Renders the table of contents page dynamically with links and page numbers.
        """
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(0, 12, "Table of Contents", ln=True)
        pdf.ln(4)
        pdf.set_text_color(0, 0, 0)

        for section in outline:
            # Create a clickable link inside the PDF
            link = pdf.add_link()
            pdf.set_link(link, page=section.page_number)
            
            # Format indentation based on outline hierarchy level
            pdf.set_font("Arial", "B" if section.level == 0 else "", 11)
            pdf.set_x(15 + section.level * 8)
            pdf.cell(150, 9, ("    " * section.level) + section.name, link=link)
            
            # Draw page number on the right side
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 9, str(section.page_number), align="R", link=link, ln=True)


def _start_section(pdf, title, level=0):
    """
    Registers a section bookmark in the PDF outline sidebar and Table of Contents.
    Defensively wraps the call for backwards compatibility with older FPDF versions.
    """
    if not SUPPORTS_TOC:
        return
    try:
        pdf.start_section(title, level=level)
    except Exception:
        pass


def _add_back_link(pdf):
    """
    Renders a clickable link that jumps back to the Table of Contents page.
    """
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
    """
    Draws a standard colored banner heading with optional description subtitle.
    Also handles bookmark creation and table-of-contents back-links.
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
        # multi_cell automatically wraps text to new lines
        pdf.multi_cell(0, 5, subtitle, new_x="LMARGIN", new_y="NEXT")
        
    pdf.set_text_color(0, 0, 0)

    if toc:
        _add_back_link(pdf)

    pdf.ln(2)


def _body(pdf, text):
    """Renders basic wrapped body paragraph text."""
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _add_kpi_card(pdf, title, value, color, x, y, w=45, h=20, link=None):
    """
    Draws a solid colored KPI card displaying a key metric.
    If 'link' is provided, the card behaves as a button jumping to that section.
    """
    # Draw background rectangle
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, h, style="F")
    
    # Render card title
    pdf.set_xy(x + 3, y + 3)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(w - 6, 4, title, ln=True)
    
    # Render card numeric value
    pdf.set_xy(x + 3, y + 10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(w - 6, 6, str(value), ln=True)
    pdf.set_text_color(0, 0, 0)

    # Bind link to the card boundaries
    if link is not None and SUPPORTS_LINKS:
        try:
            pdf.link(x, y, w, h, link)
        except Exception:
            pass


def _ensure_space(pdf, needed_height):
    """
    Checks if there is enough height remaining on the current page.
    If not, it triggers a page break. Prevents images and tables from breaking awkwardly.
    """
    if pdf.get_y() + needed_height > pdf.page_break_trigger:
        pdf.add_page()


def _create_plot(path, draw_fn):
    """
    Executes a matplotlib plot function, saves the figure, and closes the plot context.
    
    Why close?
    Matplotlib standard behaviors keep plots in memory. If not explicitly closed,
    re-running report generation can cause RAM exhaustion or duplicate figure layers.
    """
    draw_fn()
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def create_histogram(df):
    """Generates a histogram plot for the first numeric column."""
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
    """Generates a bar chart showing columns with missing values."""
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
    """Generates a pie chart of column data types."""
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
    """
    Generates a pie chart of categories for the most useful categorical column
    (meaning the column has low category cardinality, 2 to 12 classes).
    """
    categorical = df.select_dtypes(exclude=np.number)
    candidate = None
    for column in categorical.columns:
        nunique = df[column].nunique(dropna=True)
        if 1 < nunique <= 12:
            candidate = column
            break

    # Fall back to dtype breakdown if no low-cardinality categorical columns exist
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
    """Generates a correlation heatmap across all numeric columns."""
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
    """Renders the descriptive statistics section."""
    numeric = df.select_dtypes(include=np.number)
    if numeric.empty:
        return

    _section_title(pdf, "Statistical Summary", "Descriptive statistics for every numeric column")
    stats = numeric.describe().round(2)

    for column in stats.columns:
        # Check height to avoid breaking stats tables across page breaks
        _ensure_space(pdf, 8 + len(stats.index) * 7)

        # Draw column header
        pdf.set_fill_color(*PRIMARY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, column, ln=True, fill=True)

        # Render stats rows
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 9)
        for idx in stats.index:
            pdf.cell(40, 7, str(idx), border=1)
            pdf.cell(40, 7, str(stats.loc[idx, column]), border=1, ln=True)
        pdf.ln(4)


def add_ai_insights(pdf, ai_text):
    """
    Renders the AI Assistant response section.
    
    Why clean_text with regular expressions?
    Standard PDF fonts (Helvetica, Times, Arial) cannot parse Unicode symbols or emojis.
    Passing emojis to pdf.cell causes standard FPDF to crash. We strip non-ASCII characters to be safe.
    """
    _ensure_space(pdf, 40)
    _section_title(pdf, "AI Insights", "Generated by the AI Assistant from this dataset's summary")

    clean_text = re.sub(r"[^\x00-\x7F]+", " ", ai_text or "No AI insights were generated for this dataset.")
    pdf.set_font("Arial", "", 10)
    pdf.set_fill_color(*LIGHT)
    pdf.multi_cell(0, 8, clean_text[:1200], border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)


def add_recommendations(pdf, df):
    """Renders suggestions checklist based on the dataset state."""
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
    """Renders quality score banner and detailed verdict."""
    _ensure_space(pdf, 45)
    _start_section(pdf, "Dataset Quality Score", level=0)

    if link is not None and SUPPORTS_LINKS:
        try:
            pdf.set_link(link, page=pdf.page_no())
        except Exception:
            pass

    score = calculate_quality_score(df)

    # Draw banner
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
    """
    Builds the full interactive PDF report and saves it to a temporary path.
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

    # ── Cover page band + KPI cards + information details ──
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

    # Links setup for cards
    info_link = pdf.add_link() if SUPPORTS_LINKS else None
    missing_link = pdf.add_link() if SUPPORTS_LINKS else None
    quality_link = pdf.add_link() if SUPPORTS_LINKS else None

    # Draw KPI cards
    kpi_y = pdf.get_y() + 4
    _add_kpi_card(pdf, "Rows", f"{df.shape[0]:,}", PRIMARY, 15, kpi_y, 40, 24, link=info_link)
    _add_kpi_card(pdf, "Columns", df.shape[1], SUCCESS, 60, kpi_y, 40, 24, link=info_link)
    _add_kpi_card(pdf, "Quality", f"{score}%", WARNING, 105, kpi_y, 40, 24, link=quality_link)
    _add_kpi_card(pdf, "Missing", missing_total, DANGER, 150, kpi_y, 40, 24, link=missing_link)
    pdf.set_y(kpi_y + 30)

    # Info table
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

    # ── Table of Contents placeholder page ──
    if SUPPORTS_TOC:
        try:
            pdf.add_page()
            pdf.toc_page = pdf.page_no()
            pdf.insert_toc_placeholder(pdf.render_toc)
        except Exception:
            pdf.toc_page = None

    # ── Details section pages ──
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

    # Descriptive Statistics
    add_statistics(pdf, df)

    # Correlation relationships
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

    # Charts & Plots
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

    # AI and closing summary sections
    add_ai_insights(pdf, ai_text)
    add_recommendations(pdf, df)
    add_summary(pdf, df, link=quality_link)

    # Output to file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        output_path = tmp.name
    pdf.output(output_path)
    return output_path


def export_to_pdf(ai_text=""):
    """
    Convenience wrapper pulling the dataset from st.session_state.
    """
    df = st.session_state.get("df")
    if df is None:
        raise ValueError("No dataset loaded")
    return export_dataset_report(df, ai_text=ai_text)