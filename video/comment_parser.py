"""
Comment Parser
==============
Parses raw OCR text lines into structured comment objects.
Handles common live-stream chat formats:
- "username: message"
- "username message"
- Bid detection ("$50", "50 dollars", "bid 50")
- Emoji and noise filtering
"""

import re
from typing import List, Dict, Optional, Set
from collections import defaultdict


# ── Patterns ─────────────────────────────────────────────────────────────────

# Common username:message separators in stream chats
USERNAME_PATTERNS = [
    # "username: message" or "username : message"
    re.compile(r"^([A-Za-z0-9_.\-]{2,25})\s*[:：]\s*(.+)$"),
    # "@username message"
    re.compile(r"^@([A-Za-z0-9_.\-]{2,25})\s+(.+)$"),
    # "username| message" (some platforms)
    re.compile(r"^([A-Za-z0-9_.\-]{2,25})\s*[|]\s*(.+)$"),
]

# Bid amount patterns
BID_PATTERNS = [
    # "$50" or "$ 50" or "$50.00"
    re.compile(r"\$\s?(\d+(?:\.\d{1,2})?)"),
    # "50 dollars" or "50 bucks"
    re.compile(r"(\d+(?:\.\d{1,2})?)\s*(?:dollars?|bucks?|usd)", re.IGNORECASE),
    # "bid 50" or "bid: 50" or "BID 50"
    re.compile(r"bid\s*:?\s*\$?\s*(\d+(?:\.\d{1,2})?)", re.IGNORECASE),
    # "i bid 50" or "my bid 50"
    re.compile(r"(?:i|my|ill?|i\'?ll)\s+bid\s+\$?\s*(\d+(?:\.\d{1,2})?)", re.IGNORECASE),
    # Just a number alone (if line is very short, likely a bid)
    re.compile(r"^(\d{1,5}(?:\.\d{1,2})?)$"),
]

# Interest signals (non-bid engagement)
INTEREST_KEYWORDS = {
    "want", "need", "love", "interested", "how much", "price",
    "mine", "dibs", "me", "sold", "deal", "take it",
    "beautiful", "nice", "amazing", "wow", "fire", "gem",
    "grail", "chase", "hit", "banger",
}

# Negative / disengagement signals
NEGATIVE_KEYWORDS = {
    "pass", "too much", "expensive", "nah", "no thanks",
    "skip", "overpriced", "not worth", "meh", "boring",
}

# Noise / non-informative patterns to skip
NOISE_PATTERNS = [
    re.compile(r"^[^a-zA-Z0-9]*$"),           # Only symbols/spaces
    re.compile(r"^.{0,2}$"),                    # Too short
    re.compile(r"^(hi|hello|hey|yo|sup)\s*$", re.IGNORECASE),  # Pure greetings (keep as comments but low value)
]


class CommentParser:
    """
    Parses raw OCR text into structured comment objects.
    
    Handles deduplication across frames (OCR often reads the same
    comments multiple times as they remain on screen).
    """
    
    def __init__(self, dedup_window: float = 5.0):
        """
        Args:
            dedup_window: Seconds within which duplicate text is suppressed.
        """
        self.dedup_window = dedup_window
        self._seen_texts: Dict[str, float] = {}  # normalized_text -> last_seen_timestamp
        self._comment_id = 0
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for dedup comparison."""
        return re.sub(r"\s+", " ", text.lower().strip())
    
    def _is_duplicate(self, text: str, timestamp: float) -> bool:
        """Check if we've seen this text recently."""
        normalized = self._normalize_text(text)
        if normalized in self._seen_texts:
            last_seen = self._seen_texts[normalized]
            if timestamp - last_seen < self.dedup_window:
                return True
        self._seen_texts[normalized] = timestamp
        
        # Cleanup old entries to prevent memory bloat
        if len(self._seen_texts) > 5000:
            cutoff = timestamp - self.dedup_window * 2
            self._seen_texts = {
                k: v for k, v in self._seen_texts.items() if v > cutoff
            }
        
        return False
    
    def _is_noise(self, text: str) -> bool:
        """Check if text is noise (too short, only symbols, etc)."""
        return any(p.match(text) for p in NOISE_PATTERNS)
    
    def _extract_username_message(self, text: str) -> tuple:
        """
        Try to split text into (username, message).
        Returns (None, text) if no username pattern found.
        """
        for pattern in USERNAME_PATTERNS:
            match = pattern.match(text)
            if match:
                return match.group(1), match.group(2)
        return None, text
    
    def _detect_bid(self, text: str) -> Optional[float]:
        """
        Detect if the message contains a bid and extract the amount.
        Returns the bid amount or None.
        """
        for pattern in BID_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    amount = float(match.group(1))
                    # Sanity check: bids typically between $1 and $99999
                    if 0.5 <= amount <= 99999:
                        return amount
                except ValueError:
                    continue
        return None
    
    def _detect_interest(self, text: str) -> float:
        """
        Score how much interest the message shows (0-1).
        """
        text_lower = text.lower()
        words = set(re.findall(r"\w+", text_lower))
        
        interest_hits = len(words & INTEREST_KEYWORDS)
        negative_hits = len(words & NEGATIVE_KEYWORDS)
        
        # Exclamation marks and caps suggest excitement
        excitement = min(text.count("!") * 0.1, 0.3) + (0.2 if text.isupper() and len(text) > 3 else 0)
        
        score = (interest_hits * 0.25 + excitement - negative_hits * 0.3)
        return max(0.0, min(1.0, score))
    
    def _classify_intent(self, text: str, bid_amount: Optional[float]) -> str:
        """Classify the comment's intent."""
        if bid_amount is not None:
            return "bid"
        
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ["how much", "price", "cost", "?"]):
            return "inquiry"
        if any(kw in text_lower for kw in NEGATIVE_KEYWORDS):
            return "disengagement"
        if any(kw in text_lower for kw in ["want", "need", "mine", "dibs", "take"]):
            return "intent_to_buy"
        if any(kw in text_lower for kw in ["love", "nice", "amazing", "wow", "fire", "beautiful"]):
            return "enthusiasm"
        if any(kw in text_lower for kw in ["fake", "scam", "shill", "rigged"]):
            return "suspicion"
        
        return "general"
    
    def parse_comments(
        self, raw_texts: List[str], timestamp: float
    ) -> List[Dict]:
        """
        Parse a batch of raw OCR text lines into structured comments.
        
        Args:
            raw_texts: List of text strings from OCR
            timestamp: Video timestamp in seconds
            
        Returns:
            List of comment dicts (deduplicated, noise-filtered)
        """
        comments = []
        
        for text in raw_texts:
            text = text.strip()
            
            # Skip noise
            if self._is_noise(text):
                continue
            
            # Skip duplicates
            if self._is_duplicate(text, timestamp):
                continue
            
            # Extract username and message
            username, message = self._extract_username_message(text)
            
            # Detect bid
            bid_amount = self._detect_bid(message)
            
            # Interest scoring
            interest = self._detect_interest(message)
            
            # Intent classification
            intent = self._classify_intent(message, bid_amount)
            
            self._comment_id += 1
            
            comment = {
                "id": self._comment_id,
                "timestamp": timestamp,
                "raw_text": text,
                "username": username or f"user_{hash(text) % 10000:04d}",
                "text": message,
                "is_bid": bid_amount is not None,
                "bid_amount": bid_amount,
                "interest_score": interest,
                "intent": intent,
                "has_username": username is not None,
            }
            
            comments.append(comment)
        
        return comments
    
    def reset(self):
        """Reset dedup cache and counters."""
        self._seen_texts.clear()
        self._comment_id = 0
