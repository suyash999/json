"""
Theme Analyzer
==============
Real-time topic/theme extraction from buyer chat comments.

Uses lightweight NLP (TF-IDF + NMF) instead of heavy LLMs for speed.
Runs efficiently on CPU — processes thousands of comments in <100ms.

Outputs:
- Named themes with representative keywords
- Theme strength scores
- Theme evolution over time
"""

import re
from typing import List, Tuple, Dict, Optional
from collections import Counter


# ── Stopwords (expanded for auction/stream context) ──────────────────────────
STOPWORDS = {
    # Standard English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out",
    "off", "over", "under", "again", "further", "then", "once", "and",
    "but", "or", "nor", "not", "no", "so", "if", "than", "too", "very",
    "just", "about", "up", "down", "here", "there", "when", "where",
    "why", "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "only", "own", "same", "that", "this",
    "these", "those", "what", "which", "who", "whom", "its", "it",
    "he", "she", "they", "them", "their", "his", "her", "my", "your",
    "our", "i", "me", "we", "you", "him",
    # Stream/chat noise
    "lol", "lmao", "omg", "ok", "okay", "yeah", "yep", "nope",
    "haha", "hehe", "like", "gonna", "wanna", "gotta", "dont",
    "im", "ive", "its", "thats", "whats", "hes", "shes",
    "let", "get", "got", "go", "going", "come", "know", "think",
    "really", "actually", "literally", "basically",
}

# Theme name templates based on keyword clusters
THEME_TEMPLATES = {
    "pricing": ["price", "cost", "expensive", "cheap", "value", "worth", "deal", "money", "dollar", "buck"],
    "card_quality": ["mint", "grade", "psa", "condition", "raw", "graded", "slab", "centering", "surface"],
    "player_hype": ["goat", "legend", "star", "rookie", "auto", "signature", "autograph", "signed"],
    "bid_war": ["bid", "mine", "dibs", "want", "need", "sold", "going", "higher", "raise"],
    "product_reaction": ["fire", "heat", "banger", "hit", "chase", "gem", "beautiful", "amazing", "wow", "nice"],
    "skepticism": ["fake", "scam", "shill", "rigged", "suspicious", "overpriced", "ripoff", "cap"],
    "shipping": ["ship", "shipping", "delivery", "pack", "package", "mail", "send"],
    "collecting": ["collection", "collect", "pc", "personal", "keeper", "hold", "invest"],
}


