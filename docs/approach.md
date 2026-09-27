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
