"""
Candidate generation / blocking for business entity resolution.

The goal is to create a small set of plausible matches instead of
comparing every S1 record with every S2/S3 record.

Retrieval is performed in batches to control memory usage.
"""

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors


def _prepare_text(series):
    """Convert a pandas Series into safe strings."""
    return series.fillna("").astype(str).values


def generate_tfidf_candidates(
    query_df,
    reference_df,
    query_id_col="entity_id",
    reference_id_col="entity_id",
    text_col="name_normalized",
    top_k=10,
    batch_size=1000,
    ngram_range=(3, 5),
    min_df=2,
):
    """
    Retrieve Top-K candidate reference records for each query record.

    IMPORTANT:
    Queries are processed in batches so that we do not create a huge
    query x reference similarity matrix in memory.
    """

    if len(query_df) == 0 or len(reference_df) == 0:
        return pd.DataFrame(
            columns=[
                "query_id",
                "candidate_id",
                "retrieval_score",
                "retrieval_field",
            ]
        )

    reference_text = _prepare_text(reference_df[text_col])
    query_text = _prepare_text(query_df[text_col])

    # Character TF-IDF works well with noisy names/addresses.
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=ngram_range,
        min_df=min_df,
        dtype=np.float32,
        norm="l2",
    )

    reference_matrix = vectorizer.fit_transform(reference_text)

    # Nearest-neighbour search avoids constructing the complete
    # query-vs-reference similarity matrix.
    nn = NearestNeighbors(
        metric="cosine",
        algorithm="brute",
        n_jobs=-1,
    )

    nn.fit(reference_matrix)

    k = min(top_k, len(reference_df))

    results = []

    for start in range(0, len(query_df), batch_size):

        end = min(start + batch_size, len(query_df))

        batch_text = query_text[start:end]

        batch_matrix = vectorizer.transform(batch_text)

        distances, indices = nn.kneighbors(
            batch_matrix,
            n_neighbors=k,
            return_distance=True,
        )

        # cosine similarity = 1 - cosine distance
        similarities = 1.0 - distances

        batch_query_ids = query_df.iloc[start:end][
            query_id_col
        ].values

        for row_position, query_id in enumerate(batch_query_ids):

            for rank in range(k):

                reference_position = indices[row_position, rank]

                candidate_id = reference_df.iloc[
                    reference_position
                ][reference_id_col]

                results.append(
                    {
                        "query_id": query_id,
                        "candidate_id": candidate_id,
                        "retrieval_score": float(
                            similarities[row_position, rank]
                        ),
                        "retrieval_field": text_col,
                    }
                )

    return pd.DataFrame(results)


def generate_candidates(
    query_df,
    reference_df,
    query_id_col="entity_id",
    reference_id_col="entity_id",
    name_top_k=10,
    address_top_k=10,
    batch_size=1000,
):
    """
    Generate candidates using BOTH business name and address.

    Name candidates and address candidates are unioned and duplicate
    query-candidate pairs are removed.
    """

    print("Generating name candidates...")

    name_candidates = generate_tfidf_candidates(
        query_df=query_df,
        reference_df=reference_df,
        query_id_col=query_id_col,
        reference_id_col=reference_id_col,
        text_col="name_normalized",
        top_k=name_top_k,
        batch_size=batch_size,
    )

    print(
        f"Name candidates generated: "
        f"{len(name_candidates):,}"
    )

    print("Generating address candidates...")

    address_candidates = generate_tfidf_candidates(
        query_df=query_df,
        reference_df=reference_df,
        query_id_col=query_id_col,
        reference_id_col=reference_id_col,
        text_col="address_normalized",
        top_k=address_top_k,
        batch_size=batch_size,
    )

    print(
        f"Address candidates generated: "
        f"{len(address_candidates):,}"
    )

    combined = pd.concat(
        [name_candidates, address_candidates],
        ignore_index=True,
    )

    # If the same candidate was found through both name and address,
    # keep its strongest retrieval score.
    combined = (
        combined.sort_values(
            "retrieval_score",
            ascending=False,
        )
        .drop_duplicates(
            subset=["query_id", "candidate_id"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    print(
        f"Unique candidate pairs: "
        f"{len(combined):,}"
    )

    return combined