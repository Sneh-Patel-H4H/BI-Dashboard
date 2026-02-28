import json
from typing import Any, Dict, List

import pandas as pd


def profile_column(series: pd.Series) -> Dict[str, Any]:
    non_null = series.dropna()
    p: Dict[str, Any] = {
        "name": str(series.name),
        "dtype": str(series.dtype),
        "total_count": int(len(series)),
        "null_count": int(series.isna().sum()),
        "null_rate": round(float(series.isna().mean()), 4),
        "unique_count": int(series.nunique()),
        "sample_values": [str(v) for v in non_null.head(5).tolist()],
    }
    if pd.api.types.is_numeric_dtype(series):
        p["inferred_type"] = "numeric"
        if len(non_null):
            p["min"] = float(non_null.min())
            p["max"] = float(non_null.max())
            p["mean"] = round(float(non_null.mean()), 4)
    elif pd.api.types.is_datetime64_any_dtype(series):
        p["inferred_type"] = "datetime"
        if len(non_null):
            p["min_date"] = str(non_null.min())
            p["max_date"] = str(non_null.max())
            p["date_range_days"] = int((non_null.max() - non_null.min()).days)
    else:
        p["inferred_type"] = "text"
        if series.nunique() <= 50 and len(series) > 2:
            p["is_categorical"] = True
            p["top_values"] = [str(v) for v in series.value_counts().head(5).index.tolist()]
        else:
            p["is_categorical"] = False
    return p


def profile_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    profiles = []
    for col in df.columns:
        try:
            profiles.append(profile_column(df[col]))
        except Exception as e:
            profiles.append({"name": str(col), "dtype": "unknown", "error": str(e)})
    return profiles


def to_json(profiles: List[Dict[str, Any]]) -> str:
    return json.dumps(profiles, indent=2, default=str)
