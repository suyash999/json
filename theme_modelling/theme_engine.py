"""
═══════════════════════════════════════════════════════════════════════
THEME MODELLING ENGINE — BERT + Clustering + Keyword Hybrid
═══════════════════════════════════════════════════════════════════════
Uses sentence-transformers for embeddings, HDBSCAN/KMeans for clustering,
and keyword matching for theme assignment with confidence scoring.
"""

import numpy as np
import pandas as pd
from collections import Counter

from config.theme_mappings import (
    GRANULAR_THEMES, UBER_THEMES, TONE_MAPPINGS, POLICY_INDICATORS
)
from utils.text_preprocessing import clean_text, preprocess_series


def get_embeddings(texts: list, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64):
    """Generate BERT sentence embeddings."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return embeddings


def keyword_match_theme(text: str) -> tuple:
    """
    Match text against keyword-based themes.
    Returns (theme_id, confidence, matched_keywords).
    """
    text_lower = text.lower()
    best_theme = None
    best_score = 0
    best_keywords = []

    for theme_id, theme_data in GRANULAR_THEMES.items():
        matched = [kw for kw in theme_data["keywords"] if kw in text_lower]
        score = len(matched)
        # Weight longer keyword matches higher
        weighted_score = sum(len(kw.split()) for kw in matched)

        if weighted_score > best_score:
            best_score = weighted_score
            best_theme = theme_id
            best_keywords = matched

    # Calculate confidence
    if best_score == 0:
        return ("unclassified", 0.0, [])

    max_possible = max(
        sum(len(kw.split()) for kw in td["keywords"])
        for td in GRANULAR_THEMES.values()
    )
    confidence = min(best_score / max(max_possible * 0.15, 1), 1.0)

    return (best_theme, confidence, best_keywords)


def detect_tone(text: str) -> tuple:
    """Detect tone/sentiment of text using keyword matching."""
    text_lower = text.lower()
    best_tone = "neutral"
    best_score = 0

    for tone_id, tone_data in TONE_MAPPINGS.items():
        matched = [kw for kw in tone_data["keywords"] if kw in text_lower]
        score = len(matched)
        if score > best_score:
            best_score = score
            best_tone = tone_id

    tone_data = TONE_MAPPINGS.get(best_tone, TONE_MAPPINGS["neutral"])
    confidence = min(best_score / 3.0, 1.0)
    return (tone_data["label"], tone_data["severity"], confidence)


def detect_policy_indicator(text: str) -> tuple:
    """Check if text mentions policy-related issues."""
    text_lower = text.lower()
    for indicator_id, ind_data in POLICY_INDICATORS.items():
        matched = [kw for kw in ind_data["keywords"] if kw in text_lower]
        if matched:
            confidence = min(len(matched) / 2.0, 1.0)
            return (ind_data["label"], ind_data["category"], confidence)
    return ("None", "none", 0.0)


def cluster_texts(embeddings: np.ndarray, method: str = "kmeans", n_clusters: int = 10):
    """Cluster embeddings using KMeans or HDBSCAN."""
    if method == "hdbscan":
        try:
            import hdbscan
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=max(5, len(embeddings) // 50),
                min_samples=3,
                metric='cosine',
                cluster_selection_method='eom',
            )
            labels = clusterer.fit_predict(embeddings)
            probabilities = clusterer.probabilities_
            return labels, probabilities
        except ImportError:
            pass  # Fall back to KMeans

    from sklearn.cluster import KMeans
    n_clusters = min(n_clusters, max(2, len(embeddings) // 10))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    # Compute pseudo-probabilities from distances
    distances = kmeans.transform(embeddings)
    min_dist = distances.min(axis=1)
    probabilities = 1 - (min_dist / (min_dist.max() + 1e-10))
    return labels, probabilities


def get_cluster_summaries(
    texts: list,
    labels: np.ndarray,
    top_n_words: int = 8,
    examples: int = 3,
) -> dict:
    """Generate summaries for each cluster with top keywords and examples."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    summaries = {}
    unique_labels = sorted(set(labels))

    for label in unique_labels:
        if label == -1:
            continue  # Skip noise cluster from HDBSCAN

        mask = labels == label
        cluster_texts = [t for t, m in zip(texts, mask) if m]

        if len(cluster_texts) < 2:
            summaries[label] = {
                "size": len(cluster_texts),
                "keywords": [],
                "examples": cluster_texts[:examples],
            }
            continue

        # TF-IDF keywords for this cluster
        try:
            tfidf = TfidfVectorizer(
                max_features=200,
                stop_words='english',
                ngram_range=(1, 2),
                max_df=0.95,
                min_df=1,
            )
            tfidf_matrix = tfidf.fit_transform(cluster_texts)
            feature_names = tfidf.get_feature_names_out()
            mean_scores = tfidf_matrix.mean(axis=0).A1
            top_indices = mean_scores.argsort()[::-1][:top_n_words]
            top_keywords = [feature_names[i] for i in top_indices]
        except Exception:
            top_keywords = []

        # Get representative examples (closest to centroid conceptually)
        example_texts = cluster_texts[:examples]

        summaries[label] = {
            "size": len(cluster_texts),
            "keywords": top_keywords,
            "examples": example_texts,
        }

    return summaries


