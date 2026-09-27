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
