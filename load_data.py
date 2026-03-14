from __future__ import annotations

import pandas as pd

from src.db import CSV_PATH, DB_PATH, get_connection, initialize_database

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def main() -> None:
    data = pd.read_csv(CSV_PATH)

    with get_connection(DB_PATH) as conn:
        initialize_database(conn)

        projects = data[["project"]].drop_duplicates().rename(columns={"project": "project_id"})
        projects.to_sql("projects", conn, if_exists="append", index=False)

        subjects = (
            data[
                [
                    "subject",
                    "project",
                    "condition",
                    "age",
                    "sex",
                    "treatment",
                    "response",
                ]
            ]
            .drop_duplicates()
            .rename(columns={"subject": "subject_id", "project": "project_id"})
        )
        subjects.to_sql("subjects", conn, if_exists="append", index=False)

        samples = data[["sample", "subject", "sample_type", "time_from_treatment_start"]].rename(
            columns={"sample": "sample_id", "subject": "subject_id"}
        )
        samples.to_sql("samples", conn, if_exists="append", index=False)

        counts = data.melt(
            id_vars=["sample"],
            value_vars=POPULATIONS,
            var_name="population",
            value_name="count",
        ).rename(columns={"sample": "sample_id"})
        counts.to_sql("cell_counts", conn, if_exists="append", index=False)

    print(f"Loaded {len(data)} samples into {DB_PATH.name}")


if __name__ == "__main__":
    main()
