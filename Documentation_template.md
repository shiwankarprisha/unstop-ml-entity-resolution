# Business Entity Resolution — Methodology Documentation

## 1. Problem Definition

The objective of this project is to perform business entity resolution across three independent data sources:

- Source 1
- Source 2
- Source 3

The task is to identify which Source 2 and Source 3 records correspond to the same real-world business represented by each Source 1 entity.

The same business may appear differently across sources due to:

- differences in business-name formatting
- spelling variations
- punctuation differences
- abbreviations
- address formatting differences
- missing information
- other textual inconsistencies

Therefore, exact identifier matching alone is insufficient. The solution uses preprocessing, candidate generation, similarity scoring, selective fallback, and threshold-based matching.

A Source 1 entity may legitimately have no corresponding entity. Therefore, the system does not force every Source 1 entity to receive a match.

---

## 2. Data

The challenge contains business records from three independent sources.

### Source 1

Source 1 is the query/reference population for which final predictions are generated.

Each Source 1 entity is evaluated against potentially corresponding records in the reference sources.

### Source 2 and Source 3

Source 2 and Source 3 contain business records that may correspond to Source 1 entities.

The two sources are treated as possible matching targets during candidate generation and final matching.

### Training / Ground Truth Data

Training and ground-truth data are used during development to understand the entity-resolution problem and validate the matching methodology.

The ground truth can be used to evaluate:

- candidate generation
- similarity features
- matching decisions
- threshold choices
- overall validation performance

The final test data does not provide the corresponding ground-truth matches, so final test predictions are generated using the validated pipeline.

The solution relies on the data supplied by the challenge and does not require external business information.

---

# 3. Overall Methodology

The final solution uses a blocking-first, two-stage entity-resolution architecture.

The overall flow is:

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
      Primary Scoring
              |
              v
       Top-20 Candidates
              |
              v
    Primary Confidence Check
          /          \
      Strong          Weak / Missing
        |                  |
        |              Fallback
        |                  |
        |        Medium-token retrieval
        |                  |
        |              Top-50 Candidates
        |                  |
        \__________________/
                 |
                 v
          Final Scoring
                 |
                 v
            Thresholding
                 |
                 v
        Final Predictions
                 |
                 v
             Validation
```

The main design principle is to avoid comparing every Source 1 entity against every Source 2/Source 3 entity.

Instead, the pipeline first retrieves plausible candidates and then performs more detailed similarity calculations only on those candidates.

---

# 4. Preprocessing

Business names and addresses can contain substantial formatting variation.

Before candidate generation and matching, the relevant text fields are normalized.

## 4.1 General Text Normalization

The preprocessing stage includes operations such as:

- handling missing values
- Unicode NFKC normalization
- conversion to lowercase
- punctuation normalization
- whitespace normalization
- preservation of useful letters and numbers

The purpose is to reduce superficial differences between records while retaining information that can help identify the same business.

## 4.2 Business Name Normalization

Business names receive field-specific normalization before candidate generation.

The normalized business name is used for:

- exact candidate generation
- token extraction
- candidate retrieval
- similarity scoring

Additional name-specific normalization includes standardizing common textual variations where applicable.

## 4.3 Address Normalization

Addresses are also normalized before candidate generation and matching.

The normalized address is used for:

- address token extraction
- candidate retrieval
- similarity scoring

Normalization reduces differences caused by punctuation, spacing, capitalization, and other formatting variations.

---

# 5. Blocking and Candidate Generation

## 5.1 Why Blocking Is Required

A naive approach would compare every Source 1 entity with every Source 2 and Source 3 entity.

For a large dataset, this would create an extremely large Cartesian product.

It would also require expensive fuzzy-similarity calculations for a very large number of unlikely pairs.

Blocking addresses this problem by generating a smaller set of plausible candidate pairs before detailed matching.

Conceptually:

```text
Source 1 entity
       |
       v
Normalized fields
       |
       v
Blocking / candidate lookup
       |
       v
Candidate entity IDs
       |
       v
