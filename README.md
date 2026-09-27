# Unstop ML Entity Resolution

Business Entity Resolution solution for the Unstop ML Challenge.

## 1. Overview

This project performs large-scale business entity resolution across three independent data sources.

For each Source 1 entity, the pipeline identifies possible matching records from Source 2 and Source 3.

The final solution follows a blocking-first, two-stage matching approach:

1. Data preprocessing and normalization
2. Candidate generation / blocking
3. Similarity-based candidate scoring
4. Top-K candidate selection
5. Selective fallback for difficult entities
6. Final matching and thresholding
7. Submission file generation
8. Output validation

The solution is designed to avoid exhaustive comparison between every Source 1 entity and every Source 2/Source 3 entity.

---

## 2. Project Structure

```text
.
├── docs/
│   └── approach.md
├── notebooks/
├── outputs/
├── src/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── blocking.py
│   ├── features.py
│   ├── matching.py
│   └── generate_submission.py
├── README.md
├── Documentation_template.md
└── requirements.txt
```

---

## 3. Pipeline

The overall pipeline is:

```text
Source 1 / Source 2 / Source 3
              |
              v
       Preprocessing
              |
              v
   Candidate Generation
              |
              v
      Primary Scoring
              |
              v
       Top-20 Candidates
              |
              v
   Primary Confidence Check
          /          \
     Strong           Weak / Missing
       |                    |
       |                Fallback
       |                    |
       |          Medium-token candidates
       |                    |
       |                 Top-50
       |                    |
       \____________________/
                |
                v
         Final Scoring
                |
                v
            Threshold
                |
                v
       Final Predictions
                |
                v
            Validation
                |
                v
         Submission Files
```

### 3.1 Preprocessing

Business names and addresses are normalized before candidate generation and matching.

The preprocessing stage includes operations such as:

- missing-value handling
- Unicode normalization
- lowercasing
- punctuation normalization
- whitespace normalization
- field-specific text cleaning

The normalized representations are used consistently during candidate generation and similarity scoring.

### 3.2 Candidate Generation / Blocking

Instead of comparing every Source 1 entity against every Source 2/Source 3 entity, the pipeline first generates a smaller set of plausible candidate pairs.

The final pipeline uses exact and token-based candidate generation.

Exact normalized evidence is used to identify strong candidate pairs, while informative token-based retrieval provides additional candidate coverage.

The resulting candidate pairs are deduplicated before detailed similarity scoring.

### 3.3 Similarity Scoring

Candidate pairs are evaluated using normalized business name and address similarity.

Jaro-Winkler similarity is calculated independently for the normalized name and address fields.

The primary candidate score is:

```text
primary_score =
    0.60 × name_similarity
  + 0.40 × address_similarity
```

The strongest candidates are retained for each Source 1 entity.

### 3.4 Top-K Candidate Selection

Primary candidates are ranked independently for every Source 1 entity.

Only the Top-20 primary candidates are retained.

Candidates are ranked using the primary score, with deterministic tie-breaking using exact name agreement, exact address agreement, and candidate ID.

This reduces the number of candidates that need to be processed in subsequent stages.

### 3.5 Selective Fallback

Some Source 1 entities may not have sufficiently strong candidates in the primary candidate pool.

The fallback stage is therefore applied selectively rather than to every Source 1 entity.

A Source 1 entity enters fallback when:

```text
best primary score < 0.95
```

or when it has no primary candidate.

The fallback stage uses a broader token-based candidate search to provide additional candidate coverage for difficult entities.

### 3.6 Final Matching

Primary and fallback candidates are combined and deduplicated before the final decision.

The final score is:

```text
final_score =
    0.50 × name_similarity
  + 0.50 × address_similarity
```

A candidate is accepted only when the final score reaches the configured acceptance threshold.

The final validated V2 threshold is:

```text
final_score >= 0.850
```

This allows the system to leave an entity unmatched when no candidate provides sufficient evidence.

---

## 4. Source Code

The main pipeline modules are located under `src/`.

### `preprocessing.py`

Responsible for cleaning and normalizing the input records.

This includes the transformations applied to business names and addresses before candidate generation and matching.

### `blocking.py`

Responsible for candidate generation and blocking.

The purpose of this stage is to reduce the search space before detailed similarity calculations.

The final candidate-generation approach combines exact evidence with informative token-based retrieval.

### `features.py`

Responsible for calculating similarity features for candidate entity pairs.

The main matching signals are normalized business-name similarity and normalized address similarity.

