"""
═══════════════════════════════════════════════════════════════════════
THEME MODELLING ENGINE — Exhaustive eBay Theme Mappings
═══════════════════════════════════════════════════════════════════════
Pre-built mappings for eBay customer interactions. Users can edit these.
"""

# ─── EXHAUSTIVE GRANULAR THEMES ─────────────────────────────────────
# These are the fine-grained themes detected by BERT clustering
GRANULAR_THEMES = {
    # ── Shipping & Delivery ──
    "shipping_delay": {
        "keywords": ["late", "delay", "delayed", "slow", "hasn't arrived", "not arrived",
                     "still waiting", "where is my", "tracking stuck", "no movement",
                     "taking too long", "days late", "overdue", "expected delivery",
                     "not delivered", "never came", "lost in transit", "missing package"],
        "uber_theme": "Shipping & Delivery"
    },
    "shipping_damaged": {
        "keywords": ["damaged", "broken", "crushed", "dented", "cracked", "smashed",
                     "torn", "ripped", "bent", "scratched", "shattered", "water damage",
                     "packaging damage", "arrived damaged", "box crushed"],
        "uber_theme": "Shipping & Delivery"
    },
    "shipping_wrong_address": {
        "keywords": ["wrong address", "delivered elsewhere", "wrong location",
                     "neighbor received", "different address", "misdelivered",
                     "left at wrong", "wrong door", "wrong house"],
        "uber_theme": "Shipping & Delivery"
    },
    "shipping_tracking": {
        "keywords": ["tracking number", "tracking info", "track my", "tracking update",
                     "no tracking", "tracking not working", "tracking shows",
                     "tracking says", "usps tracking", "fedex tracking", "ups tracking"],
        "uber_theme": "Shipping & Delivery"
    },
    "shipping_cost": {
        "keywords": ["shipping cost", "shipping fee", "shipping price", "expensive shipping",
                     "free shipping", "shipping charge", "postage cost", "delivery fee",
                     "shipping too much", "overcharged shipping"],
        "uber_theme": "Shipping & Delivery"
    },
    "shipping_international": {
        "keywords": ["international shipping", "customs", "duties", "import tax",
                     "cross border", "overseas", "foreign", "global shipping",
                     "customs hold", "customs delay", "import fees"],
        "uber_theme": "Shipping & Delivery"
    },
    "shipping_method": {
        "keywords": ["expedited", "priority", "standard shipping", "overnight",
                     "express shipping", "economy shipping", "shipping speed",
                     "faster shipping", "upgrade shipping", "shipping option"],
        "uber_theme": "Shipping & Delivery"
    },

    # ── Returns & Refunds ──
    "return_request": {
        "keywords": ["return", "send back", "return label", "return shipping",
                     "want to return", "how to return", "return policy",
                     "return window", "return deadline", "return process"],
        "uber_theme": "Returns & Refunds"
    },
    "refund_request": {
        "keywords": ["refund", "money back", "get my money", "reimburse",
                     "credit back", "full refund", "partial refund",
                     "refund status", "where is my refund", "refund pending",
                     "refund not received", "refund denied"],
        "uber_theme": "Returns & Refunds"
    },
    "return_damaged": {
        "keywords": ["return damaged", "item broke", "defective return",
                     "faulty product return", "broken item return", "damaged goods"],
        "uber_theme": "Returns & Refunds"
    },
    "return_wrong_item": {
        "keywords": ["wrong item", "not what I ordered", "different item",
                     "sent wrong", "incorrect item", "not as described return",
                     "received wrong", "wrong product", "wrong color", "wrong size"],
        "uber_theme": "Returns & Refunds"
    },
    "refund_timing": {
        "keywords": ["how long refund", "refund timeline", "when will I get refund",
                     "refund processing", "refund takes", "waiting for refund",
                     "slow refund", "refund delay"],
        "uber_theme": "Returns & Refunds"
    },

    # ── Payments & Billing ──
    "payment_failed": {
        "keywords": ["payment failed", "payment declined", "card declined",
                     "transaction failed", "cannot pay", "payment error",
                     "payment not going through", "rejected payment", "payment issue"],
        "uber_theme": "Payments & Billing"
    },
    "payment_method": {
        "keywords": ["paypal", "credit card", "debit card", "payment method",
                     "apple pay", "google pay", "payment option", "how to pay",
                     "add payment", "change payment", "update card"],
        "uber_theme": "Payments & Billing"
    },
    "billing_overcharge": {
        "keywords": ["overcharged", "charged twice", "double charge", "extra charge",
                     "wrong amount", "incorrect charge", "billing error",
                     "unexpected charge", "hidden fee", "charged more"],
        "uber_theme": "Payments & Billing"
    },
    "payment_hold": {
        "keywords": ["payment hold", "funds held", "money on hold", "pending payment",
                     "payment pending", "hold on funds", "authorization hold",
                     "temporary hold", "ebay hold"],
        "uber_theme": "Payments & Billing"
    },
    "invoice_receipt": {
        "keywords": ["invoice", "receipt", "billing statement", "transaction history",
                     "purchase history", "order confirmation", "payment receipt",
                     "proof of purchase"],
        "uber_theme": "Payments & Billing"
    },

    # ── Product Issues ──
    "product_not_as_described": {
        "keywords": ["not as described", "different from listing", "misleading",
                     "false advertising", "inaccurate description", "doesn't match",
                     "not what was shown", "photo different", "listing wrong"],
        "uber_theme": "Product Issues"
    },
    "product_defective": {
        "keywords": ["defective", "doesn't work", "not working", "faulty",
                     "malfunction", "broken on arrival", "dead on arrival",
                     "stopped working", "not functioning", "quality issue"],
        "uber_theme": "Product Issues"
    },
    "product_counterfeit": {
        "keywords": ["fake", "counterfeit", "not authentic", "not genuine",
                     "knockoff", "replica", "not original", "bootleg",
                     "fraudulent product", "not real"],
        "uber_theme": "Product Issues"
    },
    "product_missing_parts": {
        "keywords": ["missing parts", "incomplete", "parts missing", "not complete",
                     "accessories missing", "missing component", "missing piece",
                     "not all included", "partial order"],
        "uber_theme": "Product Issues"
    },
    "product_quality": {
        "keywords": ["poor quality", "cheap", "low quality", "bad quality",
                     "flimsy", "thin", "fragile", "not durable", "fell apart",
                     "poor materials", "cheap material"],
        "uber_theme": "Product Issues"
    },

    # ── Account & Security ──
    "account_access": {
        "keywords": ["can't login", "locked out", "forgot password", "reset password",
                     "account suspended", "account restricted", "can't access",
                     "login issue", "sign in problem", "authentication"],
        "uber_theme": "Account & Security"
    },
    "account_hacked": {
        "keywords": ["hacked", "unauthorized", "someone accessed", "compromised",
                     "suspicious activity", "didn't make this purchase",
                     "account stolen", "identity theft", "fraud on account"],
        "uber_theme": "Account & Security"
    },
    "account_settings": {
        "keywords": ["change email", "update phone", "change address",
                     "update profile", "notification settings", "preferences",
                     "account settings", "personal info"],
        "uber_theme": "Account & Security"
    },
    "account_verification": {
        "keywords": ["verify identity", "verification", "id verification",
                     "confirm identity", "two factor", "2fa", "security code",
                     "verification code"],
        "uber_theme": "Account & Security"
    },

    # ── Seller Issues ──
    "seller_communication": {
        "keywords": ["seller not responding", "no response from seller",
                     "seller ignoring", "can't contact seller", "seller communication",
                     "message seller", "seller unresponsive", "seller ghosting"],
        "uber_theme": "Seller Issues"
    },
    "seller_fraud": {
        "keywords": ["scam", "scammer", "fraudulent seller", "fake seller",
                     "seller fraud", "dishonest seller", "seller lie",
                     "deceptive seller", "seller cheat"],
        "uber_theme": "Seller Issues"
    },
    "seller_dispute": {
        "keywords": ["dispute", "open case", "escalate", "ebay guarantee",
                     "buyer protection", "money back guarantee", "claim",
                     "resolution center", "file complaint"],
        "uber_theme": "Seller Issues"
    },

    # ── Technical Issues ──
    "app_bug": {
        "keywords": ["app crash", "app not working", "glitch", "bug", "error",
                     "app freeze", "loading issue", "won't load", "blank page",
                     "technical issue", "site down", "website error"],
        "uber_theme": "Technical Issues"
    },
    "search_issue": {
        "keywords": ["search not working", "can't find", "search results wrong",
                     "filter not working", "sort not working", "no results"],
        "uber_theme": "Technical Issues"
    },
    "checkout_issue": {
        "keywords": ["checkout error", "can't checkout", "cart issue",
                     "add to cart problem", "checkout stuck", "order not placing",
                     "checkout page error"],
        "uber_theme": "Technical Issues"
    },

    # ── Promotions & Pricing ──
    "coupon_issue": {
        "keywords": ["coupon", "promo code", "discount code", "code not working",
                     "coupon expired", "coupon invalid", "promotion", "deal",
                     "sale price", "discount not applied"],
        "uber_theme": "Promotions & Pricing"
    },
    "price_discrepancy": {
        "keywords": ["price changed", "price different", "price higher",
                     "price mismatch", "charged different price", "listing price",
                     "price wrong", "price increase"],
        "uber_theme": "Promotions & Pricing"
    },

    # ── Order Management ──
    "order_cancellation": {
        "keywords": ["cancel order", "cancellation", "cancel my order",
                     "don't want anymore", "changed my mind", "cancel purchase",
                     "stop order", "withdraw order"],
        "uber_theme": "Order Management"
    },
    "order_modification": {
        "keywords": ["change order", "modify order", "update order",
                     "change address on order", "change quantity",
                     "edit order", "amend order"],
        "uber_theme": "Order Management"
    },
    "order_status": {
        "keywords": ["order status", "where is my order", "order update",
                     "order progress", "order confirmation", "order placed",
                     "processing order", "pending order"],
        "uber_theme": "Order Management"
    },

    # ── Positive Feedback ──
    "positive_experience": {
        "keywords": ["great", "excellent", "amazing", "love it", "perfect",
                     "thank you", "awesome", "fantastic", "wonderful",
                     "satisfied", "happy with", "recommend", "best",
                     "impressed", "5 star", "fast delivery"],
        "uber_theme": "Positive Feedback"
    },
    "positive_seller": {
        "keywords": ["great seller", "excellent seller", "best seller",
                     "seller was helpful", "responsive seller",
                     "seller went above", "recommend seller"],
        "uber_theme": "Positive Feedback"
    },
}

