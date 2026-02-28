from typing import List, Optional

import pandas as pd
import streamlit as st

from ai.schema_interpreter import interpret_schema
from core.ingestion import (
    get_data_quality_notes,
    get_excel_sheets,
    load_csv,
    load_excel,
)
from core.profiler import profile_dataframe, profiles_to_json


def render() -> None:
    st.title("Upload Your Data")
    st.markdown(
        "Upload a CSV or Excel file and I'll analyse it instantly — "
        "detecting your sector, KPIs, and building your dashboard automatically."
    )

    uploaded_file = st.file_uploader(
        "Drop your file here",
        type=["csv", "xlsx", "xls"],
        help="Supports CSV and Excel files. Headers don't need to be on row 1.",
        label_visibility="collapsed",
    )

    if uploaded_file is None:
        _show_tips()
        return

    file_bytes = uploaded_file.read()
    file_name: str = uploaded_file.name
    file_ext = file_name.rsplit(".", 1)[-1].lower()

    # ---- Excel: sheet selector ------------------------------------------------
    selected_sheets: Optional[List[str]] = None
    if file_ext in ("xlsx", "xls"):
        try:
            sheets = get_excel_sheets(file_bytes)
        except ValueError as e:
            st.error(str(e))
            return

        if len(sheets) > 1:
            selected_sheets = st.multiselect(
                "This Excel file has multiple sheets. Select the sheets to analyse:",
                sheets,
                default=[sheets[0]],
            )
            if not selected_sheets:
                st.info("Please select at least one sheet to continue.")
                return
        else:
            selected_sheets = sheets

    # ---- Analyse button -------------------------------------------------------
    if st.button("🔍 Analyse My Data", type="primary"):
        _process_file(file_bytes, file_name, file_ext, selected_sheets)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _process_file(
    file_bytes: bytes,
    file_name: str,
    file_ext: str,
    selected_sheets: Optional[List[str]],
) -> None:
    progress = st.progress(0, text="Reading your file…")

    try:
        # ---- Load -------------------------------------------------------
        if file_ext == "csv":
            df, quality_notes = load_csv(file_bytes, file_name)
        else:
            if len(selected_sheets) == 1:
                df, quality_notes = load_excel(file_bytes, selected_sheets[0])
            else:
                dfs, all_notes = [], []
                for sheet in selected_sheets:
                    sdf, snotes = load_excel(file_bytes, sheet)
                    sdf["_sheet"] = sheet
                    dfs.append(sdf)
                    all_notes.extend(snotes)
                df = pd.concat(dfs, ignore_index=True)
                quality_notes = all_notes

        if df.empty:
            st.error("The uploaded file appears to be empty. Please check your file and try again.")
            return

        progress.progress(30, text="Profiling your columns…")

        # ---- Profile ----------------------------------------------------
        profiles = profile_dataframe(df)
        profiles_json = profiles_to_json(profiles)
        dq_notes = get_data_quality_notes(df)
        all_quality_notes = quality_notes + dq_notes

        progress.progress(55, text="Running AI analysis on your data…")

        # ---- Schema interpretation --------------------------------------
        try:
            schema = interpret_schema(profiles_json)
        except RuntimeError as e:
            st.error(str(e))
            return

        progress.progress(100, text="Analysis complete!")

        # ---- Persist to session state -----------------------------------
        st.session_state.raw_df = df
        st.session_state.schema = schema
        st.session_state.sector = schema.get("sector")
        st.session_state.sector_confidence = schema.get("sector_confidence")
        st.session_state.org_type = schema.get("organization_type")
        st.session_state.org_confidence = schema.get("org_confidence")
        st.session_state.dataset_description = schema.get("dataset_description")
        st.session_state.file_name = file_name
        st.session_state.upload_complete = True
        st.session_state.data_quality_notes = all_quality_notes
        # Pre-select all high-priority KPIs
        st.session_state.selected_kpis = [
            kpi
            for kpi in schema.get("suggested_kpis", [])
            if kpi.get("priority") == "high"
        ]

        st.rerun()

    except ValueError as e:
        st.error(
            f"Could not read your file: {e}. "
            "Please make sure it is a valid CSV or Excel file."
        )
    except Exception:  # noqa: BLE001
        st.error(
            "Something went wrong while processing your file. "
            "Please check the file and try again."
        )


def _show_tips() -> None:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "**📋 CSV Files**  \n"
            "Comma-separated values work great. "
            "Headers can be anywhere in the first 10 rows."
        )
    with c2:
        st.markdown(
            "**📊 Excel Files**  \n"
            "XLSX and XLS supported. Merged cells and multiple sheets are handled automatically."
        )
    with c3:
        st.markdown(
            "**🔍 What I Detect**  \n"
            "Sector, organisation type, KPIs, column roles, and data quality issues."
        )
