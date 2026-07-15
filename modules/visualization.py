import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_bar(df, col):
    counts = df[col].value_counts().head(15).reset_index()
    counts.columns = [col, "Count"]
    fig = px.bar(counts, x=col, y="Count", title=f"Distribution of {col}", color=col)
    fig.update_layout(xaxis_title=col, yaxis_title="Count")
    return fig


def plot_histogram(df, col):
    fig = px.histogram(df, x=col, title=f"Distribution of {col}", nbins=30)
    fig.update_layout(xaxis_title=col, yaxis_title="Frequency")
    return fig


def plot_pie(df, col):
    counts = df[col].value_counts().head(8).reset_index()
    counts.columns = [col, "Count"]
    fig = px.pie(counts, names=col, values="Count", title=f"Proportion of {col}")
    return fig


def plot_scatter(df, x_col, y_col):
    fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}", trendline="ols")
    fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
    return fig


def plot_box(df, col):
    fig = px.box(df, y=col, title=f"Box plot for {col}")
    return fig


def plot_violin(df, col):
    fig = px.violin(df, y=col, box=True, title=f"Violin plot for {col}")
    return fig


def plot_line(df, x_col, y_col):
    fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
    return fig


def plot_area(df, x_col, y_col):
    fig = px.area(df, x=x_col, y=y_col, title=f"Area chart for {y_col}")
    return fig


def plot_bubble(df, x_col, y_col, size_col=None):
    size_series = size_col or y_col
    fig = px.scatter(df, x=x_col, y=y_col, size=size_series, title=f"Bubble chart for {y_col}")
    return fig


def plot_treemap(df, path, values):
    fig = px.treemap(df, path=path, values=values)
    return fig


def plot_sunburst(df, path, values):
    fig = px.sunburst(df, path=path, values=values)
    return fig


def plot_correlation_matrix(df):
    numeric = df.select_dtypes(include="number")
    if numeric.empty or numeric.shape[1] < 2:
        return go.Figure()
    corr = numeric.corr()
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="Purples")
    fig.update_layout(title="Correlation matrix")
    return fig