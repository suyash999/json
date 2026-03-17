"""
═══════════════════════════════════════════════════════════════════════
TEXT PREPROCESSING — Handles negation, contractions, cleaning, NLP
═══════════════════════════════════════════════════════════════════════
"""

import re
import string
import numpy as np
import pandas as pd

from config.theme_mappings import CONTRACTIONS, NEGATION_WORDS, CUSTOM_STOPWORDS


def expand_contractions(text: str) -> str:
    """Expand contractions: can't → cannot, don't → do not, etc."""
    for contraction, expansion in CONTRACTIONS.items():
        text = re.sub(
            r'\b' + re.escape(contraction) + r'\b',
            expansion,
            text,
            flags=re.IGNORECASE
        )
    return text


def handle_negations(text: str) -> str:
    """
    Mark negated words with NEG_ prefix.
    'not happy with the service' → 'not NEG_happy NEG_with NEG_the NEG_service'
    This preserves negation context for theme detection.
    """
    words = text.split()
    result = []
    negate = False
    for i, word in enumerate(words):
        if word.lower() in NEGATION_WORDS:
            negate = True
            result.append(word)
            continue
        # End negation at punctuation
        if negate and any(p in word for p in ['.', ',', '!', '?', ';', ':']):
            negate = False
            result.append(word)
            continue
        if negate:
            result.append(f"NEG_{word}")
            # Negate max 3 words after negation word
            if len([w for w in result if w.startswith("NEG_")]) >= 3:
                negate = False
        else:
            result.append(word)
    return ' '.join(result)


def clean_text(text: str, remove_negation_markers: bool = False) -> str:
    """
    Full text cleaning pipeline:
    1. Lowercase
    2. Expand contractions
    3. Handle negations
    4. Remove URLs, emails, special chars
    5. Normalize whitespace
    """
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()
    text = expand_contractions(text)

    # Remove URLs
    text = re.sub(r'http\S+|www\.\S+', ' ', text)
    # Remove email addresses
    text = re.sub(r'\S+@\S+', ' ', text)
    # Remove order/item numbers
    text = re.sub(r'#?\d{6,}', ' ', text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # Handle negations BEFORE removing punctuation
    text = handle_negations(text)

    # Remove punctuation but keep negation markers
    text = re.sub(r'[^\w\s_]', ' ', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    if remove_negation_markers:
        text = text.replace("NEG_", "")

    return text


def remove_stopwords(text: str) -> str:
    """Remove custom stopwords while preserving negation markers."""
    words = text.split()
    filtered = [
        w for w in words
        if w.lower().replace("neg_", "") not in CUSTOM_STOPWORDS
        and len(w) > 2
    ]
    return ' '.join(filtered)


def preprocess_series(series: pd.Series) -> pd.Series:
    """Apply full preprocessing pipeline to a pandas Series."""
    return (
        series
        .fillna('')
        .astype(str)
        .apply(clean_text)
        .apply(remove_stopwords)
    )


def extract_ngrams(texts: list, n: int = 2, top_k: int = 20) -> list:
    """Extract top-k n-grams from a list of texts."""
    from collections import Counter
    ngram_counts = Counter()
    for text in texts:
        words = text.split()
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            if not any(w.startswith("NEG_") for w in ngram.split()):
                ngram_counts[ngram] += 1
    return ngram_counts.most_common(top_k)


def detect_language_quality(text: str) -> dict:
    """Basic text quality metrics."""
    words = text.split()
    return {
        "word_count": len(words),
        "char_count": len(text),
        "avg_word_length": np.mean([len(w) for w in words]) if words else 0,
        "has_negation": any(w in text.lower() for w in NEGATION_WORDS),
        "exclamation_count": text.count('!'),
        "question_marks": text.count('?'),
        "caps_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1),
    }
