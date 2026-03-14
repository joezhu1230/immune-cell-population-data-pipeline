from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import mannwhitneyu

from src.db import ROOT

OUTPUT_DIR = ROOT / "output"
POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)


def build_summary_table(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
    WITH total_counts AS (
        SELECT sample_id, SUM(count) AS total_count
        FROM cell_counts
        GROUP BY sample_id
    )
    SELECT
        s.sample_id AS sample,
        tc.total_count,
        cc.population,
        cc.count,
        ROUND((100.0 * cc.count / tc.total_count), 6) AS percentage,
        subj.project_id AS project,
        subj.subject_id AS subject,
        subj.condition,
        subj.treatment,
        subj.response,
        subj.sex,
        s.sample_type,
        s.time_from_treatment_start
    FROM cell_counts cc
    JOIN samples s ON s.sample_id = cc.sample_id
    JOIN subjects subj ON subj.subject_id = s.subject_id
    JOIN total_counts tc ON tc.sample_id = cc.sample_id
    ORDER BY s.sample_id, cc.population;
    """
    summary = pd.read_sql_query(query, conn)
    summary.to_csv(OUTPUT_DIR / "summary_table.csv", index=False)
    return summary


def run_statistical_analysis(summary: pd.DataFrame) -> pd.DataFrame:
    filtered = summary[
        (summary["condition"].str.lower() == "melanoma")
        & (summary["treatment"].str.lower() == "miraclib")
        & (summary["response"].isin(["yes", "no"]))
        & (summary["sample_type"].str.upper() == "PBMC")
    ].copy()

    rows: list[dict[str, float | int | str | bool]] = []
    for population, group in filtered.groupby("population"):
        responders = group.loc[group["response"] == "yes", "percentage"]
        non_responders = group.loc[group["response"] == "no", "percentage"]
        statistic, p_value = mannwhitneyu(responders, non_responders, alternative="two-sided")
        rows.append(
            {
                "population": population,
                "n_responders": int(responders.shape[0]),
                "n_non_responders": int(non_responders.shape[0]),
                "mean_percentage_responders": round(float(responders.mean()), 6),
                "mean_percentage_non_responders": round(float(non_responders.mean()), 6),
                "median_percentage_responders": round(float(responders.median()), 6),
                "median_percentage_non_responders": round(float(non_responders.median()), 6),
                "mann_whitney_u": float(statistic),
                "p_value": float(p_value),
                "significant_p_lt_0_05": bool(p_value < 0.05),
            }
        )

    stats = pd.DataFrame(rows).sort_values("p_value").reset_index(drop=True)
    stats.to_csv(OUTPUT_DIR / "statistical_comparison.csv", index=False)
    return stats


def plot_boxplots(summary: pd.DataFrame) -> Path:
    filtered = summary[
        (summary["condition"].str.lower() == "melanoma")
        & (summary["treatment"].str.lower() == "miraclib")
        & (summary["response"].isin(["yes", "no"]))
        & (summary["sample_type"].str.upper() == "PBMC")
    ].copy()

    ordered = filtered.pivot_table(index=["sample", "response"], columns="population", values="percentage").reset_index()
    plot_data = [
        ordered.loc[ordered["response"] == label, pop].dropna().values
        for pop in POPULATIONS
        for label in ["yes", "no"]
    ]
    labels = [
        f"{pop}\nresp" if label == "yes" else f"{pop}\nnon-resp"
        for pop in POPULATIONS
        for label in ["yes", "no"]
    ]

    plt.figure(figsize=(14, 7))
    plt.boxplot(plot_data, tick_labels=labels)
    plt.ylabel("Relative frequency (%)")
    plt.xlabel("Immune cell population")
    plt.title("Melanoma PBMC samples on miraclib: responders vs non-responders")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    output_path = OUTPUT_DIR / "responder_vs_nonresponder_boxplot.png"
    plt.savefig(output_path, dpi=200)
    plt.close()
    return output_path


def run_subset_analysis(conn: sqlite3.Connection) -> dict[str, object]:
    baseline_query = """
    SELECT
        subj.project_id AS project,
        subj.subject_id AS subject,
        subj.response,
        subj.sex,
        s.sample_id AS sample,
        cc.count AS b_cell
    FROM samples s
    JOIN subjects subj ON subj.subject_id = s.subject_id
    JOIN cell_counts cc ON cc.sample_id = s.sample_id AND cc.population = 'b_cell'
    WHERE LOWER(subj.condition) = 'melanoma'
      AND LOWER(subj.treatment) = 'miraclib'
      AND UPPER(s.sample_type) = 'PBMC'
      AND s.time_from_treatment_start = 0
    ORDER BY subj.project_id, subj.subject_id, s.sample_id;
    """
    baseline = pd.read_sql_query(baseline_query, conn)
    baseline.to_csv(OUTPUT_DIR / "melanoma_miraclib_pbmc_baseline.csv", index=False)

    projects = (
        baseline.groupby("project")["sample"]
        .count()
        .reset_index(name="sample_count")
        .sort_values("project")
    )
    responses = (
        baseline.groupby("response")["subject"]
        .nunique()
        .reset_index(name="subject_count")
        .sort_values("response")
    )
    sexes = (
        baseline.groupby("sex")["subject"]
        .nunique()
        .reset_index(name="subject_count")
        .sort_values("sex")
    )
    avg_b_cell = baseline[(baseline["sex"] == "M") & (baseline["response"] == "yes")]["b_cell"].mean()

    projects.to_csv(OUTPUT_DIR / "baseline_project_counts.csv", index=False)
    responses.to_csv(OUTPUT_DIR / "baseline_response_counts.csv", index=False)
    sexes.to_csv(OUTPUT_DIR / "baseline_sex_counts.csv", index=False)

    results = {
        "baseline_sample_count": int(len(baseline)),
        "project_counts": projects.to_dict(orient="records"),
        "response_counts": responses.to_dict(orient="records"),
        "sex_counts": sexes.to_dict(orient="records"),
        "average_b_cells_melanoma_males_responders_time0": f"{avg_b_cell:.2f}",
    }

    pd.DataFrame(
        {
            "metric": [
                "baseline_sample_count",
                "average_b_cells_melanoma_males_responders_time0",
            ],
            "value": [
                results["baseline_sample_count"],
                results["average_b_cells_melanoma_males_responders_time0"],
            ],
        }
    ).to_csv(OUTPUT_DIR / "subset_analysis_summary.csv", index=False)
    return results