# ─── UBER THEME DEFINITIONS ────────────────────────────────────────
# Normalization layer — maps granular themes to high-level categories
UBER_THEMES = {
    "Shipping & Delivery": {
        "description": "All issues related to shipping, delivery, tracking, and logistics",
        "color": "#3498db",
        "icon": "📦",
        "granular_themes": [
            "shipping_delay", "shipping_damaged", "shipping_wrong_address",
            "shipping_tracking", "shipping_cost", "shipping_international",
            "shipping_method"
        ]
    },
    "Returns & Refunds": {
        "description": "Return requests, refund processing, and exchange issues",
        "color": "#e74c3c",
        "icon": "↩️",
        "granular_themes": [
            "return_request", "refund_request", "return_damaged",
            "return_wrong_item", "refund_timing"
        ]
    },
    "Payments & Billing": {
        "description": "Payment processing, billing errors, payment methods, and holds",
        "color": "#2ecc71",
        "icon": "💳",
        "granular_themes": [
            "payment_failed", "payment_method", "billing_overcharge",
            "payment_hold", "invoice_receipt"
        ]
    },
    "Product Issues": {
        "description": "Product quality, authenticity, description accuracy, defects",
        "color": "#f39c12",
        "icon": "🏷️",
        "granular_themes": [
            "product_not_as_described", "product_defective",
            "product_counterfeit", "product_missing_parts", "product_quality"
        ]
    },
    "Account & Security": {
        "description": "Login issues, account security, verification, settings",
        "color": "#9b59b6",
        "icon": "🔐",
        "granular_themes": [
            "account_access", "account_hacked", "account_settings",
            "account_verification"
        ]
    },
    "Seller Issues": {
        "description": "Seller communication, disputes, fraud concerns",
        "color": "#e67e22",
        "icon": "🏪",
        "granular_themes": [
            "seller_communication", "seller_fraud", "seller_dispute"
        ]
    },
    "Technical Issues": {
        "description": "App bugs, website errors, checkout problems, search issues",
        "color": "#1abc9c",
        "icon": "🔧",
        "granular_themes": [
            "app_bug", "search_issue", "checkout_issue"
        ]
    },
    "Promotions & Pricing": {
        "description": "Coupon issues, pricing discrepancies, promotional offers",
        "color": "#fd79a8",
        "icon": "🏷️",
        "granular_themes": [
            "coupon_issue", "price_discrepancy"
        ]
    },
    "Order Management": {
        "description": "Order cancellation, modification, and status inquiries",
        "color": "#6c5ce7",
        "icon": "📋",
        "granular_themes": [
            "order_cancellation", "order_modification", "order_status"
        ]
    },
    "Positive Feedback": {
        "description": "Positive experiences, compliments, satisfaction",
        "color": "#00b894",
        "icon": "⭐",
        "granular_themes": [
            "positive_experience", "positive_seller"
        ]
    },
}

