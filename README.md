# Unstop ML Entity Resolution

Business Entity Resolution solution for the Unstop ML Challenge.

## 1. Overview

This project performs large-scale business entity resolution across three independent data sources.

For each Source 1 entity, the pipeline identifies possible matching records from Source 2 and Source 3.

The pipeline consists of:

1. Data preprocessing and normalization
2. Candidate generation / blocking
3. Feature engineering
4. Candidate matching
5. Submission file generation

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
└── requirements.txt
```
## 3.Pipeline
Preprocessing

Business names and addresses are normalized before matching.

The preprocessing includes Unicode normalization, lowercase conversion, whitespace normalization, punctuation handling, and other field-specific cleaning steps.

Candidate Generation

Candidate records are retrieved using character-level TF-IDF similarity.

Candidates are generated independently using normalized business names and addresses and then combined with duplicate query-candidate pairs removed.

Feature Engineering

The matching stage uses:

Character-level name similarity
Name token overlap
Character-level address similarity
Address token overlap
Address number similarity
Country consistency
Matching

Candidate pairs are scored using a weighted combination of the matching features.

Candidates are then filtered using configurable matching thresholds, with stricter requirements for additional matches.

Output

The pipeline generates:

candidate_pairs.tsv
matching_results.tsv

Both files are tab-separated and contain one row for every Source 1 entity.

## 4.Source Code
The main pipeline modules are located under src/.

preprocessing.py — data normalization
blocking.py — candidate generation
features.py — feature engineering
matching.py — match scoring and selection
generate_submission.py — final TSV generation
## 5.Reproducibility
The pipeline is organized into modular source files under `src/`.

The end-to-end execution order is:

1. Preprocess the input records using `preprocessing.py`.
2. Generate candidate pairs using `blocking.py`.
3. Build matching features using `features.py`.
4. Score and select matches using `matching.py`.
5. Generate the final TSV files using `generate_submission.py`.

The exact final execution command and configuration will be updated after the final validated pipeline version is selected.
## 6.Output Files 
matching_results.tsv

Contains the final predicted matches for each Source 1 entity.
source1_entity_id
matched_entity_ids
candidate_pairs.tsv

Contains the candidate records considered by the matching stage for each Source 1 entity.
source1_entity_id
candidate_entity_ids
Every final matched entity should be present in the corresponding candidate set.
## 7.Dependencies
Python dependencies required by the pipeline are listed in:
requirements.txt
##. Final Configuration
The final model configuration, thresholds, validation results, and leaderboard score should be updated here after the final model version is selected and validated.
``` text

### ⚠️ Ek important correction

README me maine **final score ya final threshold nahi likha**. Ye jaan-bujhkar hai, because Bhagyashree abhi model improve kar rahi hai.

Final me ye section update hoga:

```text
Final Configuration

Model:
Threshold:
Candidate-generation configuration:
Validation F0.5:
Leaderboard score:

```
