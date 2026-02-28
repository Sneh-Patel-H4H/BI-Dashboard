from typing import Optional
import pandas as pd


def format_metric_value(value: float, kpi_name: str = "") -> str:
    if value is None:
        return "N/A"
    kpi_lower = kpi_name.lower()
    is_currency = any(w in kpi_lower for w in [
        "revenue", "sales", "cost", "spend", "value", "amount",
        "price", "arr", "mrr", "gmv", "profit", "income", "fee",
    ])
    is_percentage = any(w in kpi_lower for w in [
        "rate", "ratio", "%", "churn", "conversion", "ctr", "margin", "percent",
    ])
    if is_percentage:
        return f"{value:.1f}%"
    prefix = "$" if is_currency else ""
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{prefix}{value / 1_000_000_000:.2f}B"
    if abs_val >= 1_000_000:
        return f"{prefix}{value / 1_000_000:.2f}M"
    if abs_val >= 1_000:
        return f"{prefix}{value / 1_000:.1f}K"
    if is_currency:
        return f"{prefix}{value:,.2f}"
    if isinstance(value, float) and value == int(value):
        return f"{prefix}{int(value):,}"
    return f"{prefix}{value:,.2f}"


def format_change_pct(change_pct: Optional[float]) -> str:
    if change_pct is None:
        return ""
    sign = "+" if change_pct >= 0 else ""
    return f"{sign}{change_pct:.1f}%"


def format_date_range(date_series: pd.Series) -> str:
    non_null = date_series.dropna()
    if len(non_null) == 0:
        return ""
    min_d = pd.Timestamp(non_null.min()).strftime("%b %d, %Y")
    max_d = pd.Timestamp(non_null.max()).strftime("%b %d, %Y")
    return f"{min_d} – {max_d}"
