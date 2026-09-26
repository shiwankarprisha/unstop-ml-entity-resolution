"""
Submission-output generation for the entity-resolution challenge.

Creates:
    output/candidate_pairs.tsv
    output/matching_results.tsv
"""

from pathlib import Path
import pandas as pd


def _combine_ids(series):
    """
    Convert IDs into one comma-separated string.

    Removes missing values and duplicate IDs while preserving order.
    """

    seen = set()
    result = []

    for value in series:
        if pd.isna(value):
            continue

        value = str(value).strip()

        if value and value not in seen:
            seen.add(value)
            result.append(value)

    return ",".join(result)


def create_candidate_pairs(
    source1_df,
    candidates,
    source1_id_col="entity_id",
):
    """
    Create candidate_pairs.tsv format.

    Exactly one row is produced for every Source 1 entity.
    """

    grouped = (
        candidates.groupby("query_id")["candidate_id"]
        .apply(_combine_ids)
        .reset_index()
        .rename(
            columns={
                "query_id": "source1_entity_id",
                "candidate_id": "candidate_entity_ids",
            }
        )
    )

    all_source1 = (
        source1_df[[source1_id_col]]
        .drop_duplicates()
        .rename(
            columns={
                source1_id_col: "source1_entity_id"
            }
        )
    )

    output = all_source1.merge(
        grouped,
        on="source1_entity_id",
        how="left",
    )

    output["candidate_entity_ids"] = (
        output["candidate_entity_ids"].fillna("")
    )

    return output


def create_matching_results(
    source1_df,
    matches,
    source1_id_col="entity_id",
):
    """
    Create matching_results.tsv format.

    Exactly one row is produced for every Source 1 entity.
    Unmatched entities receive an empty matched_entity_ids value.
    """

    grouped = (
        matches.groupby("query_id")["candidate_id"]
        .apply(_combine_ids)
        .reset_index()
        .rename(
            columns={
                "query_id": "source1_entity_id",
                "candidate_id": "matched_entity_ids",
            }
        )
    )

    all_source1 = (
        source1_df[[source1_id_col]]
        .drop_duplicates()
        .rename(
            columns={
                source1_id_col: "source1_entity_id"
            }
        )
    )

    output = all_source1.merge(
        grouped,
        on="source1_entity_id",
        how="left",
    )

    output["matched_entity_ids"] = (
        output["matched_entity_ids"].fillna("")
    )

    return output


def save_submission_files(
    source1_df,
    candidates,
    matches,
    output_dir="output",
):
    """
    Generate and save both official TSV files.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_output = create_candidate_pairs(
        source1_df,
        candidates,
    )

    matching_output = create_matching_results(
        source1_df,
        matches,
    )

    candidate_path = output_dir / "candidate_pairs.tsv"
    matching_path = output_dir / "matching_results.tsv"

    candidate_output.to_csv(
        candidate_path,
        sep="\t",
        index=False,
    )

    matching_output.to_csv(
        matching_path,
        sep="\t",
        index=False,
    )

    print(f"Saved: {candidate_path}")
    print(f"Saved: {matching_path}")

    print(
        f"Source 1 rows: {len(source1_df):,}"
    )
    print(
        f"matching_results rows: {len(matching_output):,}"
    )
    print(
        f"candidate_pairs rows: {len(candidate_output):,}"
    )

    return candidate_output, matching_output