# ─── TONE / SENTIMENT MAPPINGS ──────────────────────────────────────
TONE_MAPPINGS = {
    "angry": {
        "keywords": ["furious", "angry", "outraged", "livid", "pissed",
                     "unacceptable", "ridiculous", "terrible", "worst",
                     "horrible", "disgusting", "pathetic", "incompetent",
                     "useless", "never again", "fed up", "sick of"],
        "label": "Angry / Frustrated",
        "severity": "high"
    },
    "frustrated": {
        "keywords": ["frustrated", "annoying", "irritating", "disappointed",
                     "upset", "unhappy", "dissatisfied", "inconvenient",
                     "hassle", "difficult", "complicated", "confusing",
                     "struggling", "tired of"],
        "label": "Frustrated / Disappointed",
        "severity": "medium"
    },
    "neutral": {
        "keywords": ["wondering", "question", "inquiry", "information",
                     "would like to know", "can you tell", "how do I",
                     "what is", "could you", "please help"],
        "label": "Neutral / Inquiry",
        "severity": "low"
    },
    "urgent": {
        "keywords": ["urgent", "emergency", "asap", "immediately",
                     "right now", "time sensitive", "critical",
                     "cannot wait", "need this today", "deadline"],
        "label": "Urgent / Time-Sensitive",
        "severity": "high"
    },
    "positive": {
        "keywords": ["thank", "thanks", "appreciate", "grateful",
                     "happy", "pleased", "satisfied", "great",
                     "excellent", "wonderful", "love", "amazing",
                     "fantastic", "perfect", "awesome"],
        "label": "Positive / Satisfied",
        "severity": "none"
    },
    "confused": {
        "keywords": ["confused", "don't understand", "unclear",
                     "makes no sense", "why", "how come",
                     "lost", "not sure", "help me understand"],
        "label": "Confused / Unclear",
        "severity": "medium"
    },
    "threatening": {
        "keywords": ["lawyer", "legal action", "sue", "attorney",
                     "bbb", "better business", "report", "authorities",
                     "file complaint", "consumer protection",
                     "social media", "go public"],
        "label": "Threatening / Escalation",
        "severity": "critical"
    },
}