### `matching.py`

Responsible for candidate scoring, ranking, thresholding, fallback logic, and final match selection.

### `generate_submission.py`

Responsible for connecting the pipeline stages and generating the final submission files.

---

## 5. Candidate Generation and Scalability

A full comparison between all Source 1 entities and all Source 2/Source 3 entities would result in a very large Cartesian product.

The solution avoids this by using blocking and candidate generation before expensive similarity calculations.

The primary candidate pool combines:

1. Exact normalized candidates
2. Rare/informative token candidates

The final V2 primary candidate pool contained:

```text
46,277,162 candidate pairs
```

covering:

```text
1,578,910 Source 1 entities
```

After primary scoring, only the Top-20 candidates per Source 1 entity are retained.

Difficult Source 1 entities are processed using a selective fallback stage rather than applying the fallback search to the complete dataset.

The fallback stage uses medium-frequency token candidates and retains the Top-50 candidates per fallback Source 1 entity.

Fallback processing is performed in batches to control memory usage.

This design allows the system to perform detailed fuzzy similarity calculations only on a relatively small set of plausible candidate pairs.

---

## 6. Similarity Features

The final V2 matching pipeline primarily uses two textual similarity features.

### 6.1 Name Similarity

Jaro-Winkler similarity is calculated between the normalized business names of the Source 1 entity and candidate entity.

### 6.2 Address Similarity

Jaro-Winkler similarity is calculated between the normalized business addresses of the Source 1 entity and candidate entity.

These features capture both exact-like similarity and small textual variations that may occur between records representing the same business.

---

## 7. Primary Matching

The primary candidate score is:

```text
primary_score =
    0.60 × name_similarity
  + 0.40 × address_similarity
```

Name similarity therefore contributes 60% of the primary score, while address similarity contributes 40%.

Candidates are ranked independently for each Source 1 entity.

The Top-20 candidates are retained.

The ranking uses:

1. Primary score
2. Exact normalized name agreement
3. Exact normalized address agreement
4. Candidate ID

This provides deterministic candidate selection when multiple candidates have similar scores.

---

## 8. Selective Fallback

The fallback stage is intended for Source 1 entities that are difficult to resolve using the primary candidate pool.

The fallback condition is:

```text
best_primary_score < 0.95
```

or:

```text
no primary candidate
```

Only these Source 1 entities enter the fallback search.

The fallback stage uses medium-frequency tokens from normalized business names and addresses.

Fallback candidates are processed in batches of:

```text
10,000 Source 1 entities
```

The fallback candidates are ranked and reduced to the Top-50 candidates per fallback Source 1 entity.

The fallback candidates are then combined with the relevant primary candidates before final scoring.

---

## 9. Final Matching and Threshold

The final matching score uses equal weighting between name and address:

```text
final_score =
    0.50 × name_similarity
  + 0.50 × address_similarity
```

The final acceptance threshold is:

```text
final_score >= 0.850
```

Candidates below the threshold are not accepted.

This means that the system does not force every Source 1 entity to have a match.

An empty match is a valid outcome when no candidate satisfies the final matching criteria.

---

## 10. Validation

The final outputs are validated before submission.

### 10.1 Matching Output Validation

The matching output is checked for:

- duplicate Source 1/candidate pairs
- invalid Source 1 IDs
- invalid candidate IDs
- consistency of prediction counts

### 10.2 Candidate Output Validation

The candidate output is checked for:

- correct number of rows
- unique Source 1 IDs
- duplicate Source 1 rows
- malformed rows
- duplicate candidate IDs within individual rows

### 10.3 Prediction/Candidate Consistency

Every final prediction is checked against the corresponding candidate set.

A final predicted entity must exist among the candidates associated with the same Source 1 entity.

The final V2 validation confirmed:

```text
Source 1 rows checked:       1,732,544
Predicted links checked:     5,030,669
Missing predicted links:     0
Missing Source 1 rows:       0
```

The candidate output validation confirmed:

```text
Data rows:                   1,732,544
Unique Source 1 IDs:         1,732,544
Duplicate Source 1 rows:     0
Malformed rows:              0
Duplicate candidate IDs:     0
```

---

## 11. Final Output Files

### `matching_results.tsv`

Contains the final predicted matches for each Source 1 entity.

The expected fields are:

```text
source1_entity_id
matched_entity_ids
```

There is one row for every Source 1 entity.

The `matched_entity_ids` field contains the accepted matching entity IDs.

Multiple matching entity IDs may be represented as a comma-separated list.

