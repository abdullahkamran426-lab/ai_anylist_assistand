<div align="center">

# ✦ PROJECT OVERVIEW

### Data Analysis Assistant

<p>
  Upload any CSV dataset and transform it into interactive visualizations,<br/>
  statistical summaries, and AI-generated insights — all in minutes.
</p>

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](#)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=flat-square&logo=plotly&logoColor=white)](#)
[![OpenRouter](https://img.shields.io/badge/AI-OpenRouter-7C5CFC?style=flat-square)](#)

**🌐 Live App:** [https://aianylistassistand-e4ufhunamkwkljyylj6col.streamlit.app/](https://aianylistassistand-e4ufhunamkwkljyylj6col.streamlit.app/)

</div>

---

## 📌 Overview

**DataMind AI** is a modular Streamlit web application for interactive CSV data exploration.  
It combines automated cleaning, Plotly visualizations, descriptive statistics, and a natural-language AI assistant — all accessible through a clean, sidebar-navigated interface.

> **Stack:** Python · Streamlit · Pandas · Plotly · OpenRouter (Llama 3.1) · FPDF

---

## ✨ Features

|  | Feature | Description |
|:---:|:---|:---|
| 📤 | **CSV Upload** | Drag-and-drop any `.csv` file; encoding fallbacks handled automatically |
| 🧹 | **Auto-Clean** | Deduplication, missing-value detection, and type normalization |
| 👁 | **Dataset Preview** | Full table view with row, column, and missing value summary |
| 📊 | **Statistics** | Numeric `describe()`, per-column missing values, and categorical counts |
| 📈 | **Visualizations** | Bar, Histogram, Pie, and Scatter plots powered by Plotly |
| 🤖 | **AI Assistant** | Ask natural-language questions via Llama 3.1 8B on OpenRouter |
| 📄 | **PDF Export** | Download AI-generated analysis as a professional PDF report |

---

## 🗂 Repository Structure

```text
Hackathon/
├── main.py              # App entrypoint — routing, UI, session state
├── modules/             # Helper modules package
│   ├── __init__.py      # Package marker
│   ├── analysis.py      # Data loading, cleaning, statistics, PDF export
│   ├── visualization.py # Plotly chart generators
│   ├── ai_helper.py     # OpenRouter AI client and question handler
│   ├── config.py        # Configuration constants
│   ├── session.py       # Session state management
│   ├── sidebar.py       # Sidebar rendering
│   ├── utils.py         # Helper functions
│   ├── pages/           # Page rendering functions (package)
│   │   ├── __init__.py  # Re-exports all render_* functions
│   │   ├── home.py      # Landing page
│   │   ├── upload.py    # CSV upload & auto-clean
│   │   ├── clean_data.py # Interactive data cleaning
│   │   ├── dataset_preview.py # Table view
│   │   ├── statistics.py # Numeric stats & categories
│   │   ├── visualizations.py # Plotly charts
│   │   ├── ai_assistant.py # AI Q&A interface
│   │   ├── export_report.py # PDF report generation
│   │   └── about.py     # App information
│   └── style/           # CSS styling (package)
│       ├── __init__.py  # Aggregates all CSS modules
│       ├── base.py      # Font imports & color palette
│       ├── sidebar.py   # Sidebar styling
│       ├── widgets.py   # Generic widget styling
│       ├── layout.py    # Layout components
│       ├── upload.py    # Upload page styling
│       └── explore.py   # Stats/Visualizations styling
├── requirements.txt     # Python dependencies
├── .env                 # API key (not committed)
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### 1 · Clone the Repository

```bash
git clone https://github.com/abdullahkamran426-lab/ai_anylist_assistand.git
cd datamind-ai
```

### 2 · Create & Activate a Virtual Environment

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3 · Install Dependencies

```bash
pip install -r requirements.txt
```

### 4 · Configure the Environment

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

> 🔑 Get your free API key at [openrouter.ai/keys](https://openrouter.ai/keys)

### 5 · Launch the App

```bash
streamlit run main.py
```

The app will open at `http://localhost:8501`.

---

## 🔄 Application Workflow

```mermaid
flowchart TD
    A([👤 User]) --> B[Launch Streamlit App]
    B --> C["main.py<br/>↓<br/>initialize_session_state()"]
    C --> D["style/__init__.py<br/>↓<br/>inject_css()"]
    D --> E["sidebar.py<br/>↓<br/>render_sidebar()"]
    E --> F{Sidebar Navigation}

    F --> G[📤 Upload CSV]
    G --> H["pages/upload.py<br/>render_upload_page()"]
    H --> I["analysis.load_data()<br/>encoding fallback"]
    I --> J["analysis.clean_data()<br/>normalize types"]
    J --> K[(📦 Session State<br/>DataFrame)]

    K --> L[👁 Dataset Preview]
    K --> M[📊 Statistics]
    K --> N[📈 Visualizations]
    K --> O[🤖 AI Assistant]

    L  --> L1["pages/dataset_preview.py<br/>render_dataset_preview_page()"]
    M  --> M1["pages/statistics.py<br/>render_statistics_page()"]
    M1 --> M2["analysis.get_numeric_stats()"]
    N  --> N1["pages/visualizations.py<br/>render_visualizations_page()"]
    N1 --> N2["visualization.plot_*()<br/>bar / histogram / pie / scatter"]

    O  --> O1["pages/ai_assistant.py<br/>render_ai_assistant_page()"]
    O1 --> O2["analysis.get_summary()"]
    O2 --> O3["ai_helper.ask_ai()<br/>↓<br/>OpenRouter API"]
    O3 --> O4["Llama 3.1 8B<br/>Response"]
    O4 --> O5[(💾 session_state<br/>answer)]

    O5  --> P[📄 Export Report]
    P  --> P1["pages/export_report.py<br/>render_export_page()"]
    P1 --> P2["analysis.export_to_pdf()"]
    P2 --> Q([⬇ Download PDF])

    style A  fill:#7C5CFC,color:#fff,stroke:none
    style K  fill:#1C2435,color:#DCE4F0,stroke:#2D3A52
    style O5 fill:#1C2435,color:#DCE4F0,stroke:#2D3A52
    style Q  fill:#00D68F,color:#fff,stroke:none
```

---

## 🧩 Module Reference

<details>
<summary><strong>📄 main.py — Application Orchestrator</strong></summary>
<br/>

Clean entry point that delegates all functionality to modules. Handles page routing, session state initialization, CSS injection, and sidebar rendering.

| Section | Purpose |
|:---|:---|
| Imports | Imports from modules package (style, session, sidebar, pages) |
| Page Config | Sets Streamlit page title, icon, and layout |
| CSS Injection | Calls `inject_css()` from `style` package |
| Session Init | Calls `initialize_session_state()` from `session` module |
| Sidebar | Calls `render_sidebar()` to get selected page |
| Page Routing | Routes to appropriate `render_*()` function from `pages` package |

</details>

<details>
<summary><strong>📦 modules/config.py — Configuration Constants</strong></summary>
<br/>

Centralized application configuration.

| Constant | Description |
|:---|:---|
| `LARGE_DF_THRESHOLD` | Row count threshold for sampling (default: 50,000) |
| `NAV_OPTIONS` | List of page names for sidebar navigation |
| `SESSION_STATE_DEFAULTS` | Dictionary of default session state values |

</details>

<details>
<summary><strong>🎨 modules/style/ — CSS Styling Package</strong></summary>
<br/>

Contains all custom CSS for the application, split across focused modules for maintainability.

| Module | Description |
|:---|:---|
| `base.py` | Google Font imports, CSS custom property palette (--accent, --card, --border, etc.), base html/body rules |
| `sidebar.py` | Sidebar navigation re-skin |
| `widgets.py` | Generic Streamlit widget skins (buttons, dataframe, input fields, etc.) |
| `layout.py` | Custom layout primitives shared across pages (.hero, .pill, .section-label, .panel, etc.) |
| `upload.py` | Upload Dataset page-specific styling |
| `explore.py` | Dataset Preview / Statistics / Visualizations page styling |
| `__init__.py` | Aggregates all CSS modules and exports `inject_css()` and `get_css()` |

**Public API:** `inject_css()` — called once at the start of main.py to inject the complete compiled stylesheet.

</details>

<details>
<summary><strong>💾 modules/session.py — Session State Management</strong></summary>
<br/>

Manages Streamlit session state initialization and cleanup.

| Function | Description |
|:---|:---|
| `initialize_session_state()` | Initializes all session state variables with defaults |
| `clear_dataset_state()` | Clears dataset-related session state (df, filename, logs, etc.) |

</details>

<details>
<summary><strong>📋 modules/sidebar.py — Sidebar Rendering</strong></summary>
<br/>

Renders the application sidebar with navigation, dataset status, and branding.

| Function | Description |
|:---|:---|
| `render_sidebar()` | Renders complete sidebar and returns selected page name |

Includes: logo with pulsing AI status, navigation radio, dataset status badge (with health percentage), clear dataset button, and footer.

</details>

<details>
<summary><strong>🛠️ modules/utils.py — Helper Functions</strong></summary>
<br/>

Utility functions used throughout the application.

| Function | Description |
|:---|:---|
| `section(label, title)` | Renders consistent section header pattern |
| `sample_df_for_speed(frame, enabled, n)` | Returns sampled dataframe for large datasets |

</details>

<details>
<summary><strong>📄 modules/pages/ — Page Rendering Functions Package</strong></summary>
<br/>

All page rendering functions for the application, split into one module per page for scalability and maintainability.

| Module | Function | Description |
|:---|:---|:---|
| `home.py` | `render_home_page()` | Landing page with app overview and feature cards |
| `upload.py` | `render_upload_page()` | CSV upload with auto-clean and success banner |
| `clean_data.py` | `render_clean_data_page()` | Interactive data cleaning with live preview |
| `dataset_preview.py` | `render_dataset_preview_page()` | Full table view with column details |
| `statistics.py` | `render_statistics_page()` | Numeric stats, missing values, value counts |
| `visualizations.py` | `render_visualizations_page()` | Plotly chart builder (bar, histogram, pie, scatter) |
| `ai_assistant.py` | `render_ai_assistant_page()` | Natural-language Q&A with conversation history |
| `export_report.py` | `render_export_page()` | PDF report generation and download |
| `about.py` | `render_about_page()` | App information and technology stack |

**Public API:** `__init__.py` re-exports all `render_*` functions, so imports in main.py remain unchanged: `from modules.pages import render_home_page, render_upload_page, ...`

</details>

<details>
<summary><strong>🔧 modules/analysis.py — Data & Export Utilities</strong></summary>
<br/>

| Function | Signature | Description |
|:---|:---|:---|
| `load_data` | `(uploaded_file)` | Reads CSV with encoding fallbacks (`utf-8` → `cp1252` → `latin1`). Cached with `@st.cache_data`. |
| `clean_data` | `(df)` | Strips commas from `Gross` column and casts it to numeric. Returns cleaned DataFrame. |
| `get_summary` | `(df, filename)` | Builds a text snapshot (filename, shape, dtypes, head, describe) for the AI prompt. |
| `get_numeric_stats` | `(df)` | Returns `df.describe()` for numeric columns, or `None` if none exist. |
| `get_category_counts` | `(df, col)` | Returns `value_counts()` for a given categorical column. |
| `export_to_pdf` | `(text, filename)` | Writes AI response to a PDF via FPDF, stripping non-ASCII characters first. |

</details>

<details>
<summary><strong>📈 modules/visualization.py — Chart Generators</strong></summary>
<br/>

All functions return a **Plotly figure object** ready for `st.plotly_chart()`.

| Function | Chart Type | Notes |
|:---|:---|:---|
| `plot_bar(df, col)` | Bar chart | Top 15 value counts of a categorical column |
| `plot_histogram(df, col)` | Histogram | 30 bins across a numeric column |
| `plot_pie(df, col)` | Pie chart | Top 8 categories of a categorical column |
| `plot_scatter(df, x, y)` | Scatter plot | Two numeric columns on X and Y axes |

</details>

<details>
<summary><strong>🤖 modules/ai_helper.py — AI Integration</strong></summary>
<br/>

| Setting | Value |
|:---|:---|
| Provider | OpenRouter (OpenAI-compatible API) |
| Model | `meta-llama/llama-3.1-8b-instruct` |
| `max_tokens` | `500` |
| `temperature` | `0.3` |
| Fallback | Returns a descriptive error string if the API key is missing or a request fails |

**`ask_ai(question, dataset_summary)`**  
Sends a combined prompt — dataset context and user question — to the model and returns the generated response string.

</details>

---

## 📦 Dependencies

| Library | Purpose | Active |
|:---|:---|:---:|
| `streamlit` | Web UI framework | ✅ |
| `pandas` | Data loading and manipulation | ✅ |
| `plotly` | Interactive chart rendering | ✅ |
| `fpdf` | PDF report generation | ✅ |
| `openai` | OpenRouter-compatible AI client | ✅ |
| `python-dotenv` | `.env` variable loading | ✅ |
| `numpy` | Numeric utilities | ✅ |

---

## 🛠 Technology Stack

| Technology | Why It's Used |
|:---|:---|
| **Python** | Primary language - extensive data science ecosystem, easy to read, great for rapid prototyping |
| **Streamlit** | Web UI framework - enables building interactive data apps with pure Python, no HTML/CSS/JS knowledge required, perfect for data tools |
| **Pandas** | Data manipulation - industry-standard for CSV loading, cleaning, and statistical analysis, powerful DataFrame operations |
| **Plotly** | Interactive visualizations - creates beautiful, interactive charts that work in browsers, better than static matplotlib for web apps |
| **OpenRouter (Llama 3.1)** | AI integration - provides access to state-of-the-art LLMs for natural-language data analysis, cost-effective alternative to OpenAI |
| **FPDF** | PDF generation - lightweight library for creating downloadable reports without complex dependencies |
| **OpenAI SDK** | AI client - OpenRouter-compatible client for making API calls to LLMs with proper error handling |
| **python-dotenv** | Environment management - securely loads API keys from `.env` files, prevents hardcoding sensitive data |
| **NumPy** | Numerical computing - efficient array operations, used by pandas for numeric column detection and statistics |

---

## ⚙️ Configuration Reference

| Variable | File | Description |
|:---|:---|:---|
| `OPENROUTER_API_KEY` | `.env` | Your OpenRouter API key — required for the AI assistant |

---

## 📝 Notes

- The **AI assistant is optional** — all other features work without an API key configured.
- `clean_data()` currently targets a `Gross` column specifically. Extend it in `analysis.py` for your dataset's structure.
- `matplotlib` and `seaborn` are in `requirements.txt` but not yet wired to any charts — swap Plotly functions in `visualization.py` if you prefer them.


---

<div align="center">
  Built with 🐍 Python &nbsp;·&nbsp; ⚡ Streamlit &nbsp;·&nbsp; 🤖 OpenRouter
</div>
