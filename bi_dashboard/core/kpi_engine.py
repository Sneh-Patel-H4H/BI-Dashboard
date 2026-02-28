from typing import Any, Dict, List, Optional

import duckdb
import pandas as pd

from utils.formatting import format_metric_value


def compute_kpis(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    selected_kpis: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Dynamically compute every selected KPI against the real DataFrame using DuckDB.
    Returns {kpi_name: {value, formatted_value, change, change_pct, change_direction}}.
    No column names are hardcoded; everything is resolved from the schema.
    """
    results: Dict[str, Any] = {}
    date_column = _find_date_column(schema, df)

    con = duckdb.connect()
    con.register("data", df)

    for kpi in selected_kpis:
        try:
            results[kpi["name"]] = _compute_one(con, df, kpi, date_column)
        except Exception as e:  # noqa: BLE001
            results[kpi["name"]] = {
                "value": None,
                "formatted_value": "N/A",
                "change": None,
                "change_pct": None,
                "change_direction": None,
                "error": str(e),
            }

    con.close()
    return results


# ---------------------------------------------------------------------------
# Single-KPI computation
# ---------------------------------------------------------------------------

def _compute_one(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    kpi: Dict[str, Any],
    date_column: Optional[str],
) -> Dict[str, Any]:
    metric_col = _resolve_metric_col(kpi, df)
    if metric_col is None:
        return {"value": None, "formatted_value": "N/A", "change": None, "change_pct": None, "change_direction": None}

    agg = _detect_agg(kpi.get("formula", ""))
    safe = f'"{metric_col}"'
    value = con.execute(f"SELECT {agg}({safe}) FROM data").fetchone()[0]

    if value is None:
        return {"value": None, "formatted_value": "N/A", "change": None, "change_pct": None, "change_direction": None}

    result: Dict[str, Any] = {
        "value": float(value),
        "formatted_value": format_metric_value(float(value), kpi["name"]),
    }
    result.update(_period_change(con, df, metric_col, date_column, agg))
    return result


def _resolve_metric_col(kpi: Dict[str, Any], df: pd.DataFrame) -> Optional[str]:
    """Find the first numeric column named in columns_used, falling back to any numeric col."""
    for col in kpi.get("columns_used", []):
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            return col
    # Fallback
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            return col
    return None


def _detect_agg(formula: str) -> str:
    f = formula.lower()
    if any(w in f for w in ["average", "mean", "avg"]):
        return "AVG"
    if "count" in f:
        return "COUNT"
    if any(w in f for w in ["max", "maximum", "highest", "largest"]):
        return "MAX"
    if any(w in f for w in ["min", "minimum", "lowest", "smallest"]):
        return "MIN"
    return "SUM"


# ---------------------------------------------------------------------------
# Period-over-period change
# ---------------------------------------------------------------------------

def _period_change(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    metric_col: str,
    date_col: Optional[str],
    agg: str,
) -> Dict[str, Any]:
    empty = {"change": None, "change_pct": None, "change_direction": None}

    if date_col is None or date_col not in df.columns:
        return empty
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        return empty

    date_series = df[date_col].dropna()
    if len(date_series) < 4:
        return empty

    try:
        granularity = _detect_granularity(date_series)
        max_date = date_series.max()

        if granularity == "daily":
            current_start = max_date - pd.Timedelta(days=1)
            prior_start = max_date - pd.Timedelta(days=2)
            prior_end = current_start
        elif granularity == "weekly":
            current_start = max_date - pd.Timedelta(weeks=1)
            prior_start = max_date - pd.Timedelta(weeks=2)
            prior_end = current_start
        elif granularity == "monthly":
            current_start = max_date - pd.DateOffset(months=1)
            prior_start = max_date - pd.DateOffset(months=2)
            prior_end = current_start
        else:  # yearly
            current_start = max_date - pd.DateOffset(years=1)
            prior_start = max_date - pd.DateOffset(years=2)
            prior_end = current_start

        sm = f'"{metric_col}"'
        sd = f'"{date_col}"'

        current_val = con.execute(
            f"SELECT {agg}({sm}) FROM data WHERE {sd} >= '{current_start}'"
        ).fetchone()[0]

        prior_val = con.execute(
            f"SELECT {agg}({sm}) FROM data WHERE {sd} >= '{prior_start}' AND {sd} < '{prior_end}'"
        ).fetchone()[0]

        if current_val is not None and prior_val is not None and float(prior_val) != 0:
            change = float(current_val) - float(prior_val)
            change_pct = (change / abs(float(prior_val))) * 100
            return {
                "change": change,
                "change_pct": round(change_pct, 1),
                "change_direction": "up" if change >= 0 else "down",
            }
    except Exception:  # noqa: BLE001
        pass

    return empty


def _detect_granularity(date_series: pd.Series) -> str:
    """Infer daily / weekly / monthly / yearly from median gap between dates."""
    sorted_dates = date_series.sort_values()
    diffs = sorted_dates.diff().dropna()
    if len(diffs) == 0:
        return "monthly"
    median_diff = diffs.median()
    if median_diff <= pd.Timedelta(days=2):
        return "daily"
    if median_diff <= pd.Timedelta(days=9):
        return "weekly"
    if median_diff <= pd.Timedelta(days=35):
        return "monthly"
    return "yearly"


def _find_date_column(schema: Dict[str, Any], df: pd.DataFrame) -> Optional[str]:
    """Return the original_name of the first date-role column that exists in df."""
    for col in schema.get("columns", []):
        if col.get("role") == "date" and col["original_name"] in df.columns:
            return col["original_name"]
    return None
