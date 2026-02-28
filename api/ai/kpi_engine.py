from typing import Any, Dict, List, Optional

import pandas as pd

from utils.formatting import format_metric_value


def compute_kpis(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    selected_kpis: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute all selected KPIs. Returns {name: {value, formatted_value, change_pct, change_direction}}."""
    date_col = _find_date_col(schema, df)
    results = {}
    for kpi in selected_kpis:
        try:
            results[kpi["name"]] = _compute_one(df, kpi, date_col)
        except Exception:  # noqa: BLE001
            results[kpi["name"]] = {"value": None, "formatted_value": "N/A",
                                    "change_pct": None, "change_direction": None}
    return results


def _compute_one(df: pd.DataFrame, kpi: Dict[str, Any], date_col: Optional[str]) -> Dict[str, Any]:
    col = _resolve_metric_col(kpi, df)
    if col is None:
        return {"value": None, "formatted_value": "N/A", "change_pct": None, "change_direction": None}

    agg = _detect_agg(kpi.get("formula", ""))
    series = df[col].dropna()
    value = float(_agg_series(series, agg))

    result: Dict[str, Any] = {
        "value": value,
        "formatted_value": format_metric_value(value, kpi["name"]),
    }
    result.update(_period_change(df, col, date_col, agg))
    return result


def _resolve_metric_col(kpi: Dict[str, Any], df: pd.DataFrame) -> Optional[str]:
    for c in kpi.get("columns_used", []):
        if c in df.columns and pd.api.types.is_numeric_dtype(df[c]):
            return c
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None


def _detect_agg(formula: str) -> str:
    f = formula.lower()
    if any(w in f for w in ["average", "mean", "avg"]):
        return "mean"
    if "count" in f:
        return "count"
    if any(w in f for w in ["max", "maximum", "highest"]):
        return "max"
    if any(w in f for w in ["min", "minimum", "lowest"]):
        return "min"
    return "sum"


def _agg_series(series: pd.Series, agg: str) -> float:
    if agg == "mean":
        return series.mean()
    if agg == "count":
        return float(len(series))
    if agg == "max":
        return series.max()
    if agg == "min":
        return series.min()
    return series.sum()


def _period_change(
    df: pd.DataFrame, metric_col: str, date_col: Optional[str], agg: str
) -> Dict[str, Any]:
    empty = {"change_pct": None, "change_direction": None}
    if not date_col or date_col not in df.columns:
        return empty
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        return empty
    dates = df[date_col].dropna()
    if len(dates) < 4:
        return empty
    try:
        gran = _granularity(dates)
        max_d = dates.max()
        offsets = {
            "daily": (pd.Timedelta(days=1), pd.Timedelta(days=2)),
            "weekly": (pd.Timedelta(weeks=1), pd.Timedelta(weeks=2)),
            "monthly": (pd.DateOffset(months=1), pd.DateOffset(months=2)),
            "yearly": (pd.DateOffset(years=1), pd.DateOffset(years=2)),
        }
        cur_off, pri_off = offsets[gran]
        cur_start = max_d - cur_off
        pri_start = max_d - pri_off
        cur_val = _agg_series(df.loc[df[date_col] >= cur_start, metric_col].dropna(), agg)
        pri_val = _agg_series(df.loc[(df[date_col] >= pri_start) & (df[date_col] < cur_start), metric_col].dropna(), agg)
        if pri_val != 0:
            pct = ((cur_val - pri_val) / abs(pri_val)) * 100
            return {"change_pct": round(pct, 1), "change_direction": "up" if pct >= 0 else "down"}
    except Exception:  # noqa: BLE001
        pass
    return empty


def _granularity(dates: pd.Series) -> str:
    med = dates.sort_values().diff().dropna().median()
    if med <= pd.Timedelta(days=2):
        return "daily"
    if med <= pd.Timedelta(days=9):
        return "weekly"
    if med <= pd.Timedelta(days=35):
        return "monthly"
    return "yearly"


def _find_date_col(schema: Dict[str, Any], df: pd.DataFrame) -> Optional[str]:
    for c in schema.get("columns", []):
        if c.get("role") == "date" and c["original_name"] in df.columns:
            return c["original_name"]
    return None
