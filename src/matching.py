"""
Conservative matching logic for business entity resolution.

The matcher combines the features generated in features.py
and decides which candidate pairs are confident enough to accept.
"""

import pandas as pd


def calculate_match_score(features):
    """
    Calculate a weighted matching score.

    Name and address similarity receive the largest weights.
    The weights are intentionally easy to change later after
    validation on labelled training data.
    """

    df = features.copy()

    df["match_score"] = (
        0.40 * df["name_similarity"]
        + 0.15 * df["name_token_overlap"]
        + 0.30 * df["address_similarity"]
        + 0.10 * df["address_token_overlap"]
        + 0.05 * df["address_number_similarity"]
    )

    # Country disagreement is strong negative evidence.
    # We do NOT hard-code any specific countries.
    if (
        "query_country" in df.columns
        and "candidate_country" in df.columns
    ):
        known_country = (
            df["query_country"].notna()
            & df["candidate_country"].notna()
            & (df["query_country"].astype(str).str.strip() != "")
            & (df["candidate_country"].astype(str).str.strip() != "")
        )

        country_disagreement = (
            known_country
            & (df["country_match"] == 0)
        )

        df.loc[country_disagreement, "match_score"] *= 0.25

    return df


def select_matches(
    features,
    threshold=0.78,
    secondary_threshold=0.84,
    max_matches=5,
):
    """
    Select zero, one, or multiple matches for each Source 1 entity.

    The first candidate must pass the main threshold.

    Additional candidates are accepted only if they pass the stricter
    secondary threshold. This keeps multi-match support conservative,
    which is important for the precision-heavy F0.5 metric.

    Thresholds should later be tuned using labelled training data.
    """

    scored = calculate_match_score(features)

    scored = scored.sort_values(
        ["query_id", "match_score"],
        ascending=[True, False],
    )

    accepted = []

    for query_id, group in scored.groupby("query_id"):

        group = group.reset_index(drop=True)

        # Best candidate
        best = group.iloc[0]

        # If even the strongest candidate is weak,
        # treat this Source 1 entity as a singleton.
        if best["match_score"] < threshold:
            continue

        accepted.append(
            {
                "query_id": query_id,
                "candidate_id": best["candidate_id"],
                "match_score": float(best["match_score"]),
            }
        )

        # Additional matches require stronger evidence.
        additional = group.iloc[1:]

        for _, row in additional.iterrows():

            if len(
                [
                    x for x in accepted
                    if x["query_id"] == query_id
                ]
            ) >= max_matches:
                break

            if row["match_score"] >= secondary_threshold:

                accepted.append(
                    {
                        "query_id": query_id,
                        "candidate_id": row["candidate_id"],
                        "match_score": float(row["match_score"]),
                    }
                )

    return pd.DataFrame(
        accepted,
        columns=[
            "query_id",
            "candidate_id",
            "match_score",
        ],
    )