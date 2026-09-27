# Business Entity Resolution — Approach

## 1. Problem Statement

The objective of this project is to identify matching business records across three independent data sources.

For each Source 1 entity, the system identifies corresponding records from Source 2 and Source 3.

The same real-world business may appear differently across sources because of:

- differences in business-name formatting
- spelling variations
- punctuation
- abbreviations
- address formatting
- missing or inconsistent information

Because of these variations, direct exact matching is insufficient.

The final solution therefore uses:

1. Text normalization
2. Candidate generation / blocking
3. Similarity scoring
4. Top-K candidate selection
5. Selective fallback
6. Final threshold-based matching
7. Output validation

---

## 2. Overall Pipeline

The final V2 pipeline follows this structure:

```text
Source 1 / Source 2 / Source 3
              |
              v
       Preprocessing
              |
              v
   Primary Candidate Generation
              |
              v
      Primary Similarity Scoring
              |
              v
       Top-20 Candidates
              |
              v
    Primary Confidence Check
          /          \
      Strong          Weak / Missing
        |                  |
        |               Fallback
        |                  |
        |        Medium-token candidates
        |                  |
        |              Top-50 Candidates
        |                  |
        \__________________/
                 |
                 v
          Final Scoring
                 |
                 v
        Threshold Filtering
                 |
                 v
        Final Predictions
                 |
                 v
             Validation
```

The key design principle is to avoid exhaustive comparison between all Source 1 entities and all reference entities.

Instead, candidate generation first reduces the search space, after which detailed similarity calculations are applied to plausible candidate pairs.

---

## 3. Data Preprocessing and Normalization

Business names and addresses are normalized before candidate generation and matching.

The preprocessing stage handles common sources of textual variation, including:

- missing values
- Unicode normalization
- lowercase conversion
- punctuation normalization
- whitespace normalization
- field-specific text cleaning

Two normalized representations are used throughout the pipeline:

```text
name_normalized
address_normalized
```

### Business Name

The normalized business name is used for:

- exact candidate retrieval
- token extraction
- candidate generation
- similarity calculation

### Address

The normalized address is used for:

- token extraction
- candidate generation
- similarity calculation

The purpose of normalization is to remove irrelevant formatting differences while preserving information useful for identifying the same business.

---

## 4. Candidate Generation / Blocking

### 4.1 Motivation

Comparing every Source 1 entity against every Source 2 and Source 3 entity would result in a very large number of pairwise comparisons.

This is both computationally expensive and unnecessary because most entity pairs are clearly unrelated.

The pipeline therefore uses blocking to retrieve only plausible candidates.

```text
Source 1 entity
       |
       v
Normalized name / address
       |
       v
Candidate-generation indexes
       |
       v
Candidate entity IDs
       |
       v
Detailed similarity scoring
```

Blocking is particularly important because candidate generation determines the maximum possible recall of the matching stage.

If the correct entity is not included in the candidate set, the downstream matcher cannot recover it.

---

## 5. Primary Candidate Generation

The final V2 primary candidate pool combines two complementary sources of evidence:

1. Exact normalized candidates
2. Rare/informative token candidates

### 5.1 Exact Candidates

Exact normalized evidence is used to retrieve strong candidate pairs efficiently.

These candidates provide high-value matches where normalized business information agrees directly.

### 5.2 Rare / Informative Token Candidates

Normalized business names and addresses are tokenized.

Token frequency information is used to identify relatively rare and informative tokens.

Rare tokens are useful blocking keys because they generally retrieve a smaller and more relevant subset of reference records than common tokens.

The process is conceptually:

```text
Normalized name / address
          |
          v
        Tokens
          |
          v
  Token frequency analysis
          |
          v
Rare / informative tokens
          |
          v
 Reference lookup
          |
          v
 Candidate entity IDs
```

Candidate pairs generated from different blocking mechanisms are combined and deduplicated.

---

## 6. Primary Candidate Pool

The final V2 primary candidate pool contained:

```text
46,277,162 candidate pairs
```

covering:

```text
1,578,910 Source 1 entities
```

This candidate pool is substantially smaller than an exhaustive all-pairs comparison.

The purpose of this stage is to retain broad candidate coverage while avoiding unnecessary detailed similarity calculations.

---

## 7. Primary Similarity Scoring

Each primary candidate pair is evaluated using normalized business-name and address similarity.

The similarity function used is Jaro-Winkler similarity.

