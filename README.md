# Immune Cell Population Data Pipeline

This repository contains a complete solution for the Teiko technical assignment using Python, SQLite, and Streamlit.

## Repository structure

```text
.
├── app.py
├── cell-count.csv
├── load_data.py
├── Makefile
├── README.md
├── requirements.txt
├── run_pipeline.py
├── src/
│   ├── analysis.py
│   └── db.py
└── output/
```

## How to run

In GitHub Codespaces or any local Python environment:

```bash
make setup
make pipeline
make dashboard
```

What each command does:

- `make setup` installs the required Python packages.
- `make pipeline` creates `teiko.db`, loads the CSV into SQLite, builds the Part 2 summary table, runs the Part 3 statistical analysis, generates the boxplot, and writes the Part 4 subset outputs.
- `make dashboard` starts the Streamlit dashboard locally.

The dashboard will usually be available at `http://localhost:8501`.

## Database schema and design rationale

The dataset is modeled with four tables:

### 1. `projects`
Stores one row per project.

- `project_id` (PK)

### 2. `subjects`
Stores one row per subject. Subject-level metadata lives here because condition, age, sex, treatment, and response are repeated across samples from the same subject.

- `subject_id` (PK)
- `project_id` (FK to `projects`)
- `condition`
- `age`
- `sex`
- `treatment`
- `response`

### 3. `samples`
Stores one row per biological sample.

- `sample_id` (PK)
- `subject_id` (FK to `subjects`)
- `sample_type`
- `time_from_treatment_start`

### 4. `cell_counts`
Stores one row per sample and population. This is a long-format fact table that makes downstream analysis easier than storing one column per population inside the sample table.

- `sample_id` (FK to `samples`)
- `population`
- `count`
- composite primary key: (`sample_id`, `population`)

### Why this scales well

This schema is normalized enough for larger studies:

- Hundreds of projects can be added without duplicating project metadata.
- Thousands of subjects and samples remain manageable because repeated subject-level attributes are stored once.
- Additional immune populations can be added without changing the table structure, because new rows can simply be inserted into `cell_counts`.
- New analytics can be layered on top of the same schema using SQL joins, aggregations, and filters.
- Indexes were added on common filter columns such as condition, treatment, response, sample type, time, and population.

## Code structure

### `load_data.py`
Root-level script required by the prompt. It initializes the SQLite schema and loads the CSV into the four relational tables.

### `run_pipeline.py`
Runs the full analysis pipeline after the database has been created.

### `src/db.py`
Contains path configuration, database connection helpers, and the schema creation SQL.

### `src/analysis.py`
Contains the data products for Parts 2-4:

- summary table generation
- responder versus non-responder statistical testing
- boxplot creation
- baseline melanoma PBMC subset analysis

### `app.py`
Streamlit dashboard that presents the generated outputs interactively.

This split keeps data loading, database concerns, analysis logic, and presentation separate, which makes the code easier to test, maintain, and extend.

## Analytical choices

### Part 2
The summary table is generated from the SQLite database. For each sample, total cell count is computed as the sum of the five populations, then each population's percentage is computed as:

`percentage = 100 * count / total_count`

### Part 3
The responder analysis filters to:

- `condition = melanoma`
- `treatment = miraclib`
- `sample_type = PBMC`
- responders `response = yes`
- non-responders `response = no`

To compare the two groups for each population, the pipeline uses the two-sided Mann-Whitney U test. This is a reasonable choice because relative-frequency data may not be normally distributed.

The pipeline writes:

- `output/statistical_comparison.csv`
- `output/responder_vs_nonresponder_boxplot.png`

### Part 4
The subset analysis filters to baseline melanoma PBMC samples treated with miraclib, meaning:

- `condition = melanoma`
- `sample_type = PBMC`
- `time_from_treatment_start = 0`
- `treatment = miraclib`

It then reports:

- number of samples from each project
- number of unique responder and non-responder subjects
- number of unique male and female subjects
- average B-cell count for melanoma males who were responders at time 0

## Expected outputs

After `make pipeline`, the `output/` directory contains:

- `summary_table.csv`
- `statistical_comparison.csv`
- `responder_vs_nonresponder_boxplot.png`
- `melanoma_miraclib_pbmc_baseline.csv`
- `baseline_project_counts.csv`
- `baseline_response_counts.csv`
- `baseline_sex_counts.csv`
- `subset_analysis_summary.csv`

## Dashboard link

Once started locally, the dashboard is available at:

`http://localhost:8501`

For a GitHub submission, you can keep this section and replace it with a deployed Streamlit URL if you choose to deploy it.
