import json
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PALETTE = ["#1565C0", "#27AE60", "#E74C3C", "#F39C12", "#9B59B6", "#1ABC9C", "#E67E22"]

_BASE = dict(
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(family="Inter, system-ui, sans-serif", color="#1A1A2E"),
    margin=dict(l=24, r=24, t=56, b=48),
    xaxis=dict(gridcolor="#EEEEEE", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#EEEEEE", showgrid=True, zeroline=False),
)


def _theme(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=15, color="#1A1A2E"), x=0, xanchor="left"), **_BASE)
    return fig


def generate_charts(df: pd.DataFrame, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate up to 4 charts. Returns list of {title, chart_type, plotly_json}."""
    col_meta = {c["original_name"]: c for c in schema.get("columns", [])}

    def label(col: str) -> str:
        return col_meta.get(col, {}).get("business_label", col)

    def role_cols(role: str) -> List[str]:
        return [c["original_name"] for c in schema.get("columns", [])
                if c.get("role") == role and c["original_name"] in df.columns]

    metrics = [c for c in role_cols("metric") if pd.api.types.is_numeric_dtype(df[c])]
    dates = [c for c in role_cols("date") if pd.api.types.is_datetime64_any_dtype(df[c])]
    dims = role_cols("dimension")

    charts = []
    used: set = set()

    # 1. Line — trend over time
    if dates and metrics and "line" not in used:
        fig = _line(df, dates[0], metrics[0], label)
        if fig:
            t = f"{label(metrics[0])} Over Time"
            charts.append(_pack(t, "line", _theme(fig, t)))
            used.add("line")

    # 2. Bar — breakdown by dimension
    if dims and metrics and "bar" not in used:
        m = metrics[1] if len(metrics) > 1 and "line" in used else metrics[0]
        fig = _bar(df, dims[0], m, label)
        if fig:
            t = f"{label(m)} by {label(dims[0])}"
            charts.append(_pack(t, "bar", _theme(fig, t)))
            used.add("bar")

    # 3. Scatter — two metrics correlation
    if len(metrics) >= 2 and "scatter" not in used:
        fig = _scatter(df, metrics[0], metrics[1], label)
        if fig:
            t = f"{label(metrics[0])} vs {label(metrics[1])}"
            charts.append(_pack(t, "scatter", _theme(fig, t)))
            used.add("scatter")

    # 4. Histogram — distribution
    if metrics and "histogram" not in used and len(charts) < 4:
        col = metrics[-1]
        fig = _histogram(df, col, label)
        if fig:
            t = f"Distribution of {label(col)}"
            charts.append(_pack(t, "histogram", _theme(fig, t)))
            used.add("histogram")

    # Fill remaining with additional line charts
    if len(charts) < 4 and dates and len(metrics) > 1:
        for m in metrics[1:]:
            if len(charts) >= 4:
                break
            fig = _line(df, dates[0], m, label)
            if fig:
                t = f"{label(m)} Over Time"
                charts.append(_pack(t, "line", _theme(fig, t)))

    return charts[:4]


def _pack(title: str, chart_type: str, fig: go.Figure) -> Dict[str, Any]:
    return {"title": title, "chart_type": chart_type, "plotly_json": fig.to_json()}


def _line(df, date_col, metric_col, lbl) -> Optional[go.Figure]:
    try:
        plot = df[[date_col, metric_col]].dropna().sort_values(date_col)
        if len(plot) < 2:
            return None
        plot = plot.groupby(date_col)[metric_col].sum().reset_index()
        fig = px.line(plot, x=date_col, y=metric_col,
                      labels={metric_col: lbl(metric_col), date_col: lbl(date_col)},
                      color_discrete_sequence=[PALETTE[0]])
        fig.update_traces(line_width=2.5, mode="lines+markers", marker_size=4)
        return fig
    except Exception:
        return None


def _bar(df, dim_col, metric_col, lbl) -> Optional[go.Figure]:
    try:
        plot = df[[dim_col, metric_col]].dropna()
        if len(plot) < 2:
            return None
        plot = plot.groupby(dim_col)[metric_col].sum().reset_index().nlargest(15, metric_col)
        fig = px.bar(plot, x=dim_col, y=metric_col,
                     labels={metric_col: lbl(metric_col), dim_col: lbl(dim_col)},
                     color_discrete_sequence=[PALETTE[0]])
        fig.update_layout(xaxis_tickangle=-35)
        return fig
    except Exception:
        return None


def _scatter(df, x_col, y_col, lbl) -> Optional[go.Figure]:
    try:
        plot = df[[x_col, y_col]].dropna()
        if len(plot) < 5:
            return None
        fig = px.scatter(plot, x=x_col, y=y_col,
                         labels={x_col: lbl(x_col), y_col: lbl(y_col)},
                         color_discrete_sequence=[PALETTE[0]], opacity=0.7)
        fig.update_traces(marker_size=7)
        return fig
    except Exception:
        return None


def _histogram(df, col, lbl) -> Optional[go.Figure]:
    try:
        if len(df[col].dropna()) < 5:
            return None
        fig = px.histogram(df, x=col, labels={col: lbl(col)},
                           color_discrete_sequence=[PALETTE[0]], nbins=30)
        fig.update_traces(marker_line_width=0.5, marker_line_color="white")
        return fig
    except Exception:
        return None