# ─── POLICY CHANGE INDICATORS ──────────────────────────────────────
POLICY_INDICATORS = {
    "policy_complaint": {
        "keywords": ["used to be", "policy changed", "new policy", "old policy",
                     "before you could", "no longer", "changed the rules",
                     "updated terms", "policy update", "terms changed",
                     "wasn't like this before", "changed recently"],
        "label": "Policy Change Complaint",
        "category": "policy_change"
    },
    "policy_confusion": {
        "keywords": ["what is the policy", "policy unclear", "confused about policy",
                     "don't understand the policy", "where can I find policy",
                     "policy says", "according to policy", "read the policy"],
        "label": "Policy Confusion",
        "category": "policy_awareness"
    },
    "policy_suggestion": {
        "keywords": ["should change", "should allow", "should update",
                     "you should", "would be better if", "suggestion",
                     "recommend changing", "please consider", "feedback on policy"],
        "label": "Policy Suggestion",
        "category": "policy_feedback"
    },
    "fee_complaint": {
        "keywords": ["seller fees", "listing fees", "final value fee",
                     "fee increase", "too many fees", "fee structure",
                     "payment processing fee", "hidden fees"],
        "label": "Fee Complaint",
        "category": "policy_fees"
    },
}

# ─── NEGATION PATTERNS ─────────────────────────────────────────────
# Used in text preprocessing to handle negation properly
NEGATION_WORDS = [
    "not", "no", "never", "neither", "nobody", "nothing",
    "nowhere", "nor", "cannot", "can't", "don't", "doesn't",
    "didn't", "won't", "wouldn't", "shouldn't", "couldn't",
    "isn't", "aren't", "wasn't", "weren't", "hasn't", "haven't",
    "hadn't", "barely", "hardly", "scarcely", "seldom", "rarely",
]

# Common contractions to expand
CONTRACTIONS = {
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "hasn't": "has not",
    "haven't": "have not",
    "hadn't": "had not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "i'm": "i am",
    "i've": "i have",
    "i'll": "i will",
    "i'd": "i would",
    "you're": "you are",
    "you've": "you have",
    "you'll": "you will",
    "they're": "they are",
    "they've": "they have",
    "they'll": "they will",
    "we're": "we are",
    "we've": "we have",
    "it's": "it is",
    "that's": "that is",
    "there's": "there is",
    "here's": "here is",
    "what's": "what is",
    "who's": "who is",
    "where's": "where is",
    "let's": "let us",
}

# ─── STOPWORDS TO REMOVE ──────────────────────────────────────────
CUSTOM_STOPWORDS = [
    "ebay", "hi", "hello", "dear", "please", "thanks", "thank",
    "regards", "sincerely", "order", "item", "product", "thing",
    "stuff", "lot", "really", "very", "much", "also", "just",
    "like", "get", "got", "going", "go", "one", "would", "could",
    "said", "told", "asked", "called", "emailed", "contacted",
]
