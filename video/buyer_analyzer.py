"""
Buyer Analyzer
==============
Builds real-time buyer profiles and detects shill bidding patterns.

Tracks per-buyer:
- Comment frequency & timing
- Bid history & price escalation
- Engagement patterns
- Shill risk scoring

Shill Detection Signals:
1. Rapid-fire bidding (many bids in short window)
2. Strategic price inflation (bids always push price up significantly)
3. Bid-then-vanish (bids aggressively but never wins)
4. Late-entry aggression (only appears during bidding wars)
5. Coordinated patterns (multiple accounts bidding in relay)
6. Low engagement ratio (only bids, no general chat)
"""

import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import math


class BuyerProfile:
    """Tracks all behavior for a single buyer."""
    
    def __init__(self, username: str):
        self.username = username
        self.comments: List[Dict] = []
        self.bids: List[Dict] = []      # {"timestamp": float, "amount": float}
        self.first_seen: float = 0.0
        self.last_seen: float = 0.0
        self.intents: List[str] = []
        self._interest_scores: List[float] = []
    
    def add_comment(self, comment: Dict):
        """Register a new comment from this buyer."""
        self.comments.append(comment)
        self.last_seen = comment["timestamp"]
        
        if not self.first_seen:
            self.first_seen = comment["timestamp"]
        
        if comment.get("is_bid") and comment.get("bid_amount"):
            self.bids.append({
                "timestamp": comment["timestamp"],
                "amount": comment["bid_amount"],
            })
        
        self.intents.append(comment.get("intent", "general"))
        self._interest_scores.append(comment.get("interest_score", 0))
    
    @property
    def comment_count(self) -> int:
        return len(self.comments)
    
    @property
    def bid_count(self) -> int:
        return len(self.bids)
    
    @property
    def avg_bid(self) -> float:
        if not self.bids:
            return 0.0
        return sum(b["amount"] for b in self.bids) / len(self.bids)
    
    @property
    def max_bid(self) -> float:
        if not self.bids:
            return 0.0
        return max(b["amount"] for b in self.bids)
    
    @property
    def min_bid(self) -> float:
        if not self.bids:
            return 0.0
        return min(b["amount"] for b in self.bids)
    
    @property
    def interest_score(self) -> float:
        """Average interest level across all comments."""
        if not self._interest_scores:
            return 0.0
        # Weight recent scores more heavily
        weights = [1.0 + i * 0.1 for i in range(len(self._interest_scores))]
        weighted = sum(s * w for s, w in zip(self._interest_scores, weights))
        return min(1.0, weighted / sum(weights))
    
    @property
    def engagement_duration(self) -> float:
        """How long this buyer has been active (seconds)."""
        return max(0, self.last_seen - self.first_seen)
    
    @property
    def bid_to_comment_ratio(self) -> float:
        """Ratio of bids to total comments. High ratio = suspicious."""
        if self.comment_count == 0:
            return 0.0
        return self.bid_count / self.comment_count
    
    @property
    def avg_bid_interval(self) -> float:
        """Average time between consecutive bids (seconds)."""
        if len(self.bids) < 2:
            return float("inf")
        intervals = [
            self.bids[i+1]["timestamp"] - self.bids[i]["timestamp"]
            for i in range(len(self.bids) - 1)
        ]
        return sum(intervals) / len(intervals) if intervals else float("inf")
    
    @property
    def price_escalation_rate(self) -> float:
        """Average % increase between consecutive bids."""
        if len(self.bids) < 2:
            return 0.0
        escalations = []
        for i in range(1, len(self.bids)):
            prev = self.bids[i-1]["amount"]
            curr = self.bids[i]["amount"]
            if prev > 0:
                escalations.append((curr - prev) / prev)
        return sum(escalations) / len(escalations) if escalations else 0.0
    
    def get_behavior_tag(self) -> str:
        """Classify buyer behavior type."""
        if self.bid_count == 0:
            if self.comment_count <= 2:
                return "lurker"
            if self.interest_score > 0.6:
                return "enthusiast"
            return "observer"
        
        if self.bid_to_comment_ratio > 0.8:
            return "pure_bidder"
        if self.bid_count > 5 and self.avg_bid_interval < 10:
            return "aggressive_bidder"
        if self.interest_score > 0.5 and self.bid_count > 0:
            return "engaged_bidder"
        
        return "casual_bidder"


