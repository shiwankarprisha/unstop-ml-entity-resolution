# Business Entity Resolution — Approach

## 1. Problem Statement

The objective of this project is to identify matching business records across three independent data sources.

Source 1 is the deduplicated reference source. For each Source 1 entity, the system identifies corresponding records from Source 2 and Source 3. A Source 1 entity may have zero, one, or multiple matching records.

The input data contains noisy and inconsistent business names and addresses. The solution therefore uses a scalable candidate-generation (blocking) stage to reduce the number of possible comparisons, followed by a matching stage to determine the most likely entity matches.

## 2. Overall Pipeline

The solution follows the following high-level pipeline:

1. Load the Source 1, Source 2, and Source 3 records.
2. Normalize business names and addresses.
3. Generate a small candidate set for each Source 1 entity using blocking.
4. Compute similarity features between Source 1 records and their candidates.
5. Apply the matching logic to select likely matches.
6. Generate `matching_results.tsv`.
7. Generate `candidate_pairs.tsv` containing the final candidate set evaluated by the matching stage.
8. Validate the output files before submission.