Detailed similarity scoring
```

This makes the overall entity-resolution process substantially more scalable.

---

# 6. Primary Candidate Generation

The final V2 primary candidate pool combines two complementary sources of evidence:

1. exact normalized candidates
2. rare/informative token candidates

## 6.1 Exact Candidates

Exact normalized evidence provides a high-confidence and inexpensive way to retrieve candidate records.

Candidates supported by exact normalized name/address evidence are included in the primary candidate pool.

Exact candidate generation is useful because many records may represent the same entity even when their original raw values differ only through formatting.

## 6.2 Rare / Informative Token Candidates

Normalized business names and addresses are tokenized.

Token frequency information is used to identify relatively rare and informative tokens.

Rare tokens are useful as blocking keys because they generally correspond to a smaller subset of reference records than very common tokens.

The conceptual process is:

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

Name-derived and address-derived candidates are combined.

Duplicate Source 1/candidate pairs are removed before scoring.

## 6.3 Primary Candidate Pool Size

The final V2 primary candidate pool contained:

```text
46,277,162 candidate pairs
```

covering:

```text
1,578,910 Source 1 entities
```

This candidate pool is substantially smaller than an exhaustive comparison of all possible Source 1/reference pairs.

---

# 7. Primary Similarity Features

After candidate generation, each candidate pair is evaluated using textual similarity.

The final V2 pipeline uses two primary similarity features.

## 7.1 Name Similarity

Jaro-Winkler similarity is calculated between:

- the normalized Source 1 business name
- the normalized candidate business name

This provides a continuous measure of textual similarity and allows small variations in spelling and formatting.

## 7.2 Address Similarity

Jaro-Winkler similarity is also calculated between:

- the normalized Source 1 address
- the normalized candidate address

The address similarity provides complementary evidence to the business name.

Together, name and address similarity provide the main evidence used for candidate ranking and final matching.

---

# 8. Primary Candidate Scoring

The primary candidate score is calculated as:

```text
primary_score =
    0.60 × name_similarity
  + 0.40 × address_similarity
```

The primary score gives:

- 60% weight to business-name similarity
- 40% weight to address similarity

The purpose of this score is to rank candidates and identify the strongest candidate records for each Source 1 entity.

---

# 9. Top-K Primary Candidate Selection

Candidates are ranked independently for each Source 1 entity.

Only the strongest 20 primary candidates are retained:

```text
Top-20 candidates per Source 1 entity
```

The ranking uses the primary score.

Deterministic tie-breaking is also applied using:

1. primary score
2. exact normalized name agreement
3. exact normalized address agreement
4. candidate ID

The Top-20 reduction substantially reduces the number of candidate pairs passed to subsequent processing.

---

# 10. Selective Fallback

Not every Source 1 entity requires a broader candidate search.

After primary candidate scoring, the best primary score for each Source 1 entity is examined.

An entity enters the fallback stage when:

```text
best_primary_score < 0.95
```

or when:

```text
no primary candidate exists
```

The fallback therefore focuses additional computation on entities for which the primary candidate-generation stage did not provide sufficiently strong evidence.

Conceptually:

```text
Primary candidates
       |
       v
Best primary score
       |
       +---- >= 0.95 ----> continue to final matching
       |
       +---- < 0.95 -----> fallback
       |
       +---- no candidate -> fallback
```

This selective design avoids applying the broader fallback search to every Source 1 entity.

---

# 11. Fallback Candidate Generation

The fallback stage uses medium-frequency tokens from normalized business names and addresses.

This provides broader candidate coverage than the rare-token primary search.

The fallback candidate-generation process is performed in batches of:

```text
10,000 Source 1 entities
```

Batch processing controls memory consumption during large-scale candidate generation.

Fallback candidates are scored and ranked.

The strongest:

```text
Top-50 candidates
```

are retained for each fallback Source 1 entity.

The retained fallback candidates are then combined with the relevant primary candidates before the final matching stage.

---

# 12. Why the Candidate Generation Scales

The candidate-generation design uses several mechanisms to control computational cost.

## 12.1 Blocking

Only plausible candidates retrieved through the blocking stage are passed to detailed similarity calculations.

This avoids exhaustive all-pairs comparison.

## 12.2 Exact Candidate Retrieval

Exact normalized evidence provides inexpensive candidate retrieval for strong textual agreements.

## 12.3 Token-Based Retrieval

Token indexes allow candidate records to be retrieved through informative name and address tokens instead of scanning the entire reference dataset.

## 12.4 Top-K Reduction

The primary stage retains only the Top-20 candidates per Source 1 entity.

The fallback stage retains only the Top-50 candidates per fallback entity.

This prevents large candidate pools from being passed unnecessarily into later stages.

## 12.5 Selective Fallback

The fallback search is performed only for entities with weak or missing primary evidence.

Strong primary cases do not require the additional fallback computation.

## 12.6 Batch Processing

Fallback candidate generation is processed in batches of 10,000 Source 1 entities.

This prevents the complete fallback search space from needing to be held in memory simultaneously.

---

# 13. Candidate Generation and Recall

Candidate generation is a critical stage because it determines the maximum possible recall of the downstream matching system.

If a true matching entity is not included in the candidate set, the later similarity-scoring stage cannot recover that match.

The final pipeline therefore uses complementary candidate-generation mechanisms:

```text
Exact evidence
      +
