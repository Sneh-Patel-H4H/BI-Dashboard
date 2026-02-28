from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------

PALETTE = [
    "#2E75B6", "#27AE60", "#E74C3C", "#F39C12",
    "#9B59B6", "#1ABC9C", "#E67E22", "#34495E",
]

_LAYOUT_BASE = dict(
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color="#2C3E50"),
    margin=dict(l=24, r=24, t=56, b=40),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E9ECEF", borderwidth=1),
    xaxis=dict(gridcolor="#EEEEEE", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#EEEEEE", showgrid=True, zeroline=False),
)


def _theme(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color="#2C3E50"),
            x=0.0,
            xanchor="left",
        ),
        **_LAYOUT_BASE,
    )
    return fig


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_dashboard_charts(
    df: pd.DataFrame,
    schema: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate up to 4 Plotly charts for the dashboard.
    Strategy: maximise chart-type variety first (line → bar → scatter → histogram),
    then fill remaining slots with additional date+metric combinations ranked by
    KPI priority.
    Returns list of {title, fig, chart_type}.
    """
    col_meta = {c["original_name"]: c for c in schema.get("columns", [])}

    def _label(col: str) -> str:
        return col_meta.get(col, {}).get("business_label", col)

    def _role_cols(role: str) -> List[str]:
        return [
            c["original_name"]
            for c in schema.get("columns", [])
            if c.get("role") == role and c["original_name"] in df.columns
        ]

    metric_cols = [c for c in _role_cols("metric") if pd.api.types.is_numeric_dtype(df[c])]
    date_cols = [c for c in _role_cols("date") if pd.api.types.is_datetime64_any_dtype(df[c])]
    dim_cols = _role_cols("dimension")

    charts: List[Dict[str, Any]] = []
    used_types: set[str] = set()

    # 1. Line — date + first metric
    if date_cols and metric_cols and "line" not in used_types:
        fig = _line(df, date_cols[0], metric_cols[0], _label)
        if fig:
            title = f"{_label(metric_cols[0])} Over Time"
            charts.append({"title": title, "fig": _theme(fig, title), "chart_type": "line"})
            used_types.add("line")

    # 2. Bar — first dimension + metric (different from line's metric if possible)
    if dim_cols and metric_cols and "bar" not in used_types:
        bar_metric = metric_cols[1] if len(metric_cols) > 1 and "line" in used_types else metric_cols[0]
        fig = _bar(df, dim_cols[0], bar_metric, _label)
        if fig:
            title = f"{_label(bar_metric)} by {_label(dim_cols[0])}"
            charts.append({"title": title, "fig": _theme(fig, title), "chart_type": "bar"})
            used_types.add("bar")

    # 3. Scatter — two metrics
    if len(metric_cols) >= 2 and "scatter" not in used_types:
        fig = _scatter(df, metric_cols[0], metric_cols[1], _label)
        if fig:
            title = f"{_label(metric_cols[0])} vs {_label(metric_cols[1])}"
            charts.append({"title": title, "fig": _theme(fig, title), "chart_type": "scatter"})
            used_types.add("scatter")

    # 4. Histogram — last distinct metric
    if metric_cols and "histogram" not in used_types and len(charts) < 4:
        hist_col = metric_cols[-1]
        fig = _histogram(df, hist_col, _label)
        if fig:
            title = f"Distribution of {_label(hist_col)}"
            charts.append({"title": title, "fig": _theme(fig, title), "chart_type": "histogram"})
            used_types.add("histogram")

    # 5. Fill remaining slots with additional line charts (more metrics over same date)
    if len(charts) < 4 and date_cols and len(metric_cols) > 1:
        for mc in metric_cols[1:]:
            if len(charts) >= 4:
                break
            fig = _line(df, date_cols[0], mc, _label)
            if fig:
                title = f"{_label(mc)} Over Time"
                charts.append({"title": title, "fig": _theme(fig, title), "chart_type": "line"})

    return charts[:4]


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def _line(
    df: pd.DataFrame, date_col: str, metric_col: str, label_fn
) -> Optional[go.Figure]:
    try:
        plot = df[[date_col, metric_col]].dropna()
        if len(plot) < 2:
            return None
        plot = plot.sort_values(date_col)
        plot = plot.groupby(date_col)[metric_col].sum().reset_index()
        fig = px.line(
            plot, x=date_col, y=metric_col,
            labels={metric_col: label_fn(metric_col), date_col: label_fn(date_col)},
            color_discrete_sequence=[PALETTE[0]],
        )
        fig.update_traces(line_width=2.5, mode="lines+markers", marker_size=4)
        return fig
    except Exception:
        return None


def _bar(
    df: pd.DataFrame, dim_col: str, metric_col: str, label_fn
) -> Optional[go.Figure]:
    try:
        plot = df[[dim_col, metric_col]].dropna()
        if len(plot) < 2:
            return None
        plot = plot.groupby(dim_col)[metric_col].sum().reset_index()
        plot = plot.nlargest(15, metric_col)
        fig = px.bar(
            plot, x=dim_col, y=metric_col,
            labels={metric_col: label_fn(metric_col), dim_col: label_fn(dim_col)},
            color_discrete_sequence=[PALETTE[0]],
        )
        fig.update_layout(xaxis_tickangle=-35)
        return fig
    except Exception:
        return None


def _scatter(
    df: pd.DataFrame, x_col: str, y_col: str, label_fn
) -> Optional[go.Figure]:
    try:
        plot = df[[x_col, y_col]].dropna()
        if len(plot) < 5:
            return None
        fig = px.scatter(
            plot, x=x_col, y=y_col,
            labels={x_col: label_fn(x_col), y_col: label_fn(y_col)},
            color_discrete_sequence=[PALETTE[0]],
            opacity=0.7,
        )
        fig.update_traces(marker_size=7)
        return fig
    except Exception:
        return None


def _histogram(
    df: pd.DataFrame, col: str, label_fn
) -> Optional[go.Figure]:
    try:
        series = df[col].dropna()
        if len(series) < 5:
            return None
        fig = px.histogram(
            df, x=col,
            labels={col: label_fn(col)},
            color_discrete_sequence=[PALETTE[0]],
            nbins=30,
        )
        fig.update_traces(marker_line_width=0.5, marker_line_color="white")
        return fig
    except Exception:
        return None
