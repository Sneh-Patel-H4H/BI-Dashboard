from typing import Any, Dict, Optional

import streamlit as st

from core.chart_engine import generate_dashboard_charts
from core.kpi_engine import compute_kpis
from utils.formatting import format_change_pct


def render() -> None:
    st.title("Your Dashboard")

    df = st.session_state.get("raw_df")
    schema: Optional[Dict[str, Any]] = st.session_state.get("schema")
    kpis: Optional[Dict[str, Any]] = st.session_state.get("kpis")
    selected_kpis = st.session_state.get("selected_kpis", [])

    if df is None or schema is None:
        st.info("No data loaded yet. Head to **Upload Data** to get started.")
        return

    # ---- KPI cards ---------------------------------------------------------
    if kpis:
        st.markdown("### Key Metrics")
        _render_kpi_cards(kpis)
        st.markdown("")

    # ---- Charts ------------------------------------------------------------
    st.markdown("### Charts")

    with st.spinner("Generating charts…"):
        charts = generate_dashboard_charts(df, schema)

    if not charts:
        st.info(
            "No charts could be generated. "
            "This may be because the dataset has no numeric or date columns."
        )
        return

    # Render in pairs
    for i in range(0, len(charts), 2):
        cols = st.columns(2)
        for j, col_widget in enumerate(cols):
            idx = i + j
            if idx < len(charts):
                with col_widget:
                    st.plotly_chart(charts[idx]["fig"], use_container_width=True)

    # ---- Refresh -----------------------------------------------------------
    st.markdown("---")
    if st.button("🔄 Refresh KPIs", help="Recompute all KPI values from the current data"):
        with st.spinner("Recomputing KPIs…"):
            try:
                st.session_state.kpis = compute_kpis(df, schema, selected_kpis)
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Could not refresh KPIs: {e}")


# ---------------------------------------------------------------------------
# KPI card renderer
# ---------------------------------------------------------------------------

def _render_kpi_cards(kpis: Dict[str, Any]) -> None:
    valid = [(name, data) for name, data in kpis.items() if data.get("value") is not None]
    if not valid:
        st.info("KPI values could not be computed for this dataset.")
        return

    for i in range(0, len(valid), 4):
        batch = valid[i : i + 4]
        cols = st.columns(len(batch))
        for col_widget, (name, data) in zip(cols, batch):
            with col_widget:
                delta_str: Optional[str] = None
                delta_color = "normal"

                if data.get("change_pct") is not None:
                    delta_str = format_change_pct(data["change_pct"])
                    delta_color = (
                        "normal" if data.get("change_direction") == "up" else "inverse"
                    )

                st.metric(
                    label=name,
                    value=data.get("formatted_value", "N/A"),
                    delta=delta_str,
                    delta_color=delta_color,
                )
