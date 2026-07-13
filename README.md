# Project Documentation

## 1. Project Overview

This repository contains a Streamlit-based web application for interactive CSV data analysis. The app is designed to let users:

- Upload a CSV dataset.
- Clean and inspect the dataset.
- View summary statistics and missing-value analysis.
- Build interactive Plotly charts.
- Ask an AI assistant questions about the dataset.
- Export AI-generated insights to a PDF report.

The codebase is small and organized as a flat structure with an entrypoint (`main.py`) and helper modules.

## 2. Repository Structure

```text
ali/
|-- main.py
|-- analysis.py
|-- visualization.py
|-- ai_helper.py
|-- requirements.txt
|-- .env
|-- .gitignore
|-- README.md
```

### Source Files

- `main.py`: Streamlit application entrypoint, page routing, UI controls, and integration with helper modules.
- `analysis.py`: Data loading, cleaning, summary generation, statistics helpers, and PDF export.
- `visualization.py`: Plotly figure generation for bar charts, histograms, pie charts, and scatter plots.
- `ai_helper.py`: OpenRouter/OpenAI client initialization and AI question-answering logic.
- `requirements.txt`: Python dependencies required for the application.

### Environment File

- `.env`: Environment variables, typically storing `OPENROUTER_API_KEY`.

## 3. Module Summaries and Function Documentation

### `main.py`

#### Role

Acts as the application controller and Streamlit UI definition. It:

- Configures the page layout and style.
- Builds the sidebar navigation.
- Initializes session state values.
- Handles dataset upload and cleaning workflow.
- Presents preview, statistics, visualizations, AI assistant, and export pages.

#### Major Functional Areas

- `Home`: App introduction and feature overview.
- `Upload Dataset`: Accepts CSV upload, reads the file, cleans it, and stores it in session state.
- `Clean Data`: Provides interactive cleaning controls for duplicate removal, missing values, dropping/renaming columns, type casting, and filters.
- `Dataset Preview`: Displays the full dataset, column dtypes, missing counts, and duplicates.
- `Statistics`: Shows numeric statistics, missing values, and categorical value counts.
- `Visualizations`: Renders selected Plotly charts based on dataset columns.
- `AI Assistant`: Sends a dataset summary and user question to the AI helper.
- `Export Report`: Generates a PDF from the AI response and offers it for download.
- `About`: Describes the app and its feature set.

#### Dependencies

- Imports from `analysis.py`, `visualization.py`, and `ai_helper.py`.
- Uses Streamlit for layout and interactive controls.

### `analysis.py`

#### Role

Provides reusable data-processing utilities and export capabilities.

#### Functions

- `load_data(uploaded_file)`
  - Reads a CSV file with fallback encodings: `utf-8`, `cp1252`, and `latin1`.
  - Uses `@st.cache_data` to cache loaded datasets in Streamlit sessions.

- `clean_data(df)`
  - Specifically cleans a `Gross` column by removing commas and converting values to numeric.
  - Returns the cleaned DataFrame.

- `get_summary(df, filename)`
  - Builds a textual summary of the dataset with filename, row/column counts, column names, dtypes, first rows, and descriptive statistics.
  - This summary is used to prompt the AI assistant.

- `get_numeric_stats(df)`
  - Selects numeric columns and returns `DataFrame.describe()`.
  - Returns `None` if there are no numeric columns.

- `get_category_counts(df, col)`
  - Returns `value_counts()` for a selected categorical column.
  - Currently not used directly by `main.py`, but available as a helper.

- `export_to_pdf(text_content, filename="AI_Analysis_Report.pdf")`
  - Writes the AI-generated response text to a PDF using FPDF.
  - Removes non-ASCII characters before writing to avoid FPDF encoding issues.

### `visualization.py`

#### Role

Contains chart-generation helpers that return Plotly figure objects.

#### Functions

- `plot_bar(df, col)`
  - Creates a bar chart from the top 15 value counts of a categorical column.
  - Returns a Plotly bar figure.

- `plot_histogram(df, col)`
  - Creates a histogram for a numeric column with 30 bins.
  - Returns a Plotly histogram figure.

- `plot_pie(df, col)`
  - Creates a pie chart for the top 8 categories in a categorical column.
  - Returns a Plotly pie figure.

- `plot_scatter(df, x_col, y_col)`
  - Creates a scatter plot for two numeric columns.
  - Returns a Plotly scatter figure.

### `ai_helper.py`

#### Role

Handles AI client initialization and dataset question answering.

#### Behavior

- Loads environment variables from `.env` using `load_dotenv()`.
- Reads `OPENROUTER_API_KEY` and initializes an `OpenAI` client if available.
- If the API key is missing, sets `client = None` and returns a helpful missing-key message.

#### Functions

- `ask_ai(question, dataset_summary)`
  - Sends a chat completion request to the OpenRouter-backed model.
  - Uses the model `meta-llama/llama-3.1-8b-instruct`.
  - Sets `max_tokens=500` and `temperature=0.3`.
  - Returns the AI response or an error string if a failure occurs.

## 4. Dependency Notes

### Required Libraries

From `requirements.txt`:

- `pandas`
- `numpy`
- `matplotlib` (not currently used in code)
- `seaborn` (not currently used in code)
- `plotly`
- `fpdf`
- `python-dotenv`
- `streamlit`
- `openai`

### Observations

- `matplotlib` and `seaborn` are installed but not referenced by the current source files.
- The AI flow is optional if `OPENROUTER_API_KEY` is not configured.

## 5. Running the App

### Setup

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Environment

Create a `.env` file containing:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
```

### Launch

```powershell
streamlit run main.py
```
