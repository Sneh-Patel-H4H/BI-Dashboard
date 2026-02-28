import json
from typing import Any, Dict, List

import pandas as pd


def profile_column(series: pd.Series) -> Dict[str, Any]:
    """
    Build a rich profile for a single DataFrame column.
    Includes dtype, null statistics, unique count, sample values,
    and type-specific min/max/range details.
    """
    col_name = str(series.name)
    non_null = series.dropna()

    profile: Dict[str, Any] = {
        "name": col_name,
        "dtype": str(series.dtype),
        "total_count": int(len(series)),
        "null_count": int(series.isna().sum()),
        "null_rate": round(float(series.isna().mean()), 4),
        "unique_count": int(series.nunique()),
        "sample_values": [str(v) for v in non_null.head(5).tolist()],
    }

    if pd.api.types.is_numeric_dtype(series):
        profile["inferred_type"] = "numeric"
        if len(non_null) > 0:
            profile["min"] = float(non_null.min())
            profile["max"] = float(non_null.max())
            profile["mean"] = round(float(non_null.mean()), 4)

    elif pd.api.types.is_datetime64_any_dtype(series):
        profile["inferred_type"] = "datetime"
        if len(non_null) > 0:
            profile["min_date"] = str(non_null.min())
            profile["max_date"] = str(non_null.max())
            profile["date_range_days"] = int((non_null.max() - non_null.min()).days)

    else:
        profile["inferred_type"] = "text"
        if series.nunique() <= 50 and len(series) > 2:
            profile["is_categorical"] = True
            top = series.value_counts().head(5)
            profile["top_values"] = [str(v) for v in top.index.tolist()]
            profile["top_value_counts"] = top.tolist()
        else:
            profile["is_categorical"] = False

    return profile


def profile_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Profile every column in the DataFrame. Errors per column are captured gracefully."""
    profiles: List[Dict[str, Any]] = []
    for col in df.columns:
        try:
            profiles.append(profile_column(df[col]))
        except Exception as e:  # noqa: BLE001
            profiles.append({"name": str(col), "dtype": "unknown", "error": str(e)})
    return profiles


def profiles_to_json(profiles: List[Dict[str, Any]]) -> str:
    """Serialise column profiles to a compact JSON string for the Claude prompt."""
    return json.dumps(profiles, indent=2, default=str)