Rare/informative token evidence
      |
      v
Primary candidate pool
      |
      v
Selective fallback for difficult cases
      |
      v
Expanded candidate coverage
```

This separates the candidate-recall problem from the final precision-oriented matching decision.

---

# 14. Final Candidate Pool

The final matching stage combines relevant primary and fallback candidates.

Candidate pairs are deduplicated before final scoring.

This ensures that the same Source 1/candidate pair is not evaluated multiple times simply because it was retrieved through more than one candidate-generation mechanism.

The combined candidate pool provides the final set of entities that can potentially be accepted as matches.

---

# 15. Final Matching Score

The final matching stage uses equal weighting between name and address similarity.

The final score is:

```text
final_score =
    0.50 × name_similarity
  + 0.50 × address_similarity
```

The final stage therefore gives equal importance to:

- business-name similarity
- address similarity

This score is used to rank the final candidate set and determine which candidates satisfy the acceptance criterion.

---

# 16. Final Matching Threshold

A candidate is accepted as a final match only when:

```text
final_score >= 0.850
```

Candidates below the threshold are not accepted.

This threshold prevents weak candidate pairs from being returned merely because they were retrieved during blocking.

The threshold also allows a Source 1 entity to have an empty final match when no candidate reaches the required similarity level.

Therefore:

```text
Candidate exists
       ≠
Candidate must be matched
```

Candidate generation identifies records worth considering, while the final threshold determines whether sufficient matching evidence exists.

---

# 17. No-Match Handling

A Source 1 entity may legitimately have no corresponding entity in the reference data.

The pipeline therefore does not force every Source 1 entity to match a candidate.

If all candidate pairs for an entity fall below the final acceptance threshold, that Source 1 entity remains unmatched.

This distinction is important because candidate generation and final matching represent two different decisions:

```text
Candidate generation:
"Which records are worth considering?"

Final matching:
"Which of those records have sufficient evidence to be accepted?"
```

---

# 18. Validation

Validation is performed at multiple levels before submission.

## 18.1 Matching Output Validation

The final matching output is checked for:

- duplicate Source 1/candidate pairs
- invalid Source 1 IDs
- invalid candidate IDs
- consistency of prediction counts
- correct representation of Source 1 entities

The final V2 matching integrity checks reported:

```text
Duplicate pairs:       0
Invalid Source 1 IDs:  0
Invalid candidate IDs: 0
```

## 18.2 Candidate Output Validation

The candidate output is checked for:

- correct number of data rows
- unique Source 1 IDs
- duplicate Source 1 rows
- malformed rows
- duplicate candidate IDs within individual rows

The final V2 candidate validation reported:

```text
Data rows:               1,732,544
Unique Source 1 IDs:     1,732,544
Duplicate Source 1 IDs: 0
Malformed rows:          0
Duplicate candidate IDs: 0
```

## 18.3 Prediction / Candidate Consistency

Every final prediction is checked against the corresponding candidate set.

A final prediction must exist among the candidates generated for that Source 1 entity.

The final V2 validation reported:

```text
Source 1 rows checked:        1,732,544
Predicted links checked:      5,030,669
Missing predicted links:      0
Missing Source 1 rows:        0
```

Therefore, every final predicted link is represented in the submitted candidate set.

---

# 19. Final V2 Statistics

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
| Fallback batch size | 10,000 Source 1 entities |
| Final score | 50% name + 50% address |
| Final acceptance threshold | 0.850 |

---

# 20. Final Configuration

The final validated V2 configuration is:

| Component | Configuration |
|---|---|
| Primary candidate generation | Exact + rare/informative token candidates |
| Primary scoring | 60% name + 40% address |
| Primary candidate limit | Top-20 |
| Fallback trigger | Best primary score < 0.95 or no primary candidate |
| Fallback candidate generation | Medium-frequency token candidates |
| Fallback candidate limit | Top-50 |
| Fallback batch size | 10,000 Source 1 entities |
| Final scoring | 50% name + 50% address |
| Final acceptance threshold | 0.850 |

---

# 21. Evaluation

The challenge uses Macro F0.5 as an important evaluation metric.

During development, the available training/ground-truth data can be used to evaluate the quality of candidate generation and matching decisions.

Evaluation should consider both:

- whether the correct entity is included among the generated candidates
- whether the final matching stage selects the correct entity

The final test set does not provide ground-truth labels, so the final test predictions cannot be independently scored against the unknown test labels.

The final validation and leaderboard results should be recorded below once the final submission has been evaluated.

```text
Validation Macro F0.5:
[TO BE UPDATED WITH FINAL VALIDATED VALUE]