An empty value indicates that no match was accepted for that Source 1 entity.

### `candidate_pairs.tsv`

Contains the candidate records considered by the matching pipeline for each Source 1 entity.

The expected fields are:

```text
source1_entity_id
candidate_entity_ids
```

There is one row for every Source 1 entity.

The `candidate_entity_ids` field contains the candidate entity IDs generated by the blocking/candidate-generation stages.

Every final predicted entity must be present in the corresponding candidate set.

---

## 12. Final V2 Statistics

The final validated V2 output contains:

| Metric | Value |
|---|---:|
| Source 1 test entities | 1,732,544 |
| Source 1 entities with matches | 1,574,040 |
| Source 1 entities without matches | 158,504 |
| Final predicted links | 5,030,669 |
| Primary candidate pairs | 46,277,162 |
| Primary Source 1 entities covered | 1,578,910 |
| Primary candidates retained | Top-20 |
| Fallback trigger | Best primary score < 0.95 |
| Fallback candidates retained | Top-50 |
| Final score | 50% name + 50% address |
| Final acceptance threshold | 0.850 |

---

## 13. Reproducibility

The project is organized into modular source files under `src/`.

The intended execution flow is:

```text
1. Load Source 1, Source 2 and Source 3 data
2. Preprocess and normalize the records
3. Generate primary candidates
4. Score primary candidates
5. Retain Top-20 candidates per Source 1 entity
6. Identify entities requiring fallback
7. Generate and score fallback candidates
8. Retain Top-50 fallback candidates
9. Apply the final matching score
10. Apply the final acceptance threshold
11. Generate candidate_pairs.tsv
12. Generate matching_results.tsv
13. Validate the output files
```

Install the required dependencies using:

```bash
pip install -r requirements.txt
```

The final executable entry point should be the version of:

```text
src/generate_submission.py
```

provided with the submitted implementation.

The final V2 execution is also preserved in the project notebook for reference.

---

## 14. Dependencies

Python dependencies required by the final submitted implementation are listed in:

```text
requirements.txt
```

Install them using:

```bash
pip install -r requirements.txt
```

Only dependencies required by the final implementation should be included in `requirements.txt`.

---

## 15. Final Configuration

The following configuration corresponds to the validated V2 pipeline:

```text
Primary candidate generation:
Exact + rare/informative token candidates

Primary scoring:
60% name similarity + 40% address similarity

Primary candidate limit:
Top-20 per Source 1 entity

Fallback trigger:
Best primary score < 0.95 or no primary candidate

Fallback candidate generation:
Medium-frequency token candidates

Fallback candidate limit:
Top-50 per fallback Source 1 entity

Fallback batch size:
10,000 Source 1 entities

Final scoring:
50% name similarity + 50% address similarity

Final acceptance threshold:
0.850
```

The final leaderboard score should be added here after the final submission is evaluated.

```text
Validation Macro F0.5:
[TO BE UPDATED WITH FINAL VALIDATED VALUE]

Leaderboard score:
[TO BE UPDATED WITH FINAL SUBMISSION SCORE]
```

---

## 16. Methodology Summary

The final solution uses a two-stage candidate-generation and matching architecture.

The main design decisions are:

1. Normalize business names and addresses before comparison.
2. Avoid exhaustive pairwise comparison through blocking.
3. Combine exact and informative token-based candidate generation.
4. Use Jaro-Winkler similarity for normalized business names and addresses.
5. Rank primary candidates using a 60/40 name-address score.
6. Retain only the Top-20 primary candidates.
7. Identify difficult entities using the primary confidence score.
8. Apply a selective fallback search only to those difficult entities.
9. Use medium-frequency token candidates in the fallback stage.
10. Retain the Top-50 fallback candidates.
11. Combine primary and fallback candidates before final selection.
12. Use an equal-weight 50/50 name-address score for final matching.
13. Accept only candidates with a final score of at least 0.850.
14. Allow valid empty matches when no candidate satisfies the threshold.
15. Validate both output integrity and prediction/candidate consistency.

The resulting architecture separates candidate retrieval from final matching, allowing the solution to scale to a large entity-resolution dataset while retaining detailed similarity-based matching for plausible candidate pairs.

---

## 17. Documentation

Detailed technical methodology is provided in:

```text
Documentation_template.md
```

The documentation covers:

- problem definition
- data
- preprocessing
- blocking and candidate generation
- scalability
- similarity features
- primary matching
- selective fallback
- final thresholding
- validation
- final output
- reproducibility
