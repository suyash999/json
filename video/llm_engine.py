"""
LLM Engine (Optional)
=====================
Integrates a local LLM via llama-cpp-python for deeper analysis.

Designed for periodic batch analysis (not real-time per-comment).
Optimized for Apple Silicon via Metal acceleration.

Supported models (GGUF format):
- TinyLlama-1.1B (fastest, good enough for summaries)
- Phi-3-mini-4k (best quality/speed trade-off)
- Mistral-7B-Q4 (highest quality, needs 8GB+ RAM)

This module is entirely optional — the app works fully without it.
"""

from typing import List, Dict, Optional
import json


class LLMEngine:
    """
    Local LLM wrapper using llama-cpp-python.
    Provides periodic batch analysis of chat and buyer behavior.
    """
    
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_threads: int = 4,
        n_gpu_layers: int = -1,  # -1 = auto (Metal on macOS)
    ):
        """
        Args:
            model_path: Path to GGUF model file
            n_ctx: Context window size
            n_threads: CPU threads to use
            n_gpu_layers: GPU layers (-1 for auto/Metal)
        """
        self.model_path = model_path
        self._llm = None
        
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
            )
        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed. Install with: "
                "CMAKE_ARGS='-DLLAMA_METAL=on' pip install llama-cpp-python"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def _generate(self, prompt: str, max_tokens: int = 300) -> str:
        """Generate text from prompt."""
        if self._llm is None:
            return ""
        
        try:
            output = self._llm(
                prompt,
                max_tokens=max_tokens,
                temperature=0.3,
                top_p=0.9,
                stop=["</analysis>", "\n\n\n"],
                echo=False,
            )
            return output["choices"][0]["text"].strip()
        except Exception as e:
            return f"[LLM Error: {e}]"
    
    def analyze_chat_batch(
        self, comments: List[Dict], buyer_profiles: Dict
    ) -> str:
        """
        Analyze a batch of recent comments with buyer context.
        
        Args:
            comments: Recent parsed comments
            buyer_profiles: Current buyer profile data
            
        Returns:
            Analysis text summary
        """
        if not comments:
            return ""
        
        # Build a compact context
        chat_lines = []
        for c in comments[-30:]:  # Last 30 comments max
            bid_tag = f" [BID ${c['bid_amount']}]" if c.get("is_bid") else ""
            chat_lines.append(f"{c.get('username', '?')}: {c.get('text', '')}{bid_tag}")
        
        chat_text = "\n".join(chat_lines)
        
        # High-risk buyers
        shill_suspects = [
            f"{u} (risk: {p.get('shill_score', 0):.0%})"
            for u, p in buyer_profiles.items()
            if p.get("shill_score", 0) > 0.3
        ]
        
        prompt = f"""You are analyzing a live auction stream chat. Provide a brief, actionable analysis.

RECENT CHAT:
{chat_text}

FLAGGED BUYERS: {', '.join(shill_suspects) if shill_suspects else 'None'}

Analyze in 3-4 sentences:
1. What's the dominant mood/sentiment?
2. Are there any coordinated or suspicious patterns?
3. What product/item is generating the most interest?
<analysis>"""
        
        return self._generate(prompt, max_tokens=200)
    
    def classify_shill_behavior(
        self, username: str, profile: Dict, recent_bids: List[Dict]
    ) -> Dict:
        """
        Use LLM to provide nuanced shill assessment for a specific buyer.
        
        Returns:
            Dict with "assessment", "confidence", "reasoning"
        """
        bid_history = ", ".join(
            f"${b['amount']} @ {b['timestamp']:.0f}s" for b in recent_bids[-10:]
        )
        
        prompt = f"""Analyze this auction buyer's behavior for shill bidding indicators.

BUYER: {username}
STATS: {json.dumps(profile, default=str)}
BID HISTORY: {bid_history}

Is this buyer likely a shill? Answer with:
- ASSESSMENT: (clean/suspicious/likely_shill)
- CONFIDENCE: (low/medium/high)
- REASONING: (1-2 sentences)
<analysis>"""
        
        response = self._generate(prompt, max_tokens=150)
        
        # Parse structured response
        result = {"assessment": "unknown", "confidence": "low", "reasoning": response}
        
        response_lower = response.lower()
        if "likely_shill" in response_lower or "likely shill" in response_lower:
            result["assessment"] = "likely_shill"
        elif "suspicious" in response_lower:
            result["assessment"] = "suspicious"
        elif "clean" in response_lower:
            result["assessment"] = "clean"
        
        if "high" in response_lower:
            result["confidence"] = "high"
        elif "medium" in response_lower:
            result["confidence"] = "medium"
        
        return result
    
    def summarize_themes(self, themes: List, comment_sample: List[str]) -> str:
        """
        Generate a natural-language summary of detected themes.
        """
        theme_text = "\n".join(
            f"- {name}: {', '.join(kw)} (strength: {score:.0%})"
            for name, kw, score in themes
        )
        
        sample = "\n".join(comment_sample[:15])
        
        prompt = f"""Summarize the conversation themes in this live auction chat.

DETECTED THEMES:
{theme_text}

SAMPLE COMMENTS:
{sample}

Write a 2-3 sentence summary of what buyers are talking about and what's driving engagement:
<analysis>"""
        
        return self._generate(prompt, max_tokens=150)
    
    @property
    def is_available(self) -> bool:
        """Check if LLM is loaded and ready."""
        return self._llm is not None