def run_theme_analysis(
    df: pd.DataFrame,
    text_column: str,
    user_theme_overrides: dict = None,
    n_clusters: int = 12,
    clustering_method: str = "kmeans",
) -> pd.DataFrame:
    """
    Full theme analysis pipeline:
    1. Preprocess text
    2. Generate BERT embeddings
    3. Keyword-based theme matching
    4. Cluster for discovering new themes
    5. Tone detection
    6. Policy indicator detection
    7. Combine with confidence scoring
    """

    result_df = df.copy()

    # ── Step 1: Preprocess ──
    cleaned_texts = preprocess_series(df[text_column])
    result_df['_cleaned_text'] = cleaned_texts
    raw_texts = df[text_column].fillna('').astype(str).tolist()

    # ── Step 2: BERT Embeddings ──
    non_empty_mask = cleaned_texts.str.len() > 0
    texts_for_embedding = cleaned_texts[non_empty_mask].tolist()

    if len(texts_for_embedding) == 0:
        return result_df

    embeddings = get_embeddings(texts_for_embedding)

    # ── Step 3: Keyword Theme Matching ──
    keyword_results = []
    for text in raw_texts:
        theme, conf, kws = keyword_match_theme(text)
        keyword_results.append({
            'keyword_theme': theme,
            'keyword_confidence': round(conf, 3),
            'matched_keywords': ', '.join(kws[:5]),
        })
    kw_df = pd.DataFrame(keyword_results)
    for col in kw_df.columns:
        result_df[col] = kw_df[col].values

    # ── Step 4: Clustering ──
    cluster_labels = np.full(len(df), -1)
    cluster_probs = np.zeros(len(df))

    if len(embeddings) >= 5:
        labels, probs = cluster_texts(
            embeddings,
            method=clustering_method,
            n_clusters=n_clusters,
        )
        cluster_labels[non_empty_mask] = labels
        cluster_probs[non_empty_mask] = probs

    result_df['cluster_id'] = cluster_labels
    result_df['cluster_confidence'] = np.round(cluster_probs, 3)

    # Get cluster summaries
    cluster_summaries = get_cluster_summaries(
        texts_for_embedding,
        cluster_labels[non_empty_mask],
    )

    # ── Step 5: Assign final themes ──
    # Use keyword match when confident, cluster otherwise
    final_themes = []
    uber_themes = []
    confidences = []

    # Apply user overrides
    effective_themes = dict(GRANULAR_THEMES)
    effective_uber = dict(UBER_THEMES)
    if user_theme_overrides:
        for k, v in user_theme_overrides.items():
            if k in effective_themes:
                effective_themes[k]["uber_theme"] = v

    for idx, row in result_df.iterrows():
        kw_theme = row.get('keyword_theme', 'unclassified')
        kw_conf = row.get('keyword_confidence', 0.0)

        if kw_conf >= 0.2 and kw_theme != 'unclassified':
            final_theme = kw_theme
            confidence = kw_conf
        else:
            # Use cluster label as fallback
            cid = row.get('cluster_id', -1)
            if cid in cluster_summaries:
                # Try to map cluster keywords to known themes
                cluster_kws = ' '.join(cluster_summaries[cid].get('keywords', []))
                mapped_theme, mapped_conf, _ = keyword_match_theme(cluster_kws)
                if mapped_conf > 0.1:
                    final_theme = mapped_theme
                    confidence = mapped_conf * 0.7  # Discount cluster-derived
                else:
                    final_theme = f"cluster_{cid}"
                    confidence = row.get('cluster_confidence', 0.3)
            else:
                final_theme = "unclassified"
                confidence = 0.1

        # Resolve uber theme
        theme_data = effective_themes.get(final_theme, {})
        uber = theme_data.get("uber_theme", "Other")

        final_themes.append(final_theme)
        uber_themes.append(uber)
        confidences.append(round(confidence, 3))

    result_df['key_theme'] = final_themes
    result_df['uber_theme'] = uber_themes
    result_df['theme_confidence'] = confidences

    # ── Step 6: Tone Detection ──
    tone_results = []
    for text in raw_texts:
        tone_label, severity, tone_conf = detect_tone(text)
        tone_results.append({
            'tone': tone_label,
            'tone_severity': severity,
            'tone_confidence': round(tone_conf, 3),
        })
    tone_df = pd.DataFrame(tone_results)
    for col in tone_df.columns:
        result_df[col] = tone_df[col].values

    # ── Step 7: Policy Indicators ──
    policy_results = []
    for text in raw_texts:
        pol_label, pol_cat, pol_conf = detect_policy_indicator(text)
        policy_results.append({
            'policy_indicator': pol_label,
            'policy_category': pol_cat,
            'policy_confidence': round(pol_conf, 3),
        })
    pol_df = pd.DataFrame(policy_results)
    for col in pol_df.columns:
        result_df[col] = pol_df[col].values

    # ── Clean up ──
    result_df.drop(columns=['_cleaned_text'], inplace=True, errors='ignore')

    return result_df, cluster_summaries
