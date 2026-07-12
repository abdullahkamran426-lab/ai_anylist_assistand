import plotly.express as px

def plot_bar(df, col):
    """Generates an interactive Bar Chart."""
    counts = df[col].value_counts().head(15).reset_index()
    counts.columns = [col, 'Count']
    fig = px.bar(counts, x=col, y='Count', title=f"Distribution of {col}", color=col)
    fig.update_layout(xaxis_title=col, yaxis_title="Count")
    return fig

def plot_histogram(df, col):
    """Generates an interactive Histogram."""
    fig = px.histogram(df, x=col, title=f"Distribution of {col}", nbins=30)
    fig.update_layout(xaxis_title=col, yaxis_title="Frequency")
    return fig

def plot_pie(df, col):
    """Generates an interactive Pie Chart."""
    counts = df[col].value_counts().head(8).reset_index()
    counts.columns = [col, 'Count']
    fig = px.pie(counts, names=col, values='Count', title=f"Proportion of {col}")
    return fig

def plot_scatter(df, x_col, y_col):
    """Generates an interactive Scatter Plot."""
    fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
    fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
    return fig