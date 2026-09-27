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
9. ## 3. Data Preprocessing and Normalization

The preprocessing stage creates normalized versions of the business name and business address fields while preserving Unicode characters.

### Business Name Normalization

Business names are normalized using the following steps:

1. Missing values are converted to empty strings.
2. Text is converted to lowercase.
3. Unicode text is normalized using NFKC normalization.
4. The `&` character is standardized to the word `and`.
5. Common website prefixes and domain suffixes are removed:
   - `www.`
   - `.com`
   - `.in`
   - `.org`
   - `.net`
6. Characters that are not Unicode letters, numbers, combining marks, or whitespace are replaced with spaces.
7. Repeated whitespace is collapsed and leading/trailing whitespace is removed.

### Business Address Normalization

Business addresses use a similar normalization process:

1. Missing values are converted to empty strings.
2. Text is converted to lowercase.
3. Unicode text is normalized using NFKC normalization.
4. Characters that are not Unicode letters, numbers, combining marks, or whitespace are replaced with spaces.
5. Repeated whitespace is collapsed and leading/trailing whitespace is removed.

### Generated Features

The preprocessing stage adds two normalized columns to each dataframe:

- `name_normalized`
- `address_normalized`

These normalized fields are subsequently used by the candidate-generation and matching stages.
## 4. Candidate Generation / Blocking

Comparing every Source 1 record against every Source 2 and Source 3 record would be computationally expensive. The candidate-generation stage therefore retrieves only a small set of plausible reference records for each query record.

### Character-Level TF-IDF Retrieval

Candidate retrieval uses character-level TF-IDF representations of the normalized business name and address fields.

The TF-IDF vectorizer uses:

- Analyzer: `char_wb`
- Character n-gram range: 3 to 5
- Minimum document frequency: 2
- Data type: `float32`
- Normalization: L2

Character n-grams are used to make retrieval more tolerant of spelling variations, formatting differences, abbreviations, and other noisy text variations.

### Nearest-Neighbor Retrieval

For each query record, the system retrieves the Top-K reference records using cosine distance through `NearestNeighbors`.

Candidates are generated independently using:

1. `name_normalized`
2. `address_normalized`

The default retrieval limit is 10 candidates from the business name and 10 candidates from the business address.

The two candidate sets are then combined. If the same query-reference pair is retrieved through both fields, duplicate pairs are removed and the candidate with the stronger retrieval score is retained.

### Batch Processing

Query records are processed in batches rather than constructing a complete query-by-reference similarity matrix in memory.

The default batch size is 1,000 records. This reduces peak memory usage and allows the retrieval process to scale to larger datasets.

### Candidate Set

The resulting unique query-reference pairs form the candidate set passed to the subsequent matching stage. The retrieval score and the field responsible for retrieving the candidate are retained for downstream processing.
## 5. Matching Model and Decision Logic

After candidate generation, each Source 1–candidate pair is evaluated using a set of similarity features.

### Weighted Match Score

The matching stage combines name, address, token-overlap, address-number, and country information.

The current scoring function is:

match_score =
    0.40 × name_similarity
  + 0.15 × name_token_overlap
  + 0.30 × address_similarity
  + 0.10 × address_token_overlap
  + 0.05 × address_number_similarity

Name and address similarity receive the largest weights because they provide the primary evidence for whether two business records represent the same entity.

### Country Consistency

Country disagreement is treated as strong negative evidence when country information is available for both records.

The pipeline does not hard-code a fixed set of countries. When both country values are known and they disagree, the calculated match score is multiplied by 0.25.

This allows the pipeline to handle countries that may appear in the test data but were not present in the training data.

### Match Selection

Candidates are ranked by their calculated match score for each Source 1 entity.

The strongest candidate must reach the main matching threshold before any match is accepted.

Additional candidates are handled more conservatively and must reach a stricter secondary threshold. This supports Source 1 entities that genuinely correspond to multiple records while reducing the risk of false merges.

If the strongest candidate does not reach the main threshold, the Source 1 entity is treated as having no accepted match.

The matcher also applies a maximum number of accepted matches per Source 1 entity.

The threshold values and maximum-match setting are configurable and should be selected using validation on labelled training data.
## 6. Feature Engineering

For each candidate pair, the pipeline calculates multiple similarity features using the normalized business name and address fields.

### Name Features

Two features are calculated for business names:

- `name_similarity`: Character-level similarity calculated using Python's `SequenceMatcher`.
- `name_token_overlap`: Jaccard similarity between the sets of whitespace-separated name tokens.

### Address Features

Three features are calculated for business addresses:

- `address_similarity`: Character-level similarity using `SequenceMatcher`.
- `address_token_overlap`: Jaccard similarity between address token sets.
- `address_number_similarity`: Jaccard similarity between the sets of numeric components extracted from the two addresses.

Numeric components can capture useful evidence such as matching building numbers or postal-code components.

### Country Feature

A `country_match` feature is also calculated.

The feature is:

- `1.0` when both country values are present and equal after trimming whitespace and converting to lowercase.
- `0.0` when the values are missing, empty, or different.

The implementation does not assume a fixed list of countries, allowing the pipeline to handle previously unseen country labels.

### Feature Construction

The candidate pairs are joined with the corresponding normalized Source 1 and reference records. The resulting feature table contains the candidate identifiers together with the similarity signals used by the matching stage.

These features provide complementary evidence: character similarity captures textual closeness, token overlap captures shared words, numeric similarity captures address-number consistency, and country agreement provides an additional consistency signal.
