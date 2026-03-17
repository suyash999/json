"""
═══════════════════════════════════════════════════════════════════════
EDA ENGINE — Automatic Exploratory Data Analysis
═══════════════════════════════════════════════════════════════════════
Detects column types and generates appropriate visualizations.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


def detect_column_types(df: pd.DataFrame) -> dict:
    """
    Classify columns into: numeric, categorical, text, datetime, boolean.
    """
    types = {
        "numeric": [],
        "categorical": [],
        "text": [],
        "datetime": [],
        "boolean": [],
    }

    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            continue

        # Boolean check
        unique_vals = series.unique()
        if set(str(v).lower() for v in unique_vals) <= {'true', 'false', '1', '0', 'yes', 'no'}:
            types["boolean"].append(col)
            continue

        # Datetime check
        if pd.api.types.is_datetime64_any_dtype(series):
            types["datetime"].append(col)
            continue
        if series.dtype == 'object':
            try:
                sample = series.head(50)
                parsed = pd.to_datetime(sample, infer_datetime_format=True, errors='coerce')
                if parsed.notna().mean() > 0.7:
                    types["datetime"].append(col)
                    continue
            except Exception:
                pass

        # Numeric check
        if pd.api.types.is_numeric_dtype(series):
            if series.nunique() <= 10 and series.nunique() / len(series) < 0.05:
                types["categorical"].append(col)
            else:
                types["numeric"].append(col)
            continue

        # Text vs Categorical
        if series.dtype == 'object':
            avg_len = series.astype(str).str.len().mean()
            n_unique = series.nunique()
            ratio = n_unique / len(series)

            if avg_len > 60 or (n_unique > 100 and ratio > 0.5):
                types["text"].append(col)
            else:
                types["categorical"].append(col)
            continue

        types["categorical"].append(col)

    return types


def generate_data_summary(df: pd.DataFrame) -> dict:
    """Generate a quick data summary."""
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "missing_pct": round(df.isnull().mean().mean() * 100, 1),
        "duplicates": df.duplicated().sum(),
    }


def plot_numeric_distribution(df: pd.DataFrame, col: str) -> go.Figure:
    """Histogram + box plot for numeric columns."""
    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3],
                        shared_xaxes=True, vertical_spacing=0.05)
    fig.add_trace(
        go.Histogram(x=df[col].dropna(), name=col, marker_color='#e8a838',
                     opacity=0.8, nbinsx=40),
        row=1, col=1,
    )
    fig.add_trace(
        go.Box(x=df[col].dropna(), name=col, marker_color='#e8a838',
               line_color='#c48a18'),
        row=2, col=1,
    )
    fig.update_layout(
        title=f"Distribution: {col}",
        showlegend=False,
        template="plotly_dark",
        height=350,
        margin=dict(l=40, r=20, t=40, b=20),
    )
    return fig


def plot_categorical_distribution(df: pd.DataFrame, col: str, top_n: int = 20) -> go.Figure:
    """Bar chart for categorical columns."""
    counts = df[col].value_counts().head(top_n)
    fig = go.Figure(go.Bar(
        x=counts.values,
        y=counts.index.astype(str),
        orientation='h',
        marker_color='#e8a838',
    ))
    fig.update_layout(
        title=f"Top {min(top_n, len(counts))} values: {col}",
        template="plotly_dark",
        height=max(250, min(top_n * 25, 500)),
        margin=dict(l=150, r=20, t=40, b=20),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def plot_datetime_distribution(df: pd.DataFrame, col: str) -> go.Figure:
    """Time series line chart."""
    series = pd.to_datetime(df[col], errors='coerce').dropna()
    daily = series.dt.date.value_counts().sort_index()
    fig = go.Figure(go.Scatter(
        x=daily.index, y=daily.values,
        mode='lines+markers',
        line=dict(color='#e8a838', width=2),
        marker=dict(size=4),
    ))
    fig.update_layout(
        title=f"Timeline: {col}",
        template="plotly_dark",
        height=300,
        margin=dict(l=40, r=20, t=40, b=20),
    )
    return fig


def plot_text_stats(df: pd.DataFrame, col: str) -> go.Figure:
    """Word count distribution for text columns."""
    word_counts = df[col].fillna('').astype(str).str.split().str.len()
    fig = go.Figure(go.Histogram(
        x=word_counts, nbinsx=50,
        marker_color='#e8a838', opacity=0.8,
    ))
    fig.update_layout(
        title=f"Word Count Distribution: {col}",
        xaxis_title="Words",
        yaxis_title="Count",
        template="plotly_dark",
        height=300,
        margin=dict(l=40, r=20, t=40, b=20),
    )
    return fig


def plot_missing_values(df: pd.DataFrame) -> go.Figure:
    """Missing values heatmap."""
    missing = df.isnull().mean().sort_values(ascending=False)
    missing = missing[missing > 0]
    if missing.empty:
        return None
    fig = go.Figure(go.Bar(
        x=missing.values * 100,
        y=missing.index,
        orientation='h',
        marker_color=['#e74c3c' if v > 0.3 else '#f39c12' if v > 0.1 else '#2ecc71'
                      for v in missing.values],
    ))
    fig.update_layout(
        title="Missing Values (%)",
        template="plotly_dark",
        height=max(200, len(missing) * 25),
        margin=dict(l=150, r=20, t=40, b=20),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def plot_correlation_matrix(df: pd.DataFrame, numeric_cols: list) -> go.Figure:
    """Correlation heatmap for numeric columns."""
    if len(numeric_cols) < 2:
        return None
    corr = df[numeric_cols].corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.index,
        colorscale='RdYlGn',
        zmin=-1, zmax=1,
        text=np.round(corr.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
    ))
    fig.update_layout(
        title="Correlation Matrix",
        template="plotly_dark",
        height=max(350, len(numeric_cols) * 40),
        margin=dict(l=100, r=20, t=40, b=100),
    )
    return fig


def run_eda(df: pd.DataFrame):
    """Run full EDA and display in Streamlit."""
    col_types = detect_column_types(df)
    summary = generate_data_summary(df)

    # ── Summary metrics ──
    st.markdown("### 📊 Dataset Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows", f"{summary['rows']:,}")
    c2.metric("Columns", summary['columns'])
    c3.metric("Memory", f"{summary['memory_mb']} MB")
    c4.metric("Missing %", f"{summary['missing_pct']}%")
    c5.metric("Duplicates", f"{summary['duplicates']:,}")

    # ── Column types ──
    st.markdown("### 🏷️ Detected Column Types")
    type_cols = st.columns(5)
    labels = ["Numeric", "Categorical", "Text", "Datetime", "Boolean"]
    keys = ["numeric", "categorical", "text", "datetime", "boolean"]
    icons = ["🔢", "📁", "📝", "📅", "✅"]
    for i, (label, key, icon) in enumerate(zip(labels, keys, icons)):
        with type_cols[i]:
            cols_list = col_types[key]
            st.markdown(f"**{icon} {label}** ({len(cols_list)})")
            for c in cols_list[:8]:
                st.caption(f"→ {c}")
            if len(cols_list) > 8:
                st.caption(f"... +{len(cols_list)-8} more")

    # ── Data preview ──
    st.markdown("### 👀 Data Preview")
    st.dataframe(df.head(20), use_container_width=True, height=350)

    # ── Missing values ──
    fig_missing = plot_missing_values(df)
    if fig_missing:
        st.plotly_chart(fig_missing, use_container_width=True)

    # ── Numeric distributions ──
    if col_types["numeric"]:
        st.markdown("### 🔢 Numeric Distributions")
        num_cols_display = col_types["numeric"][:8]
        chart_cols = st.columns(2)
        for i, col in enumerate(num_cols_display):
            with chart_cols[i % 2]:
                fig = plot_numeric_distribution(df, col)
                st.plotly_chart(fig, use_container_width=True)

    # ── Correlation ──
    if len(col_types["numeric"]) >= 2:
        fig_corr = plot_correlation_matrix(df, col_types["numeric"][:12])
        if fig_corr:
            st.plotly_chart(fig_corr, use_container_width=True)

    # ── Categorical distributions ──
    if col_types["categorical"]:
        st.markdown("### 📁 Categorical Distributions")
        cat_cols_display = col_types["categorical"][:6]
        chart_cols = st.columns(2)
        for i, col in enumerate(cat_cols_display):
            with chart_cols[i % 2]:
                fig = plot_categorical_distribution(df, col)
                st.plotly_chart(fig, use_container_width=True)

    # ── Datetime distributions ──
    if col_types["datetime"]:
        st.markdown("### 📅 Temporal Distributions")
        for col in col_types["datetime"][:3]:
            fig = plot_datetime_distribution(df, col)
            st.plotly_chart(fig, use_container_width=True)

    # ── Text stats ──
    if col_types["text"]:
        st.markdown("### 📝 Text Field Statistics")
        for col in col_types["text"][:4]:
            series = df[col].fillna('').astype(str)
            tc1, tc2, tc3 = st.columns(3)
            tc1.metric(f"{col} — Avg Words", f"{series.str.split().str.len().mean():.0f}")
            tc2.metric(f"{col} — Avg Chars", f"{series.str.len().mean():.0f}")
            tc3.metric(f"{col} — Unique %", f"{(series.nunique() / max(len(series),1) * 100):.1f}%")
            fig = plot_text_stats(df, col)
            st.plotly_chart(fig, use_container_width=True)

    return col_types