class ThemeAnalyzer:
    """
    Extracts themes from chat comments using TF-IDF + NMF.
    Falls back to simple keyword frequency when scikit-learn unavailable.
    """
    
    def __init__(self, n_themes: int = 6, min_comments: int = 10):
        """
        Args:
            n_themes: Number of themes to extract
            min_comments: Minimum comments before attempting theme extraction
        """
        self.n_themes = n_themes
        self.min_comments = min_comments
        self._has_sklearn = False
        self._vectorizer = None
        self._nmf = None
        
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.decomposition import NMF
            self._has_sklearn = True
        except ImportError:
            pass
    
    def _clean_text(self, text: str) -> str:
        """Clean a single comment for analysis."""
        text = text.lower()
        text = re.sub(r"[^a-z\s]", " ", text)
        words = text.split()
        words = [w for w in words if w not in STOPWORDS and len(w) > 2]
        return " ".join(words)
    
    def _assign_theme_name(self, keywords: List[str]) -> str:
        """
        Try to assign a human-readable theme name based on keyword overlap
        with known templates. Falls back to top keywords.
        """
        keyword_set = set(keywords)
        
        best_match = None
        best_overlap = 0
        
        for theme_name, theme_words in THEME_TEMPLATES.items():
            overlap = len(keyword_set & set(theme_words))
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = theme_name
        
        if best_match and best_overlap >= 2:
            return best_match.replace("_", " ").title()
        
        # Fallback: use top 2 keywords
        return " & ".join(keywords[:2]).title() if keywords else "General"
    
    def extract_themes_sklearn(self, texts: List[str]) -> List[Tuple[str, List[str], float]]:
        """
        Extract themes using TF-IDF + NMF (Non-negative Matrix Factorization).
        
        Returns:
            List of (theme_name, keywords, strength_score)
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import NMF
        
        cleaned = [self._clean_text(t) for t in texts]
        cleaned = [t for t in cleaned if t.strip()]
        
        if len(cleaned) < self.min_comments:
            return []
        
        # TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=500,
            min_df=2,
            max_df=0.85,
            ngram_range=(1, 2),
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(cleaned)
        except ValueError:
            return []
        
        if tfidf_matrix.shape[1] < self.n_themes:
            return self.extract_themes_simple(texts)
        
        # NMF decomposition
        n_components = min(self.n_themes, tfidf_matrix.shape[1])
        nmf = NMF(
            n_components=n_components,
            random_state=42,
            max_iter=200,
            init="nndsvd",
        )
        
        try:
            W = nmf.fit_transform(tfidf_matrix)  # Document-topic matrix
            H = nmf.components_                     # Topic-term matrix
        except Exception:
            return self.extract_themes_simple(texts)
        
        feature_names = vectorizer.get_feature_names_out()
        
        themes = []
        for topic_idx, topic in enumerate(H):
            # Top keywords for this theme
            top_indices = topic.argsort()[-8:][::-1]
            keywords = [feature_names[i] for i in top_indices if topic[i] > 0.01]
            
            if not keywords:
                continue
            
            # Theme strength = proportion of documents where this is dominant
            dominant_docs = sum(1 for row in W if row.argmax() == topic_idx)
            strength = dominant_docs / max(len(cleaned), 1)
            
            theme_name = self._assign_theme_name(keywords)
            themes.append((theme_name, keywords[:6], strength))
        
        # Sort by strength
        themes.sort(key=lambda t: t[2], reverse=True)
        return themes
    
    def extract_themes_simple(self, texts: List[str]) -> List[Tuple[str, List[str], float]]:
        """
        Fallback theme extraction using simple keyword frequency + template matching.
        Used when scikit-learn is not available.
        """
        all_words = []
        for text in texts:
            cleaned = self._clean_text(text)
            all_words.extend(cleaned.split())
        
        if len(all_words) < 10:
            return []
        
        word_counts = Counter(all_words)
        total_words = len(all_words)
        
        # Match against theme templates
        themes = []
        for theme_name, theme_words in THEME_TEMPLATES.items():
            score = sum(word_counts.get(w, 0) for w in theme_words)
            if score >= 3:
                matched_keywords = [
                    w for w in theme_words if word_counts.get(w, 0) > 0
                ]
                matched_keywords.sort(key=lambda w: word_counts[w], reverse=True)
                strength = score / total_words
                themes.append((
                    theme_name.replace("_", " ").title(),
                    matched_keywords[:6],
                    min(1.0, strength * 10),
                ))
        
        # Add unmatched frequent words as "emerging" theme
        matched_words = set()
        for _, words_list in THEME_TEMPLATES.items():
            matched_words.update(words_list)
        
        unmatched = [
            (word, count) for word, count in word_counts.most_common(20)
            if word not in matched_words
        ]
        
        if unmatched and unmatched[0][1] >= 3:
            emerging_keywords = [w for w, c in unmatched[:6]]
            emerging_score = sum(c for _, c in unmatched[:6]) / total_words
            themes.append((
                "Emerging Topic",
                emerging_keywords,
                min(1.0, emerging_score * 10),
            ))
        
        themes.sort(key=lambda t: t[2], reverse=True)
        return themes[:self.n_themes]
    
    def extract_themes(self, texts: List[str]) -> List[Tuple[str, List[str], float]]:
        """
        Main entry point. Uses sklearn if available, falls back to simple method.
        
        Args:
            texts: List of comment text strings
            
        Returns:
            List of (theme_name, keywords_list, strength_score) tuples
        """
        if len(texts) < self.min_comments:
            return []
        
        if self._has_sklearn:
            return self.extract_themes_sklearn(texts)
        else:
            return self.extract_themes_simple(texts)
    
    def get_keyword_frequency(self, texts: List[str], top_n: int = 30) -> List[Tuple[str, int]]:
        """Get most frequent meaningful words across all comments."""
        all_words = []
        for text in texts:
            cleaned = self._clean_text(text)
            all_words.extend(cleaned.split())
        
        return Counter(all_words).most_common(top_n)
    
    def get_sentiment_distribution(self, texts: List[str]) -> Dict[str, float]:
        """
        Simple sentiment breakdown based on keyword matching.
        Returns distribution: positive, negative, neutral, excited.
        """
        positive = {"love", "great", "amazing", "nice", "beautiful", "awesome",
                     "fire", "heat", "gem", "banger", "deal", "good", "perfect"}
        negative = {"bad", "fake", "scam", "overpriced", "expensive", "terrible",
                     "ugly", "trash", "garbage", "worst", "rip", "ripoff"}
        excited = {"wow", "omg", "insane", "crazy", "unreal", "holy",
                   "incredible", "lets go", "yesss", "want", "need", "mine"}
        
        counts = {"positive": 0, "negative": 0, "neutral": 0, "excited": 0}
        
        for text in texts:
            words = set(re.findall(r"\w+", text.lower()))
            if words & excited:
                counts["excited"] += 1
            elif words & positive:
                counts["positive"] += 1
            elif words & negative:
                counts["negative"] += 1
            else:
                counts["neutral"] += 1
        
        total = max(sum(counts.values()), 1)
        return {k: v / total for k, v in counts.items()}
