from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"

st.set_page_config(page_title="Immune Cell Dashboard", layout="wide")
st.caption("Interactive review of Parts 2-4 for the clinical trial dataset")

summary_path = OUTPUT_DIR / "summary_table.csv"
stats_path = OUTPUT_DIR / "statistical_comparison.csv"
plot_path = OUTPUT_DIR / "responder_vs_nonresponder_boxplot.png"
subset_path = OUTPUT_DIR / "melanoma_miraclib_pbmc_baseline.csv"

missing = [p.name for p in [summary_path, stats_path, plot_path, subset_path] if not p.exists()]
if missing:
    st.error("Pipeline outputs are missing. Run `make pipeline` before starting the dashboard.")
    st.stop()

summary = pd.read_csv(summary_path)
stats = pd.read_csv(stats_path)
subset = pd.read_csv(subset_path)

st.subheader("Part 2, Sample frequency overview")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Samples", summary["sample"].nunique())
with col2:
    st.metric("Subjects", summary["subject"].nunique())
with col3:
    st.metric("Rows in summary table", len(summary))

selected_sample = st.selectbox("Choose a sample", sorted(summary["sample"].unique())[:200])
sample_view = summary.loc[summary["sample"] == selected_sample, ["sample", "total_count", "population", "count", "percentage"]]
st.dataframe(sample_view, use_container_width=True)

st.subheader("Part 3, Responder versus non-responder analysis")
st.image(str(plot_path), use_container_width=True)
st.dataframe(stats, use_container_width=True)

significant = stats.loc[stats["significant_p_lt_0_05"]]
if significant.empty:
    st.info("No populations are significant at p < 0.05.")
else:
    st.success(
        "Significant populations at p < 0.05: "
        + ", ".join(significant["population"].tolist())
    )

st.subheader("Part 4, Baseline melanoma PBMC subset")
left, right = st.columns(2)
with left:
    st.write("Baseline subset preview")
    st.dataframe(subset.head(20), use_container_width=True)
with right:
    st.write("Counts by project")
    st.dataframe(subset.groupby("project")["sample"].count().reset_index(name="sample_count"), use_container_width=True)
    st.write("Unique subjects by response")
    st.dataframe(subset.groupby("response")["subject"].nunique().reset_index(name="subject_count"), use_container_width=True)
    st.write("Unique subjects by sex")
    st.dataframe(subset.groupby("sex")["subject"].nunique().reset_index(name="subject_count"), use_container_width=True)
    value = subset[(subset["sex"] == "M") & (subset["response"] == "yes")]["b_cell"].mean()
    st.metric("Average B cells, melanoma males, responders, time=0", f"{value:.2f}")

st.markdown("Note: the prompt mentions quintazide, but the provided dataset only contains treatment values analyzed from the actual file, including miraclib.")
