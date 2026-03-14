from __future__ import annotations

from src.db import DB_PATH, get_connection
from src.analysis import ensure_output_dir, build_summary_table, run_statistical_analysis, plot_boxplots, run_subset_analysis


def main() -> None:
    ensure_output_dir()
    with get_connection(DB_PATH) as conn:
        summary = build_summary_table(conn)
        stats = run_statistical_analysis(summary)
        plot_path = plot_boxplots(summary)
        subset = run_subset_analysis(conn)

    print(f"Summary table rows: {len(summary)}")
    print(f"Statistical comparison rows: {len(stats)}")
    print(f"Saved boxplot to: {plot_path}")
    print(f"Subset analysis: {subset}")


if __name__ == "__main__":
    main()
