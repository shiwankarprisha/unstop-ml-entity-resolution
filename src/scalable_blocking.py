import re
import unicodedata
import pandas as pd


def normalize_for_blocking(text):
    """Normalize text while preserving Unicode letters and numbers."""

    if pd.isna(text):
        return ""

    text = unicodedata.normalize("NFKC", str(text).lower())

    cleaned = []

    for ch in text:
        category = unicodedata.category(ch)

        if (
            category.startswith("L")
            or category.startswith("N")
            or category.startswith("M")
        ):
            cleaned.append(ch)
        else:
            cleaned.append(" ")

    return " ".join("".join(cleaned).split())


def get_unique_tokens(text):
    """Return unique normalized tokens."""

    text = normalize_for_blocking(text)

    if not text:
        return set()

    return set(text.split())


def get_address_numbers(text):
    """Extract meaningful numeric components from an address."""

    text = normalize_for_blocking(text)

    # Avoid weak one-digit numbers such as 1, 2, 3
    return set(re.findall(r"\b\d{2,}\b", text))


def informative_tokens(text, frequency_map, max_frequency=5000):
    """
    Keep only tokens that are informative enough for blocking.
    """

    result = []

    for token in get_unique_tokens(text):

        frequency = frequency_map.get(token)

        if (
            frequency is not None
            and frequency <= max_frequency
        ):
            result.append(token)

    return result