### Name Similarity

Jaro-Winkler similarity is calculated between:

```text
Source 1 normalized name
candidate normalized name
```

### Address Similarity

Jaro-Winkler similarity is calculated between:

```text
Source 1 normalized address
candidate normalized address
```

The primary score is:

```text
primary_score =
    0.60 × name_similarity
  + 0.40 × address_similarity
```

The name therefore contributes 60% of the primary score and the address contributes 40%.

---

## 8. Top-20 Primary Candidate Selection

Candidates are ranked independently for every Source 1 entity.

Only the strongest 20 primary candidates are retained:

```text
Top-20 candidates per Source 1 entity
```

The ranking uses the primary score.

Deterministic tie-breaking is applied using:

1. primary score
2. exact normalized name agreement
3. exact normalized address agreement
4. candidate ID

This Top-K reduction limits the number of candidate pairs passed to later stages.

---

## 9. Selective Fallback

Some Source 1 entities do not receive sufficiently strong evidence from the primary candidate-generation stage.

Rather than performing a broader search for every entity, the pipeline applies fallback selectively.

An entity enters the fallback stage when:

```text
best_primary_score < 0.95
```

or when:

```text
no primary candidate exists
```

The fallback stage is therefore focused on difficult or insufficiently covered Source 1 entities.

This provides additional candidate coverage without applying the more expensive fallback process to the entire dataset.

---

## 10. Fallback Candidate Generation

The fallback stage uses medium-frequency tokens from normalized business names and addresses.

This provides broader candidate coverage than the primary rare-token search.

Fallback processing is performed in batches of:

```text
10,000 Source 1 entities
```

Batch processing limits memory usage during large-scale candidate generation.

Fallback candidates are scored and ranked, and the strongest:

```text
Top-50 candidates per fallback Source 1 entity
```

are retained.

The relevant primary and fallback candidates are then combined before final matching.

---

## 11. Final Candidate Set

Primary and fallback candidates are combined before final matching.

Duplicate Source 1/candidate pairs are removed.

This is important because the same candidate may have been retrieved through multiple candidate-generation paths.

The resulting candidate set represents the complete set of entities considered by the final matching stage.

---

## 12. Final Matching Score

The final matching stage uses equal weighting between business-name and address similarity.

The final score is:

```text
final_score =
    0.50 × name_similarity
  + 0.50 × address_similarity
```

This gives equal importance to name and address evidence during the final matching decision.

---

## 13. Final Matching Threshold

A candidate is accepted as a final match only when:

```text
final_score >= 0.850
```

Candidates below this threshold are not accepted.

The threshold provides a separation between:

```text
Candidate generation
```

and:

```text
Final match acceptance
```

A candidate being retrieved does not automatically mean that it is accepted as a match.

---

## 14. No-Match Handling

The system does not force every Source 1 entity to receive a match.

If none of the available candidates reaches the final acceptance threshold, the Source 1 entity remains unmatched.

Therefore:

```text
Candidate exists
       ≠
Candidate must be matched
```

An empty match is a valid output.

This is important for avoiding low-confidence false matches.

---

## 15. Scalability

The final design improves scalability through several mechanisms.

### Blocking

Only plausible candidate pairs are passed to detailed similarity scoring.

### Exact Retrieval

Exact normalized evidence provides inexpensive candidate retrieval.

### Token-Based Retrieval

Informative tokens provide targeted candidate retrieval without scanning the entire reference dataset.

### Top-K Reduction

Only Top-20 primary candidates are retained.

Fallback entities retain only Top-50 candidates.

### Selective Fallback

The broader fallback search is applied only to Source 1 entities that have weak or missing primary evidence.

### Batch Processing

Fallback processing uses batches of 10,000 Source 1 entities to control memory consumption.

Together, these mechanisms substantially reduce the amount of detailed pairwise similarity computation required.

---

## 16. Feature Summary

The final V2 matching pipeline primarily uses:

| Feature | Description |
|---|---|
| Name similarity | Jaro-Winkler similarity of normalized business names |
| Address similarity | Jaro-Winkler similarity of normalized business addresses |

The primary and final stages use different weights:

```text
Primary:
60% name + 40% address

Final:
50% name + 50% address
```

The primary score is used to rank and reduce candidates, while the final score is used for the final acceptance decision.

---

## 17. Validation

The final pipeline performs validation at multiple levels.

### Matching Integrity

The final matching output is checked for:

- duplicate pairs
- invalid Source 1 IDs
- invalid candidate IDs

The final V2 matching validation reported:

```text
Duplicate pairs:       0
Invalid Source 1 IDs:  0
Invalid candidate IDs: 0
```

### Candidate File Integrity

The candidate output is checked for:

- correct row count
- unique Source 1 IDs
- duplicate Source 1 rows
- malformed rows
- duplicate candidate IDs

The final V2 candidate validation reported:

```text
Data rows:               1,732,544
Unique Source 1 IDs:     1,732,544
Duplicate Source 1 IDs: 0
Malformed rows:          0
Duplicate candidate IDs: 0
```

### Prediction / Candidate Consistency

Every final prediction is checked against the candidate set.

The final V2 validation reported:

```text
Source 1 rows checked:    1,732,544
Predicted links checked:  5,030,669
Missing predicted links:  0
Missing Source 1 rows:    0
```

Therefore every final predicted link is represented in the corresponding candidate set.

---

## 18. Final V2 Statistics

The final validated V2 output contains:

| Metric | Value |
|---|---:|
| Source 1 test entities | 1,732,544 |
| Source 1 entities with matches | 1,574,040 |
| Source 1 entities without matches | 158,504 |
| Final predicted links | 5,030,669 |
| Primary candidate pairs | 46,277,162 |
| Primary Source 1 entities covered | 1,578,910 |
| Primary candidate limit | Top-20 |
| Fallback trigger | Best primary score < 0.95 |
| Fallback candidate limit | Top-50 |
| Fallback batch size | 10,000 |
| Final score | 50% name + 50% address |
| Final threshold | 0.850 |

---

## 19. Output Files

The final pipeline generates two TSV files.

### `candidate_pairs.tsv`

Contains the candidate entity IDs considered for each Source 1 entity.

Expected columns:

```text
source1_entity_id
candidate_entity_ids
```

Every Source 1 entity has a corresponding row.

### `matching_results.tsv`

Contains the final accepted matches.

Expected columns:

```text
source1_entity_id
matched_entity_ids
```

Every Source 1 entity has a corresponding row.

An empty `matched_entity_ids` value represents a Source 1 entity for which no candidate passed the final threshold.

Every final predicted entity must be present in the corresponding candidate set.

---

## 20. Reproducibility

The intended final execution flow is:

```text
1. Load Source 1, Source 2 and Source 3 data
2. Normalize business names and addresses
3. Generate exact and rare-token primary candidates
4. Calculate primary name and address similarities
5. Rank and retain Top-20 primary candidates
6. Identify Source 1 entities requiring fallback
7. Generate medium-token fallback candidates
8. Process fallback candidates in batches
9. Retain Top-50 fallback candidates
10. Combine primary and fallback candidates
11. Calculate final matching scores
12. Apply the 0.850 final threshold
13. Generate candidate_pairs.tsv
14. Generate matching_results.tsv
15. Validate both output files
```

The final V2 implementation and configuration should be treated as the source of truth for reproducing the submitted result.

---

## 21. Final Configuration

The validated V2 configuration is:

```text
Primary candidate generation:
Exact + rare/informative token candidates

Primary score:
0.60 × name similarity + 0.40 × address similarity

Primary candidate limit:
Top-20

Fallback trigger:
Best primary score < 0.95 or no primary candidate

Fallback candidate generation:
Medium-frequency token candidates

Fallback candidate limit:
Top-50

Fallback batch size:
10,000 Source 1 entities

Final score:
0.50 × name similarity + 0.50 × address similarity

Final acceptance threshold:
0.850
```

---

## 22. Summary

The final solution separates entity resolution into two main stages:

1. Efficient candidate retrieval
2. Detailed candidate matching

The candidate-generation stage uses exact and informative token evidence to reduce the search space.

The primary candidate stage uses Jaro-Winkler name and address similarity with a 60/40 weighting and retains the Top-20 candidates.

Entities with weak or missing primary evidence are processed using a selective medium-token fallback stage.

The fallback stage retains the Top-50 candidates for each difficult entity.

The final matching stage uses equal weighting between name and address similarity and accepts candidates only when:

```text
final_score >= 0.850
```

The final outputs are validated for structural integrity, identifier validity, duplicate records, and consistency between candidate and matching files.

This architecture provides a scalable approach to large-scale business entity resolution while separating broad candidate retrieval from the final high-confidence matching decision.
