"""
Feature engineering for candidate business pairs.

Candidate generation gives us possible matches.
This module calculates signals that tell us how strong each pair is.
"""

import re
import pandas as pd
from difflib import SequenceMatcher


def string_similarity(a, b):
    """Character-level similarity between two normalized strings."""

    if not a or not b:
        return 0.0

    return SequenceMatcher(None, str(a), str(b)).ratio()


def token_jaccard(a, b):
    """Token overlap between two strings."""

    if not a or not b:
        return 0.0

    tokens_a = set(str(a).split())
    tokens_b = set(str(b).split())

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)

    return intersection / union


def extract_numbers(text):
    """Extract numbers such as building numbers and postal codes."""

    if not text:
        return set()

    return set(re.findall(r"\d+", str(text)))


def number_similarity(a, b):
    """
    Measure whether numeric address components overlap.

    Numbers can be useful signals for addresses such as:
        12 MG Road
        12 M.G. Road
    """

    nums_a = extract_numbers(a)
    nums_b = extract_numbers(b)

    if not nums_a or not nums_b:
        return 0.0

    intersection = len(nums_a & nums_b)
    union = len(nums_a | nums_b)

    return intersection / union


def country_match(country_a, country_b):
    """Check whether countries agree."""

    if pd.isna(country_a) or pd.isna(country_b):
        return 0.0

    a = str(country_a).strip().lower()
    b = str(country_b).strip().lower()

    if not a or not b:
        return 0.0

    return 1.0 if a == b else 0.0


def build_features(
    candidates,
    query_df,
    reference_df,
    query_id_col="entity_id",
    reference_id_col="entity_id",
):
    """
    Build matching features for every candidate pair.
    """

    # Only keep columns required for matching.
    query_columns = [
        query_id_col,
        "name_normalized",
        "address_normalized",
    ]

    reference_columns = [
        reference_id_col,
        "name_normalized",
        "address_normalized",
    ]

    # Country is optional so our small tests also work.
    if "country" in query_df.columns:
        query_columns.append("country")

    if "country" in reference_df.columns:
        reference_columns.append("country")

    query_lookup = query_df[query_columns].copy()
    reference_lookup = reference_df[reference_columns].copy()

    # Rename columns before joining.
    query_lookup = query_lookup.rename(
        columns={
            query_id_col: "query_id",
            "name_normalized": "query_name",
            "address_normalized": "query_address",
            "country": "query_country",
        }
    )

    reference_lookup = reference_lookup.rename(
        columns={
            reference_id_col: "candidate_id",
            "name_normalized": "candidate_name",
            "address_normalized": "candidate_address",
            "country": "candidate_country",
        }
    )

    # Attach query information.
    features = candidates.merge(
        query_lookup,
        on="query_id",
        how="left",
    )

    # Attach candidate information.
    features = features.merge(
        reference_lookup,
        on="candidate_id",
        how="left",
    )

    # -----------------------------
    # NAME FEATURES
    # -----------------------------

    features["name_similarity"] = features.apply(
        lambda row: string_similarity(
            row["query_name"],
            row["candidate_name"],
        ),
        axis=1,
    )

    features["name_token_overlap"] = features.apply(
        lambda row: token_jaccard(
            row["query_name"],
            row["candidate_name"],
        ),
        axis=1,
    )

    # -----------------------------
    # ADDRESS FEATURES
    # -----------------------------

    features["address_similarity"] = features.apply(
        lambda row: string_similarity(
            row["query_address"],
            row["candidate_address"],
        ),
        axis=1,
    )

    features["address_token_overlap"] = features.apply(
        lambda row: token_jaccard(
            row["query_address"],
            row["candidate_address"],
        ),
        axis=1,
    )

    features["address_number_similarity"] = features.apply(
        lambda row: number_similarity(
            row["query_address"],
            row["candidate_address"],
        ),
        axis=1,
    )

    # -----------------------------
    # COUNTRY FEATURE
    # -----------------------------

    if (
        "query_country" in features.columns
        and "candidate_country" in features.columns
    ):
        features["country_match"] = features.apply(
            lambda row: country_match(
                row["query_country"],
                row["candidate_country"],
            ),
            axis=1,
        )
    else:
        features["country_match"] = 0.0

    return features