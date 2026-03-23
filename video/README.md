# 🔍 eBay Live Stream Analyzer

Real-time auction stream intelligence — 100% local, zero cost.

Processes recorded live-stream auction videos to extract buyer chat, detect shill bidding, analyze conversation themes, and capture product images — all running on your machine with no API keys or cloud services.

---

## Features

### 💬 Chat Theme Analysis
- Extracts topics from buyer comments using TF-IDF + NMF
- Named themes with keyword clouds (e.g., "Pricing", "Card Quality", "Bid War")
- Real-time theme strength scoring
- Sentiment distribution tracking

### 👥 Buyer Behavior Dashboard
- Distinct buyer identification and profiling
- Interest scoring per buyer
- Engagement metrics: comment frequency, bid counts, activity duration
- Behavior classification: lurker, observer, enthusiast, casual/aggressive/pure bidder

### 🚨 Shill Bidding Detection
- **Rapid-fire bidding**: Flags accounts placing many bids in short windows
- **Strategic price inflation**: Detects bids that consistently push prices up
- **Bid-only accounts**: Flags accounts that only bid with zero general engagement
- **Late-entry aggression**: Detects accounts that appear and immediately start bidding
- **Relay bidding**: Identifies A-B-A-B coordinated bid patterns between accounts
- Real-time risk scoring (0–100%) per buyer

### 📦 Product/Card Capture
- Automatic scene-change detection for new products
- Frame stability check before capture (avoids blurry mid-transition shots)
- Quality filtering (brightness, sharpness)
- Timestamped product catalog

---

## Architecture

```
Video File
    │
    ├──► VideoProcessor (OpenCV)
    │        │
    │        ├──► Chat Region Crop ──► OCR Engine (EasyOCR/Tesseract)
    │        │                              │
    │        │                              ▼
    │        │                         CommentParser
    │        │                          │         │
    │        │                          ▼         ▼
    │        │                    BuyerAnalyzer  ThemeAnalyzer
    │        │                    (profiles +    (TF-IDF + NMF)
    │        │                     shill detect)
    │        │
    │        └──► Product Region Crop ──► ProductDetector
    │                                     (scene change + histogram)
    │
    └──► [Optional] LLM Engine (llama-cpp-python)
              Periodic batch analysis every 30-60s
```

**Processing rates (Apple Silicon / CPU):**
- OCR: ~1.5 FPS (configurable 0.5–5.0)
- Product detection: ~0.5 FPS (configurable 0.1–2.0)
- Theme extraction: every ~10 OCR cycles (near-instant via TF-IDF)
- LLM analysis: every 30–60s (optional)

---

## Setup

### 1. Prerequisites

- Python 3.9+
- macOS (Apple Silicon) or Linux/Windows with Python

### 2. Install Dependencies

```bash
# Clone or download this directory
cd ebay_stream_analyzer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install core dependencies
pip install -r requirements.txt
```

### 3. (Optional) Install Local LLM Support

For Apple Silicon with Metal acceleration:
```bash
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
```

For CPU only:
```bash
pip install llama-cpp-python
```

Download a model (GGUF format):
- **TinyLlama-1.1B** (fastest, ~700MB): Best for quick summaries
- **Phi-3-mini-4k** (~2.3GB): Best quality/speed balance
- **Mistral-7B-Q4** (~4GB): Highest quality, needs 8GB+ RAM

Models available on Hugging Face — search for GGUF versions.

### 4. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Usage Guide

### Step 1: Upload Video
Upload any recorded auction stream (MP4, AVI, MOV, MKV, WebM, FLV).

### Step 2: Configure Chat Region
In the sidebar under "Chat Region", adjust the percentage coordinates to match where the chat overlay appears in your video:
- **Typical eBay Live**: Left 65%, Top 10%, Right 100%, Bottom 90%
- **Facebook Live**: Left 0%, Top 60%, Right 50%, Bottom 95%
- **YouTube Live**: Left 60%, Top 5%, Right 100%, Bottom 85%

Use the Video Feed tab to preview the first frame and find the right region.

### Step 3: Tune Settings
- **OCR sample rate**: Higher = more comments captured, more CPU usage
- **Scene change sensitivity**: Lower = more products captured (may include false positives)
- **Shill detection thresholds**: Adjust based on auction intensity

### Step 4: Start Analysis
Click "Start Analysis" and watch the dashboards populate in real-time.

---

## Module Reference

| Module | File | Purpose |
|--------|------|---------|
| Video Processor | `video_processor.py` | OpenCV frame extraction |
| OCR Engine | `ocr_engine.py` | EasyOCR/Tesseract text extraction |
| Comment Parser | `comment_parser.py` | Structure raw OCR into comments |
| Buyer Analyzer | `buyer_analyzer.py` | Profiles, shill detection |
| Theme Analyzer | `theme_analyzer.py` | TF-IDF + NMF topic modeling |
| Product Detector | `product_detector.py` | Scene-change product capture |
| LLM Engine | `llm_engine.py` | Optional local LLM analysis |

---

## Customization

### Adding New Shill Detection Signals
Edit `buyer_analyzer.py` → `_check_shill_signals()`. Each signal contributes a weighted score (0–0.25) to the overall risk.

### Adding Theme Templates
Edit `theme_analyzer.py` → `THEME_TEMPLATES` dict. Add new keyword groups to improve theme naming.

### Supporting New Chat Formats
Edit `comment_parser.py` → `USERNAME_PATTERNS` list. Add regex patterns for different stream platform chat formats.

---

## Performance Notes

| Component | Apple M1/M2 | Intel i7 | Notes |
|-----------|------------|----------|-------|
| OCR (EasyOCR) | ~0.3s/frame | ~0.5s/frame | First call slower (model load) |
| Theme Analysis | <50ms | <50ms | TF-IDF is very fast |
| Product Detection | <10ms | <10ms | Histogram comparison |
| LLM (TinyLlama) | ~2 tok/s | ~1 tok/s | Optional, batch only |
| LLM (Phi-3-mini) | ~5 tok/s (Metal) | ~1.5 tok/s | Metal acceleration helps |

Memory usage: ~500MB base + ~200MB per hour of video + LLM model size.

---

## License

MIT — Use freely, no attribution required.
