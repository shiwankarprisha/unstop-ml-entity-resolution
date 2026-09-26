import re
import unicodedata
import pandas as pd


def normalize_name(text):
    """
    Normalize a business name while preserving Unicode characters.
    """

    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Standardize &
    text = text.replace("&", " and ")

    # Website cleanup
    text = re.sub(r"\bwww\.", "", text)
    text = re.sub(r"\.(com|in|org|net)\b", "", text)

    # Keep Unicode letters, numbers, combining marks and spaces
    cleaned = []

    for char in text:
        category = unicodedata.category(char)

        if (
            category.startswith("L")
            or category.startswith("N")
            or category.startswith("M")
            or char.isspace()
        ):
            cleaned.append(char)
        else:
            cleaned.append(" ")

    text = "".join(cleaned)

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_address(text):
    """
    Normalize a business address while preserving Unicode characters.
    """

    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    cleaned = []

    for char in text:
        category = unicodedata.category(char)

        if (
            category.startswith("L")
            or category.startswith("N")
            or category.startswith("M")
            or char.isspace()
        ):
            cleaned.append(char)
        else:
            # punctuation becomes whitespace
            cleaned.append(" ")

    text = "".join(cleaned)

    # Collapse repeated whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def preprocess_dataframe(df):
    """
    Add normalized name and address columns to a dataframe.

    Expected input columns:
        business_name
        business_address
    """

    df = df.copy()

    df["name_normalized"] = df["business_name"].apply(normalize_name)

    df["address_normalized"] = df["business_address"].apply(
        normalize_address
    )

    return df