class BuyerAnalyzer:
    """
    Analyzes buyer behavior across all participants and detects shill bidding.
    """
    
    def __init__(
        self,
        bid_freq_threshold: int = 5,
        price_jump_threshold: int = 15,
        shill_window: float = 60.0,
    ):
        """
        Args:
            bid_freq_threshold: Number of bids in a short window to flag as suspicious
            price_jump_threshold: % price increase to flag as suspicious
            shill_window: Time window (seconds) for frequency analysis
        """
        self.bid_freq_threshold = bid_freq_threshold
        self.price_jump_threshold = price_jump_threshold / 100.0
        self.shill_window = shill_window
        
        self.profiles: Dict[str, BuyerProfile] = {}
        self._global_bid_history: List[Dict] = []  # All bids across all buyers
        self._shill_alerts: List[Dict] = []
    
    def process_comment(self, comment: Dict):
        """Process a single parsed comment."""
        username = comment.get("username", "unknown")
        
        if username not in self.profiles:
            self.profiles[username] = BuyerProfile(username)
        
        self.profiles[username].add_comment(comment)
        
        # Track global bid history
        if comment.get("is_bid") and comment.get("bid_amount"):
            self._global_bid_history.append({
                "username": username,
                "timestamp": comment["timestamp"],
                "amount": comment["bid_amount"],
            })
            
            # Run shill detection after each bid
            self._check_shill_signals(username)
    
    def _check_shill_signals(self, username: str):
        """
        Check if a buyer exhibits shill bidding signals.
        Updates shill alerts in real-time.
        """
        profile = self.profiles.get(username)
        if not profile or profile.bid_count < 2:
            return
        
        reasons = []
        risk_score = 0.0
        
        # Signal 1: Rapid-fire bidding
        recent_bids = [
            b for b in profile.bids
            if profile.last_seen - b["timestamp"] < self.shill_window
        ]
        if len(recent_bids) >= self.bid_freq_threshold:
            reasons.append(
                f"Rapid bidding: {len(recent_bids)} bids in {self.shill_window:.0f}s window"
            )
            risk_score += 0.25
        
        # Signal 2: Strategic price inflation
        if profile.price_escalation_rate > self.price_jump_threshold:
            reasons.append(
                f"Price inflation: avg {profile.price_escalation_rate:.0%} increase per bid"
            )
            risk_score += 0.25
        
        # Signal 3: High bid-to-comment ratio (only bids, no chat)
        if profile.bid_to_comment_ratio > 0.7 and profile.comment_count >= 3:
            reasons.append(
                f"Low engagement: {profile.bid_to_comment_ratio:.0%} of messages are bids"
            )
            risk_score += 0.15
        
        # Signal 4: Very fast bid intervals
        if profile.avg_bid_interval < 8.0 and profile.bid_count >= 3:
            reasons.append(
                f"Machine-gun bidding: avg {profile.avg_bid_interval:.1f}s between bids"
            )
            risk_score += 0.2
        
        # Signal 5: Bid-then-vanish (bids but never follows up with engagement)
        bid_intents = sum(1 for i in profile.intents if i == "bid")
        other_intents = sum(1 for i in profile.intents if i != "bid")
        if bid_intents >= 3 and other_intents == 0:
            reasons.append("Bid-only account: no engagement besides bidding")
            risk_score += 0.2
        
        # Signal 6: Late-entry aggression
        if profile.bids and profile.first_seen > 0:
            # Check if buyer appeared late and immediately started bidding
            time_to_first_bid = profile.bids[0]["timestamp"] - profile.first_seen
            if time_to_first_bid < 3.0 and profile.bid_count >= 2:
                reasons.append(
                    f"Late-entry aggression: started bidding within {time_to_first_bid:.1f}s of appearing"
                )
                risk_score += 0.1
        
        # Signal 7: Coordinated relay bidding
        risk_score += self._check_relay_pattern(username) * 0.25
        
        # Normalize
        risk_score = min(1.0, risk_score)
        
        if risk_score > 0.3 and reasons:
            # Update or create alert
            existing = next(
                (a for a in self._shill_alerts if a["username"] == username), None
            )
            if existing:
                existing["risk_score"] = risk_score
                existing["reasons"] = reasons
                existing["bid_count"] = profile.bid_count
                existing["avg_bid_interval"] = profile.avg_bid_interval
                existing["min_bid"] = profile.min_bid
                existing["max_bid"] = profile.max_bid
            else:
                self._shill_alerts.append({
                    "username": username,
                    "risk_score": risk_score,
                    "reasons": reasons,
                    "bid_count": profile.bid_count,
                    "avg_bid_interval": profile.avg_bid_interval,
                    "min_bid": profile.min_bid,
                    "max_bid": profile.max_bid,
                })
    
    def _check_relay_pattern(self, username: str) -> float:
        """
        Check if this buyer is part of a coordinated relay bidding pattern.
        
        Relay = two or more accounts taking turns bidding back-and-forth
        to drive up the price.
        
        Returns a score 0-1 indicating relay suspicion.
        """
        if len(self._global_bid_history) < 4:
            return 0.0
        
        # Look at recent global bids
        recent = self._global_bid_history[-20:]
        
        # Find sequences where this user alternates with another
        user_bids = [b for b in recent if b["username"] == username]
        if len(user_bids) < 2:
            return 0.0
        
        # Check for A-B-A-B pattern
        partner_counts = defaultdict(int)
        for i in range(len(recent) - 1):
            if recent[i]["username"] == username:
                next_bidder = recent[i + 1]["username"]
                if next_bidder != username:
                    partner_counts[next_bidder] += 1
        
        if partner_counts:
            max_alternations = max(partner_counts.values())
            if max_alternations >= 3:
                return 0.8
            elif max_alternations >= 2:
                return 0.4
        
        return 0.0
    
    def unique_buyer_count(self) -> int:
        """Number of distinct buyers seen."""
        return len(self.profiles)
    
    def get_profiles(self) -> Dict:
        """Get all buyer profiles as serializable dicts."""
        result = {}
        for username, profile in self.profiles.items():
            result[username] = {
                "comment_count": profile.comment_count,
                "bid_count": profile.bid_count,
                "avg_bid": profile.avg_bid,
                "max_bid": profile.max_bid,
                "min_bid": profile.min_bid,
                "interest_score": profile.interest_score,
                "shill_score": self._get_shill_score(username),
                "first_seen": profile.first_seen,
                "last_seen": profile.last_seen,
                "behavior_tag": profile.get_behavior_tag(),
                "bid_to_comment_ratio": profile.bid_to_comment_ratio,
                "avg_bid_interval": profile.avg_bid_interval if profile.avg_bid_interval != float("inf") else 0,
                "engagement_duration": profile.engagement_duration,
            }
        return result
    
    def _get_shill_score(self, username: str) -> float:
        """Get shill risk score for a buyer."""
        alert = next(
            (a for a in self._shill_alerts if a["username"] == username), None
        )
        return alert["risk_score"] if alert else 0.0
    
    def get_shill_alerts(self) -> List[Dict]:
        """Get all current shill bidding alerts."""
        return sorted(self._shill_alerts, key=lambda a: a["risk_score"], reverse=True)
    
    def get_active_bidders(self, window: float = 60.0) -> List[str]:
        """Get buyers who have bid recently."""
        if not self._global_bid_history:
            return []
        latest = self._global_bid_history[-1]["timestamp"]
        return list(set(
            b["username"] for b in self._global_bid_history
            if latest - b["timestamp"] < window
        ))
    
    def get_bid_timeline(self) -> List[Dict]:
        """Get full bid history with buyer info."""
        return self._global_bid_history.copy()
    
    def get_summary_stats(self) -> Dict:
        """Get aggregate statistics."""
        profiles = list(self.profiles.values())
        bidders = [p for p in profiles if p.bid_count > 0]
        
        return {
            "total_buyers": len(profiles),
            "active_bidders": len(bidders),
            "total_bids": sum(p.bid_count for p in profiles),
            "avg_bids_per_bidder": (
                sum(p.bid_count for p in bidders) / len(bidders) if bidders else 0
            ),
            "highest_bid": max((p.max_bid for p in profiles), default=0),
            "shill_alerts": len(self._shill_alerts),
            "high_risk_buyers": sum(
                1 for a in self._shill_alerts if a["risk_score"] > 0.7
            ),
        }
