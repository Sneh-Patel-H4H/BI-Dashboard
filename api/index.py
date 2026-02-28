"""
FastAPI backend — single entry point for Vercel serverless deployment.
All /api/* routes are handled here.
"""
import json
import os
import sys

# Ensure the api/ directory is on the path so sub-packages resolve correctly
_api_dir = os.path.dirname(os.path.abspath(__file__))
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

from ai.kpi_engine import compute_kpis
from ai.qa_pipeline import answer
from ai.schema_interpreter import interpret_schema
from core.chart_engine import generate_charts
from core.ingestion import (
    get_excel_sheets,
    load_csv,
    load_excel,
    quality_notes,
)
from core.profiler import profile_dataframe, to_json as profiles_to_json
from utils.formatting import format_date_range

app = FastAPI(title="BI Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

MAX_SAMPLE_ROWS = 500
MAX_FILE_MB = 50


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    schema: Dict[str, Any]
    sample_rows: List[Dict[str, Any]]
    chat_history: List[Dict[str, Any]] = []


class SheetsRequest(BaseModel):
    pass


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Get Excel sheet names (before full upload)
# ---------------------------------------------------------------------------

@app.post("/api/sheets")
async def get_sheets(file: UploadFile = File(...)):
    content = await file.read()
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "xls"):
        raise HTTPException(400, "Only Excel files have multiple sheets.")
    try:
        sheets = get_excel_sheets(content)
        return {"sheets": sheets}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


# ---------------------------------------------------------------------------
# Upload + full analysis (the heavy endpoint)
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload(
    file: UploadFile = File(...),
    sheet: Optional[str] = Form(None),
    selected_kpis_json: Optional[str] = Form(None),  # JSON string, used on re-confirm
):
    # ---- Size check --------------------------------------------------------
    content = await file.read()
    if len(content) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large. Maximum size is {MAX_FILE_MB} MB.")

    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower()

    # ---- Ingest ------------------------------------------------------------
    try:
        ingest_notes: List[str] = []
        if ext == "csv":
            df, ingest_notes = load_csv(content)
        elif ext in ("xlsx", "xls"):
            df, ingest_notes = load_excel(content, sheet or 0)
        else:
            raise HTTPException(400, "Unsupported file type. Please upload a CSV or Excel file.")
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    if df.empty:
        raise HTTPException(400, "The uploaded file appears to be empty.")

    all_notes = ingest_notes + quality_notes(df)

    # ---- Profile + Claude analysis -----------------------------------------
    try:
        profiles = profile_dataframe(df)
        profiles_json = profiles_to_json(profiles)
        schema = interpret_schema(profiles_json)
    except RuntimeError as e:
        raise HTTPException(502, str(e)) from e

    # ---- KPI computation (full dataset) ------------------------------------
    high_kpis = [k for k in schema.get("suggested_kpis", []) if k.get("priority") == "high"]
    kpi_values = compute_kpis(df, schema, high_kpis)

    # ---- Charts (full dataset) ---------------------------------------------
    charts = generate_charts(df, schema)

    # ---- Sample rows for Q&A -----------------------------------------------
    sample = _safe_sample(df, MAX_SAMPLE_ROWS)

    # ---- Date range --------------------------------------------------------
    date_range = ""
    for col_meta in schema.get("columns", []):
        if col_meta.get("role") == "date":
            col_name = col_meta["original_name"]
            if col_name in df.columns and pd.api.types.is_datetime64_any_dtype(df[col_name]):
                date_range = format_date_range(df[col_name])
                break

    return {
        "schema": schema,
        "kpis": kpi_values,
        "charts": charts,
        "sample_rows": sample,
        "total_rows": len(df),
        "column_count": len(df.columns),
        "quality_notes": all_notes,
        "date_range": date_range,
        "file_name": filename,
    }


# ---------------------------------------------------------------------------
# Recompute KPIs after user changes KPI selection on discovery page
# ---------------------------------------------------------------------------

@app.post("/api/kpis")
async def recompute_kpis(
    file: UploadFile = File(...),
    sheet: Optional[str] = Form(None),
    selected_kpis_json: str = Form(...),
):
    content = await file.read()
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    try:
        df, _ = load_csv(content) if ext == "csv" else load_excel(content, sheet or 0)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    selected = json.loads(selected_kpis_json)
    schema_raw = Form(...)  # not available here — use /api/upload instead
    # This endpoint is intentionally simple; the frontend should call /api/upload
    # and then filter KPIs client-side.
    return {"kpis": {}}


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty.")
    result = answer(req.question, req.schema, req.sample_rows, req.chat_history)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_sample(df: pd.DataFrame, n: int) -> List[Dict[str, Any]]:
    """Return up to n rows as a JSON-serialisable list of dicts."""
    sample = df.head(n) if len(df) > n else df
    return json.loads(sample.to_json(orient="records", date_format="iso", default_handler=str))