Leaderboard score:
[TO BE UPDATED WITH FINAL SUBMISSION SCORE]
```

---

# 22. Output Files

## 22.1 `matching_results.tsv`

This file contains the final predictions.

The output contains one row for every Source 1 entity.

The expected fields are:

```text
source1_entity_id
matched_entity_ids
```

The `matched_entity_ids` field contains the accepted matching entity IDs.

An entity may have multiple accepted matching IDs.

An empty value represents a Source 1 entity for which no candidate satisfies the final matching criteria.

---

## 22.2 `candidate_pairs.tsv`

This file contains the candidate entity IDs considered by the matching pipeline.

The output contains one row for every Source 1 entity.

The expected fields are:

```text
source1_entity_id
candidate_entity_ids
```

The `candidate_entity_ids` field contains the candidate IDs generated by the blocking/candidate-generation stages.

Every final predicted entity must be present in the candidate set associated with the same Source 1 entity.

---

# 23. Reproducibility

The final V2 execution is preserved in the project notebook and the submitted source implementation.

The intended execution flow is:

```text
1. Load Source 1, Source 2 and Source 3 data
2. Preprocess and normalize the records
3. Generate primary candidates
4. Score primary candidates
5. Retain Top-20 candidates per Source 1 entity
6. Identify entities requiring fallback
7. Generate fallback candidates
8. Score fallback candidates
9. Retain Top-50 fallback candidates
10. Combine relevant primary and fallback candidates
11. Apply the final matching score
12. Apply the final acceptance threshold
13. Generate candidate_pairs.tsv
14. Generate matching_results.tsv
15. Validate the generated outputs
```

The Python dependencies required by the final implementation are listed in:

```text
requirements.txt
```

They can be installed using:

```bash
pip install -r requirements.txt
```

The submitted implementation should use the same configuration documented in this file when generating the final outputs.

---

# 24. Source Code Organization

The source implementation is organized into separate stages.

### `preprocessing.py`

Contains data cleaning and normalization logic.

### `blocking.py`

Contains candidate-generation and blocking logic.

### `features.py`

Contains similarity-feature calculations.

### `matching.py`

Contains candidate scoring, fallback logic, thresholding, and final match selection.

### `generate_submission.py`

Connects the pipeline stages and generates the final output files.

The final implementation should represent the validated pipeline rather than superseded experimental approaches.

---

# 25. Methodology Summary

The final solution uses a two-stage candidate-generation and matching architecture.

The major design decisions are:

1. Normalize business names and addresses before comparison.
2. Avoid exhaustive pairwise comparison through blocking.
3. Combine exact and informative token-based candidate generation.
4. Use Jaro-Winkler similarity for normalized business names and addresses.
5. Rank primary candidates using a 60/40 name-address score.
6. Retain only the Top-20 primary candidates.
7. Identify difficult entities using the primary confidence score.
8. Apply a selective fallback search only to those difficult entities.
9. Use medium-frequency token candidates in the fallback stage.
10. Process fallback candidates in batches to control memory usage.
11. Retain the Top-50 fallback candidates.
12. Combine primary and fallback candidates before final selection.
13. Use an equal-weight 50/50 name-address score for final matching.
14. Accept only candidates with a final score of at least 0.850.
15. Allow valid empty matches when no candidate satisfies the threshold.
16. Validate candidate-file integrity.
17. Validate final matching integrity.
18. Verify that every final prediction is present in its corresponding candidate set.

The resulting architecture separates candidate retrieval from final matching, allowing the solution to process a large entity-resolution dataset while restricting detailed similarity calculations to plausible candidate pairs.

---

# 26. Final Submission Checklist

Before submitting the project, verify the following:

- [ ] `README.md` is present.
- [ ] `Documentation_template.md` is present.
- [ ] Source code reflects the final validated pipeline.
- [ ] `requirements.txt` contains the dependencies required by the submitted implementation.
- [ ] `matching_results.tsv` has the required format.
- [ ] `candidate_pairs.tsv` has the required format.
- [ ] Every Source 1 entity is represented in the required output.
- [ ] There are no duplicate Source 1 rows.
- [ ] There are no malformed output rows.
- [ ] Candidate IDs are valid.
- [ ] Final predicted IDs are valid.
- [ ] Every final predicted entity occurs in the corresponding candidate set.
- [ ] Final thresholds in the documentation match the submitted code.
- [ ] Final validation results have been recorded.
- [ ] Final leaderboard score has been recorded after submission.
