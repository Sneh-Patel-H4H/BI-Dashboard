import pandas as pd
import streamlit as st

from core.kpi_engine import compute_kpis
from utils.formatting import format_date_range

# ---------------------------------------------------------------------------
# Colour mappings
# ---------------------------------------------------------------------------

SECTOR_COLORS: dict[str, str] = {
    "Ecommerce": "#FF6B35",
    "Marketing": "#9B59B6",
    "Sales/CRM": "#2E75B6",
    "SaaS/Product": "#27AE60",
    "Customer Support": "#7F8C8D",
    "Finance": "#7F8C8D",
    "HR / People": "#7F8C8D",
    "Logistics / Operations": "#E67E22",
    "Healthcare": "#1ABC9C",
    "Mixed": "#95A5A6",
}

CONFIDENCE_COLORS: dict[str, str] = {
    "High": "#27AE60",
    "Medium": "#F39C12",
    "Low": "#E74C3C",
}


def render() -> None:
    schema: dict = st.session_state.schema
    df: pd.DataFrame = st.session_state.raw_df
    sector: str = st.session_state.sector or "Unknown"
    sector_confidence: str = st.session_state.sector_confidence or "Low"
    org_type: str = st.session_state.org_type or "Unknown"
    org_confidence: str = st.session_state.org_confidence or "Low"
    dataset_description: str = st.session_state.dataset_description or ""
    quality_notes: list[str] = st.session_state.data_quality_notes

    # ---- Animated header -----------------------------------------------
    st.markdown(
        """
        <div style="text-align:center; padding:24px 0 8px;">
            <div style="font-size:56px; animation: pulse 1s ease-in-out;">✨</div>
            <h1 style="color:#2C3E50; font-size:26px; margin:8px 0 4px;">
                Here is what I found in your data
            </h1>
            <p style="color:#7F8C8D; font-size:15px; margin:0;">
                AI-powered analysis complete
            </p>
        </div>
        <style>
            @keyframes pulse {
                0%   { transform: scale(0.8); opacity: 0; }
                60%  { transform: scale(1.1); opacity: 1; }
                100% { transform: scale(1.0); }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---- Sector + Org cards --------------------------------------------
    col_sector, col_org = st.columns(2)

    with col_sector:
        sector_color = SECTOR_COLORS.get(sector, "#7F8C8D")
        conf_color = CONFIDENCE_COLORS.get(sector_confidence, "#95A5A6")
        st.markdown("**Detected Sector**")
        st.markdown(
            f"""
            <div style="margin:8px 0 4px;">
                <span style="background:{sector_color};color:white;padding:6px 16px;
                    border-radius:20px;font-weight:600;font-size:15px;">{sector}</span>
                <span style="background:{conf_color};color:white;padding:4px 10px;
                    border-radius:20px;font-size:12px;margin-left:8px;">
                    {sector_confidence} Confidence
                </span>
            </div>
            <p style="color:#7F8C8D;font-size:13px;margin:6px 0 0;">
                {schema.get("sector_reasoning", "")}
            </p>
            """,
            unsafe_allow_html=True,
        )

    with col_org:
        org_conf_color = CONFIDENCE_COLORS.get(org_confidence, "#95A5A6")
        st.markdown("**Organisation Type**")
        st.markdown(
            f"""
            <div style="margin:8px 0 4px;">
                <span style="background:#34495E;color:white;padding:6px 16px;
                    border-radius:20px;font-weight:600;font-size:15px;">{org_type}</span>
                <span style="background:{org_conf_color};color:white;padding:4px 10px;
                    border-radius:20px;font-size:12px;margin-left:8px;">
                    {org_confidence} Confidence
                </span>
            </div>
            <p style="color:#7F8C8D;font-size:13px;margin:6px 0 0;">
                {schema.get("org_reasoning", "")}
            </p>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ---- Dataset summary -----------------------------------------------
    st.markdown("**Dataset Summary**")

    date_range_str = ""
    for col_meta in schema.get("columns", []):
        if col_meta.get("role") == "date":
            col_name = col_meta["original_name"]
            if col_name in df.columns and pd.api.types.is_datetime64_any_dtype(df[col_name]):
                date_range_str = format_date_range(df[col_name])
                break

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Rows", f"{len(df):,}")
    with m2:
        st.metric("Columns", f"{len(df.columns):,}")
    with m3:
        if date_range_str:
            st.metric("Date Range", date_range_str)
        else:
            completeness = int((1 - df.isna().mean().mean()) * 100)
            st.metric("Data Completeness", f"{completeness}%")
    with m4:
        high_kpi_count = sum(
            1 for k in schema.get("suggested_kpis", []) if k.get("priority") == "high"
        )
        st.metric("KPIs Identified", str(high_kpi_count))

    if dataset_description:
        st.markdown(f"*{dataset_description}*")

    # ---- Data quality warnings -----------------------------------------
    if quality_notes:
        st.markdown("")
        st.markdown("**⚠️ Data Quality Notes**")
        for note in quality_notes:
            st.warning(note)

    st.markdown("---")

    # ---- KPI checkboxes ------------------------------------------------
    st.markdown("**Proposed KPIs**")
    st.markdown(
        "These KPIs will appear on your dashboard. Uncheck any you don't want to include."
    )

    all_kpis: list[dict] = schema.get("suggested_kpis", [])
    high_kpis = [k for k in all_kpis if k.get("priority") == "high"]
    other_kpis = [k for k in all_kpis if k.get("priority") != "high"]

    selected: list[dict] = []

    for kpi in high_kpis:
        checked = st.checkbox(
            f"**{kpi['name']}** — {kpi.get('formula', '')}",
            value=True,
            key=f"kpi_check_{kpi['name']}",
        )
        if checked:
            selected.append(kpi)

    if other_kpis:
        with st.expander("Additional KPIs (optional)"):
            for kpi in other_kpis:
                checked = st.checkbox(
                    f"{kpi['name']} — {kpi.get('formula', '')}",
                    value=False,
                    key=f"kpi_check_{kpi['name']}",
                )
                if checked:
                    selected.append(kpi)

    st.markdown("---")

    # ---- CTA -----------------------------------------------------------
    btn_disabled = len(selected) == 0
    if btn_disabled:
        st.info("Select at least one KPI to build your dashboard.")

    if st.button(
        "🚀 Build My Dashboard",
        type="primary",
        use_container_width=True,
        disabled=btn_disabled,
    ):
        with st.spinner("Computing your KPIs…"):
            try:
                kpis = compute_kpis(df, schema, selected)
                st.session_state.kpis = kpis
                st.session_state.selected_kpis = selected
                st.session_state.discovery_complete = True
                # Navigate directly to the Dashboard page
                st.session_state.selected_nav = "📊 Dashboard"
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Could not build your dashboard: {e}")
