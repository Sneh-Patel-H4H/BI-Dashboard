import io
import re
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from dateutil.parser import parse as dateutil_parse

NULL_VALUES = {
    "", "N/A", "n/a", "NA", "-", "none", "None",
    "null", "NULL", "NaN", "nan", "#N/A", "#NA", "na",
}
CURRENCY_RE = re.compile(r"[$£€¥₹,\s]")


def _is_numeric_string(val: str) -> bool:
    try:
        float(CURRENCY_RE.sub("", val))
        return True
    except (ValueError, TypeError):
        return False


def detect_header_row(raw: pd.DataFrame) -> int:
    """Return the 0-based row index most likely to be the header."""
    best_row, best_score = 0, -1
    for i in raw.index:
        score = sum(
            1 for v in raw.loc[i]
            if not pd.isna(v) and str(v).strip() and not _is_numeric_string(str(v).strip())
        )
        if score > best_score:
            best_score, best_row = score, int(i)
    return best_row


def normalize_nulls(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace(list(NULL_VALUES), np.nan)


def coerce_numerics(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype != object:
            continue
        cleaned = df[col].astype(str).map(lambda x: CURRENCY_RE.sub("", x))
        numeric = pd.to_numeric(cleaned, errors="coerce")
        non_null = df[col].notna().sum()
        if non_null > 0 and (numeric.notna().sum() / non_null) > 0.5:
            df = df.copy()
            df[col] = numeric
    return df


def fix_duplicate_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    seen: Dict[str, int] = {}
    new_cols, renamed = [], []
    for col in df.columns:
        s = str(col).strip() if col is not None else "column"
        if s in seen:
            seen[s] += 1
            new = f"{s}_{seen[s]}"
            new_cols.append(new)
            renamed.append(new)
        else:
            seen[s] = 1
            new_cols.append(s)
    df = df.copy()
    df.columns = new_cols
    return df, renamed


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype != object:
            continue
        sample = df[col].dropna().head(10)
        if len(sample) == 0:
            continue
        hits = sum(1 for v in sample if _looks_like_date(str(v)))
        if len(sample) > 0 and hits / len(sample) > 0.7:
            try:
                df = df.copy()
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            except Exception:
                pass
    return df


def _looks_like_date(val: str) -> bool:
    try:
        dateutil_parse(val)
        return True
    except Exception:
        return False


def load_csv(content: bytes) -> Tuple[pd.DataFrame, List[str]]:
    notes: List[str] = []
    try:
        raw = pd.read_csv(io.BytesIO(content), header=None, dtype=str, nrows=10, encoding_errors="replace")
    except Exception as e:
        raise ValueError(f"Could not read CSV file: {e}") from e

    hr = detect_header_row(raw)
    if hr > 0:
        notes.append(f"Header detected on row {hr + 1} — adjusted automatically.")

    df = pd.read_csv(
        io.BytesIO(content), header=hr, dtype=str,
        na_values=list(NULL_VALUES), keep_default_na=True, encoding_errors="replace",
    )
    df = normalize_nulls(df)
    df, renamed = fix_duplicate_columns(df)
    if renamed:
        notes.append(f"Duplicate columns renamed: {', '.join(renamed)}")
    df = coerce_numerics(df)
    df = parse_dates(df)
    return df, notes


def get_excel_sheets(content: bytes) -> List[str]:
    try:
        return pd.ExcelFile(io.BytesIO(content)).sheet_names
    except Exception as e:
        raise ValueError(f"Could not read Excel file: {e}") from e


def load_excel(content: bytes, sheet: Union[str, int]) -> Tuple[pd.DataFrame, List[str]]:
    notes: List[str] = []
    try:
        raw = pd.read_excel(io.BytesIO(content), sheet_name=sheet, header=None, dtype=str, nrows=10, engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Could not read sheet '{sheet}': {e}") from e

    hr = detect_header_row(raw)
    if hr > 0:
        notes.append(f"Header detected on row {hr + 1} — adjusted automatically.")

    df = pd.read_excel(io.BytesIO(content), sheet_name=sheet, header=hr, dtype=str, engine="openpyxl")
    df = normalize_nulls(df)
    df, renamed = fix_duplicate_columns(df)
    if renamed:
        notes.append(f"Duplicate columns renamed: {', '.join(renamed)}")
    df = coerce_numerics(df)
    df = parse_dates(df)
    return df, notes


def quality_notes(df: pd.DataFrame) -> List[str]:
    notes = []
    high_null = sorted(
        [(c, df[c].isna().mean()) for c in df.columns if df[c].isna().mean() > 0.1],
        key=lambda x: -x[1],
    )[:5]
    for col, rate in high_null:
        notes.append(f"{int(rate * 100)}% missing values in '{col}'")
    dups = df.duplicated().sum()
    if dups:
        notes.append(f"{dups:,} duplicate rows detected")
    return notes
