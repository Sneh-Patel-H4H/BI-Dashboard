import io
import re
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from dateutil.parser import parse as dateutil_parse

# All representations that should be treated as missing
NULL_REPRESENTATIONS = {
    "", "N/A", "n/a", "NA", "-", "none", "None",
    "null", "NULL", "NaN", "nan", "#N/A", "#NA", "na", "N/a",
}

# Pattern to strip currency/formatting from numeric strings
CURRENCY_PATTERN = re.compile(r"[$£€¥₹,\s]")


# ---------------------------------------------------------------------------
# Header detection
# ---------------------------------------------------------------------------

def _is_numeric_string(val: str) -> bool:
    """Return True if val looks like a pure number (after stripping formatting)."""
    try:
        float(CURRENCY_PATTERN.sub("", val))
        return True
    except (ValueError, TypeError):
        return False


def detect_header_row(raw_df: pd.DataFrame) -> int:
    """
    Scan the first 10 rows and return the 0-based index of the most likely
    header row (the one with the most non-null, non-numeric string values).
    Ties are broken by taking the topmost row.
    """
    sample = raw_df.head(10)
    best_row = 0
    best_score = -1

    for i in sample.index:
        score = 0
        for val in sample.loc[i]:
            if pd.isna(val):
                continue
            s = str(val).strip()
            if s and not _is_numeric_string(s):
                score += 1
        if score > best_score:
            best_score = score
            best_row = i

    return int(best_row)


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def normalize_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Replace all known null representations with NaN."""
    return df.replace(list(NULL_REPRESENTATIONS), np.nan)


def coerce_numeric_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    For object-typed columns that look numeric (>50 % convert successfully),
    strip currency symbols and coerce to float.
    Returns (cleaned_df, list_of_coerced_column_names).
    """
    coerced: List[str] = []
    for col in df.columns:
        if df[col].dtype != object:
            continue
        cleaned = df[col].astype(str).apply(
            lambda x: CURRENCY_PATTERN.sub("", x) if pd.notna(x) else x
        )
        numeric = pd.to_numeric(cleaned, errors="coerce")
        non_null_count = df[col].notna().sum()
        if non_null_count > 0 and (numeric.notna().sum() / non_null_count) > 0.5:
            df = df.copy()
            df[col] = numeric
            coerced.append(col)
    return df, coerced


def fix_duplicate_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Rename duplicate column names with _2, _3 … suffix."""
    seen: Dict[str, int] = {}
    new_cols: List[str] = []
    renamed: List[str] = []

    for col in df.columns:
        col_str = str(col).strip() if col is not None else "column"
        if col_str in seen:
            seen[col_str] += 1
            new_name = f"{col_str}_{seen[col_str]}"
            new_cols.append(new_name)
            renamed.append(new_name)
        else:
            seen[col_str] = 1
            new_cols.append(col_str)

    df = df.copy()
    df.columns = new_cols
    return df, renamed


def _parse_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attempt to parse object columns that look like dates.
    A column is converted if >70 % of its non-null sample values parse as dates.
    """
    for col in df.columns:
        if df[col].dtype != object:
            continue
        sample = df[col].dropna().head(10)
        if len(sample) == 0:
            continue
        date_count = 0
        for val in sample:
            try:
                dateutil_parse(str(val))
                date_count += 1
            except Exception:
                pass
        if len(sample) > 0 and (date_count / len(sample)) > 0.7:
            try:
                df = df.copy()
                df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            except Exception:
                pass
    return df


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_csv(file_content: bytes, filename: str) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load a CSV file with automatic header detection, null normalisation,
    duplicate column renaming, numeric coercion, and date parsing.
    Returns (DataFrame, list_of_quality_notes).
    """
    quality_notes: List[str] = []

    # First pass: raw read to detect header row
    try:
        raw = pd.read_csv(
            io.BytesIO(file_content), header=None, dtype=str, nrows=10, encoding_errors="replace"
        )
    except Exception as e:
        raise ValueError(f"Could not read CSV file: {e}") from e

    header_row = detect_header_row(raw)
    if header_row > 0:
        quality_notes.append(
            f"Header detected on row {header_row + 1} (not row 1) — data adjusted automatically."
        )

    # Second pass: proper read with correct header
    try:
        df = pd.read_csv(
            io.BytesIO(file_content),
            header=header_row,
            dtype=str,
            na_values=list(NULL_REPRESENTATIONS),
            keep_default_na=True,
            encoding_errors="replace",
        )
    except Exception as e:
        raise ValueError(f"Could not parse CSV file: {e}") from e

    df = normalize_nulls(df)
    df, renamed = fix_duplicate_columns(df)
    if renamed:
        quality_notes.append(f"Duplicate column names renamed: {', '.join(renamed)}")

    df, _ = coerce_numeric_columns(df)
    df = _parse_date_columns(df)
    return df, quality_notes


def get_excel_sheets(file_content: bytes) -> List[str]:
    """Return a list of sheet names for an Excel file."""
    try:
        xl = pd.ExcelFile(io.BytesIO(file_content))
        return xl.sheet_names
    except Exception as e:
        raise ValueError(f"Could not read Excel file: {e}") from e


def load_excel(
    file_content: bytes, sheet_name: Union[str, int]
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load a single sheet from an Excel file with the same cleaning pipeline as CSV.
    Uses openpyxl with data_only=True so formulas resolve to their computed values.
    Returns (DataFrame, list_of_quality_notes).
    """
    quality_notes: List[str] = []

    # Raw read (no header) to detect header row
    try:
        raw = pd.read_excel(
            io.BytesIO(file_content),
            sheet_name=sheet_name,
            header=None,
            dtype=str,
            nrows=10,
            engine="openpyxl",
        )
    except Exception as e:
        raise ValueError(f"Could not read Excel sheet '{sheet_name}': {e}") from e

    header_row = detect_header_row(raw)
    if header_row > 0:
        quality_notes.append(
            f"Header detected on row {header_row + 1} — data adjusted automatically."
        )

    # Full read with correct header
    try:
        df = pd.read_excel(
            io.BytesIO(file_content),
            sheet_name=sheet_name,
            header=header_row,
            dtype=str,
            engine="openpyxl",
        )
    except Exception as e:
        raise ValueError(f"Could not parse Excel sheet '{sheet_name}': {e}") from e

    df = normalize_nulls(df)
    df, renamed = fix_duplicate_columns(df)
    if renamed:
        quality_notes.append(f"Duplicate column names renamed: {', '.join(renamed)}")

    df, _ = coerce_numeric_columns(df)
    df = _parse_date_columns(df)
    return df, quality_notes


# ---------------------------------------------------------------------------
# Data quality helpers
# ---------------------------------------------------------------------------

def get_data_quality_notes(df: pd.DataFrame) -> List[str]:
    """
    Generate data quality notes suitable for display on the discovery page.
    Reports columns with >10 % null rate and any duplicate rows.
    """
    notes: List[str] = []

    null_rates = {col: df[col].isna().mean() for col in df.columns}
    high_null = sorted(
        [(col, rate) for col, rate in null_rates.items() if rate > 0.1],
        key=lambda x: -x[1],
    )[:5]
    for col, rate in high_null:
        notes.append(f"{int(rate * 100)}% missing values in '{col}'")

    dup_count = df.duplicated().sum()
    if dup_count > 0:
        notes.append(f"{dup_count:,} duplicate rows detected")

    return notes
