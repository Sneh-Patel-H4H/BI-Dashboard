import pandas as pd
from typing import Optional


def format_metric_value(value: float, kpi_name: str = "") -> str:
    """Format a metric value with appropriate scale, prefix, and precision."""
    if value is None:
        return "N/A"

    kpi_lower = kpi_name.lower()
    is_currency = any(
        w in kpi_lower
        for w in ["revenue", "sales", "cost", "spend", "value", "amount", "price", "arr", "mrr", "gmv", "profit", "income"]
    )
    is_percentage = any(
        w in kpi_lower
        for w in ["rate", "ratio", "%", "churn", "conversion", "ctr", "margin", "percent"]
    )

    if is_percentage:
        return f"{value:.1f}%"

    prefix = "$" if is_currency else ""
    abs_val = abs(value)

    if abs_val >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.2f}M"
    elif abs_val >= 1_000:
        return f"{prefix}{value / 1_000:.1f}K"
    else:
        if is_currency:
            return f"{prefix}{value:,.2f}"
        elif isinstance(value, float) and value == int(value):
            return f"{prefix}{int(value):,}"
        else:
            return f"{prefix}{value:,.2f}"


def format_change_pct(change_pct: Optional[float]) -> str:
    """Format a percentage change value with sign."""
    if change_pct is None:
        return ""
    sign = "+" if change_pct >= 0 else ""
    return f"{sign}{change_pct:.1f}%"


def format_date_range(date_series: pd.Series) -> str:
    """Format a human-readable date range from a date series."""
    non_null = date_series.dropna()
    if len(non_null) == 0:
        return "No dates"
    min_date = pd.Timestamp(non_null.min())
    max_date = pd.Timestamp(non_null.max())
    return f"{min_date.strftime('%b %d, %Y')} — {max_date.strftime('%b %d, %Y')}"


def format_large_number(value: float) -> str:
    """Format a number with K/M/B suffix, no currency prefix."""
    if value is None:
        return "N/A"
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif abs_val >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{value:,.0f}"
