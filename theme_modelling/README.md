# 🎯 Theme Modelling Engine — Setup & Deployment Guide

## What This Is

A complete Streamlit-based NLP analytics platform for customer feedback theme analysis. Built for eBay-style data but works with any customer feedback dataset.

### Features
- **Tab 1 — EDA**: Auto-detects column types (numeric, text, date, categorical, boolean) and generates charts
- **Tab 2 — Theme Analysis**: BERT embeddings + keyword matching + KMeans/HDBSCAN clustering. 40+ pre-built eBay themes
- **Tab 3 — Theme Normalization**: Map granular themes to uber themes. Pre-filled + user-editable. Handles cross-category overlap (e.g., "returns" appearing in both shipping and payments)
- **Tab 4 — Tone & Policy**: Sentiment/tone detection (angry, frustrated, urgent, threatening, etc.) + policy change indicator detection
- **Tab 5 — Visualizations**: Treemap, sunburst, heatmaps, time-series trends, confidence distributions. Downloadable final dataset

---

## Quick Start (Local)

### 1. Prerequisites
- Python 3.9+
- pip

### 2. Install
```bash
cd theme-engine
pip install -r requirements.txt
```

**Note on sentence-transformers:** This downloads a ~100MB BERT model on first run. If you're on a machine with limited resources, the app automatically falls back to keyword-only analysis.

### 3. Run
```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

### 4. Use
1. Upload your CSV/Excel/JSON in the sidebar
2. Tab 1: Review the auto-generated EDA, select the text column
3. Tab 2: Review pre-built mappings, optionally add custom ones, hit "Run Theme Analysis"
4. Tab 3: Review and fix any theme normalization issues
5. Tab 4: Review tone and policy detection, edit mappings
6. Tab 5: Explore the full visualization dashboard, download results

---

## Project Structure

```
theme-engine/
├── app.py                          # Main Streamlit app (all 5 tabs)
├── requirements.txt                # Python dependencies
├── config/
│   ├── __init__.py
│   └── theme_mappings.py           # Exhaustive eBay theme definitions:
│                                   #   - 40+ granular themes with keywords
│                                   #   - 10 uber theme categories
│                                   #   - Tone/sentiment mappings
│                                   #   - Policy change indicators
│                                   #   - Negation handling patterns
│                                   #   - Contraction expansion rules
│                                   #   - Custom stopwords
├── utils/
│   ├── __init__.py
│   ├── text_preprocessing.py       # NLP pipeline:
│   │                               #   - Contraction expansion
│   │                               #   - Negation handling (NEG_ marking)
│   │                               #   - URL/email/HTML removal
│   │                               #   - Stopword filtering
│   │                               #   - N-gram extraction
│   ├── theme_engine.py             # Core analysis engine:
│   │                               #   - BERT sentence embeddings
│   │                               #   - Keyword theme matching
│   │                               #   - KMeans / HDBSCAN clustering
│   │                               #   - Cluster summarization (TF-IDF)
│   │                               #   - Tone detection
│   │                               #   - Policy indicator detection
│   │                               #   - Confidence scoring
│   └── eda_engine.py               # Auto-EDA:
│                                   #   - Column type detection
│                                   #   - Histogram/box plots (numeric)
│                                   #   - Bar charts (categorical)
│                                   #   - Time series (datetime)
│                                   #   - Word count distributions (text)
│                                   #   - Correlation matrix
│                                   #   - Missing value analysis
```

---

## Deploy to Streamlit Cloud (Free)

1. Push the project to a GitHub repository:
   ```bash
   cd theme-engine
   git init
   git add .
   git commit -m "Theme engine v1"
   git remote add origin https://github.com/YOUR_USER/theme-engine.git
   git push -u origin main
   ```

2. Go to **https://share.streamlit.io**

3. Sign in with GitHub

4. Click **"New app"**:
   - Repository: `YOUR_USER/theme-engine`
   - Branch: `main`
   - Main file: `app.py`

5. Click **Deploy**

6. Your app will be live at: `https://YOUR_USER-theme-engine.streamlit.app`

**Important:** Streamlit Cloud has 1GB RAM on free tier. For large datasets (>50K rows), consider deploying on a paid tier or self-hosting.

---

## Deploy with Docker

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t theme-engine .
docker run -p 8501:8501 theme-engine
```

---

## How the Theme Engine Works

### Step 1: Text Preprocessing
- Expand contractions (can't → cannot)
- Handle negations (marks words after "not" with NEG_ prefix so "not happy" ≠ "happy")
- Remove URLs, emails, order numbers, HTML
- Remove custom eBay-specific stopwords

### Step 2: BERT Embeddings
- Uses `all-MiniLM-L6-v2` (lightweight, fast, 384-dim embeddings)
- Each text → 384-dimensional vector capturing semantic meaning
- Batched processing for performance

### Step 3: Hybrid Theme Assignment
- **Keyword matching**: Each text checked against 40+ theme keyword lists
- **BERT clustering**: KMeans or HDBSCAN groups semantically similar texts
- **Hybrid**: Use keyword match when confident (>0.2), fall back to cluster-derived theme
- **Confidence scoring**: Weighted score based on keyword matches and cluster probability

### Step 4: Theme Normalization
- Granular themes (e.g., "shipping_delay") → Uber themes (e.g., "Shipping & Delivery")
- Pre-filled mappings handle cross-category overlap
- Users can override any mapping via UI or bulk JSON

### Step 5: Enrichment
- **Tone detection**: 7 tone categories (angry, frustrated, neutral, urgent, positive, confused, threatening)
- **Policy indicators**: Detects mentions of policy changes, complaints, suggestions, fee issues
- **Severity scoring**: Critical / High / Medium / Low / None

### Output Columns Added
| Column | Description |
|--------|-------------|
| `key_theme` | Granular theme label |
| `uber_theme` | Normalized high-level theme |
| `theme_confidence` | 0-1 confidence score |
| `keyword_theme` | Theme from keyword matching |
| `keyword_confidence` | Keyword match confidence |
| `matched_keywords` | Which keywords matched |
| `cluster_id` | BERT cluster assignment |
| `cluster_confidence` | Cluster membership probability |
| `tone` | Detected tone/sentiment |
| `tone_severity` | Severity level |
| `tone_confidence` | Tone detection confidence |
| `policy_indicator` | Policy-related category |
| `policy_category` | Policy type |
| `policy_confidence` | Policy detection confidence |

---

## Customization

### Adding New Themes
Edit `config/theme_mappings.py`:
```python
GRANULAR_THEMES["my_new_theme"] = {
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "uber_theme": "Existing Uber Theme"  # or create new
}
```

### Adding New Uber Themes
```python
UBER_THEMES["My New Category"] = {
    "description": "Description here",
    "color": "#hexcolor",
    "icon": "🆕",
    "granular_themes": ["my_new_theme"]
}
```

### Changing the BERT Model
In `utils/theme_engine.py`, change the model name:
```python
# Faster but less accurate:
model_name = "all-MiniLM-L6-v2"

# More accurate but slower:
model_name = "all-mpnet-base-v2"
```

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'sentence_transformers'"**
→ Run: `pip install sentence-transformers`

**"CUDA out of memory"**
→ The app uses CPU by default. For GPU, set `device='cuda'` in `get_embeddings()`

**"App is slow with large datasets"**
→ Reduce `n_clusters`, use `kmeans` instead of `hdbscan`, or sample your data first

**"Themes aren't accurate enough"**
→ Add more keywords to `theme_mappings.py` or use the custom mapping UI in Tab 2/3

---

That's it! You have a complete, production-ready theme modelling engine. 🚀
