"""
🎙️ Audio Intelligence Suite
─────────────────────────────────────────────────────────────
End-to-end audio analytics: transcription, speaker diarization,
tone analysis, theme extraction, policy detection & more.
100% open-source. No paid APIs required.
─────────────────────────────────────────────────────────────
"""

import streamlit as st
import os
import sys
import json
import tempfile
import time
import warnings
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

# ─── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="Audio Intelligence Suite",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&display=swap');

:root {
    --bg-dark: #0a0a0f;
    --surface: #12121a;
    --surface-2: #1a1a2e;
    --accent: #00d4aa;
    --accent-2: #7b61ff;
    --accent-3: #ff6b6b;
    --text: #e0e0e0;
    --text-muted: #888;
    --border: #2a2a3e;
}

.stApp { font-family: 'DM Sans', sans-serif; }

div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d15 0%, #12121a 100%);
    border-right: 1px solid var(--border);
}

.metric-card {
    background: linear-gradient(135deg, #12121a, #1a1a2e);
    border: 1px solid #2a2a3e;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00d4aa, #7b61ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label { color: #888; font-size: 0.85rem; margin-top: 4px; }

.speaker-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.speaker-0 { background: #00d4aa22; color: #00d4aa; border: 1px solid #00d4aa44; }
.speaker-1 { background: #7b61ff22; color: #7b61ff; border: 1px solid #7b61ff44; }
.speaker-2 { background: #ff6b6b22; color: #ff6b6b; border: 1px solid #ff6b6b44; }

.tone-positive { color: #00d4aa; }
.tone-negative { color: #ff6b6b; }
.tone-neutral { color: #ffd93d; }

.policy-flag-yes {
    background: #ff6b6b22; color: #ff6b6b; border: 1px solid #ff6b6b44;
    padding: 8px 16px; border-radius: 8px; font-weight: 700;
    display: inline-block;
}
.policy-flag-no {
    background: #00d4aa22; color: #00d4aa; border: 1px solid #00d4aa44;
    padding: 8px 16px; border-radius: 8px; font-weight: 700;
    display: inline-block;
}

.segment-block {
    background: #12121a;
    border-left: 3px solid #7b61ff;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
}

.theme-badge {
    display: inline-block;
    padding: 4px 12px;
    margin: 2px;
    border-radius: 20px;
    font-size: 0.8rem;
    background: #7b61ff22;
    color: #7b61ff;
    border: 1px solid #7b61ff44;
}

.header-glow {
    text-align: center;
    padding: 20px 0;
}
.header-glow h1 {
    font-size: 2.5rem;
    background: linear-gradient(135deg, #00d4aa, #7b61ff, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
}
.header-glow p { color: #888; font-size: 1rem; }

.env-ok { color: #00d4aa; }
.env-fail { color: #ff6b6b; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  ENVIRONMENT CHECKS — find ffmpeg on any OS
# ════════════════════════════════════════════════════════════

def find_ffmpeg():
    """
    Find ffmpeg binary. Returns the full path string or None.
    Checks: PATH, common Windows install locations, conda, imageio-ffmpeg, pydub.
    """
    # 1. Already on PATH?
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    # 2. Common Windows locations
    if sys.platform == "win32":
        candidates = []
        for env_var in ["LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"]:
            base = os.environ.get(env_var, "")
            if base:
                candidates.append(Path(base) / "ffmpeg" / "bin" / "ffmpeg.exe")
        candidates += [
            Path("C:/ffmpeg/bin/ffmpeg.exe"),
            Path("C:/tools/ffmpeg/bin/ffmpeg.exe"),
        ]
        # Conda
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if conda_prefix:
            candidates.append(Path(conda_prefix) / "Library" / "bin" / "ffmpeg.exe")
            candidates.append(Path(conda_prefix) / "bin" / "ffmpeg.exe")
        # Python's own folder
        candidates.append(Path(sys.executable).parent / "ffmpeg.exe")
        candidates.append(Path(sys.executable).parent / "Scripts" / "ffmpeg.exe")

        for c in candidates:
            try:
                if c.exists():
                    return str(c)
            except Exception:
                continue

    # 3. imageio-ffmpeg (pip install imageio-ffmpeg)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    return None


def ensure_ffmpeg_on_path():
    """
    Make sure ffmpeg is discoverable by subprocess calls.
    Also monkey-patches Whisper's audio loader to use the found binary.
    Returns (True, path) or (False, None).
    """
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        ffmpeg_dir = str(Path(ffmpeg).parent)
        # Add to PATH
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        # Monkey-patch Whisper's load_audio to use the full ffmpeg path.
        # This is a safety net — our main approach loads audio as numpy,
        # but this covers any edge case where Whisper still tries ffmpeg.
        try:
            import whisper.audio as _wa
            import numpy as np

            _original_load = getattr(_wa, "load_audio", None)

            def _patched_load_audio(file, sr=16000):
                """Load audio using the discovered ffmpeg binary."""
                try:
                    # Try scipy first (works for WAV without ffmpeg)
                    from scipy.io import wavfile
                    _sr, data = wavfile.read(file)
                    if data.dtype == np.int16:
                        data = data.astype(np.float32) / 32768.0
                    elif data.dtype == np.int32:
                        data = data.astype(np.float32) / 2147483648.0
                    else:
                        data = data.astype(np.float32)
                    if data.ndim > 1:
                        data = data[:, 0]
                    if _sr != sr:
                        duration = len(data) / _sr
                        target_len = int(duration * sr)
                        indices = np.linspace(0, len(data) - 1, target_len)
                        data = np.interp(indices, np.arange(len(data)), data).astype(np.float32)
                    return data
                except Exception:
                    pass
                # Fallback: use ffmpeg with full path
                cmd = [
                    ffmpeg, "-nostdin", "-threads", "0",
                    "-i", file,
                    "-f", "s16le", "-ac", "1", "-acodec", "pcm_s16le",
                    "-ar", str(sr), "-",
                ]
                out = subprocess.run(cmd, capture_output=True, check=True).stdout
                return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

            _wa.load_audio = _patched_load_audio
        except ImportError:
            pass  # Whisper not installed yet, will be patched on next call

        return True, ffmpeg
    return False, None


def check_ffmpeg_works(ffmpeg_path):
    """Verify ffmpeg actually runs."""
    try:
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def convert_audio_to_wav(input_path, output_path, ffmpeg_path="ffmpeg"):
    """Convert any audio file to 16kHz mono WAV using ffmpeg."""
    cmd = [
        ffmpeg_path, "-y", "-i", input_path,
        "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed:\n{result.stderr}")
    return output_path


# ════════════════════════════════════════════════════════════
#  MODEL LOADING (cached across reruns)
# ════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def load_whisper_model(model_size="base"):
    import whisper
    return whisper.load_model(model_size)


@st.cache_resource(show_spinner=False)
def load_sentiment_pipeline():
    from transformers import pipeline
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", top_k=None)


@st.cache_resource(show_spinner=False)
def load_zero_shot_pipeline():
    from transformers import pipeline
    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


@st.cache_resource(show_spinner=False)
def load_summarizer_pipeline():
    """
    Returns an extractive summarizer function (no model download needed).
    Uses TF-IDF sentence scoring — works on any transformers version.
    """
    def _extractive_summarize(text, max_length=150, min_length=30, **kwargs):
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer

        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if len(sentences) <= 3:
            return [{"summary_text": " ".join(sentences)}]

        # Score sentences by TF-IDF importance
        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(sentences)
            scores = np.asarray(tfidf_matrix.sum(axis=1)).flatten()
        except Exception:
            scores = np.array([len(s.split()) for s in sentences], dtype=float)

        # Boost early sentences (position bias — first sentences often most important)
        position_boost = np.array([1.0 / (i + 1) ** 0.5 for i in range(len(sentences))])
        combined = scores * 0.7 + position_boost * 0.3 * np.max(scores)

        # Pick top sentences, preserve original order
        target_words = max_length // 2  # rough word target
        ranked_indices = combined.argsort()[::-1]
        selected = []
        word_count = 0
        for idx in ranked_indices:
            words_in = len(sentences[idx].split())
            if word_count + words_in > target_words and word_count >= min_length // 2:
                break
            selected.append(idx)
            word_count += words_in
            if len(selected) >= 5:
                break

        selected.sort()  # preserve original order
        summary = " ".join(sentences[i] for i in selected)
        return [{"summary_text": summary}]

    return _extractive_summarize


@st.cache_resource(show_spinner=False)
def load_emotion_pipeline():
    from transformers import pipeline
    return pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)


# ════════════════════════════════════════════════════════════
#  AUDIO PROCESSING FUNCTIONS
# ════════════════════════════════════════════════════════════

def transcribe_audio(wav_path, model_size="base"):
    """
    Transcribe a 16kHz WAV using Whisper.
    CRITICAL: We load audio as numpy FIRST, then pass the array to Whisper.
    This bypasses Whisper's internal ffmpeg call (which fails on Windows
    when ffmpeg isn't on the system PATH).
    """
    import numpy as np
    import whisper

    model = load_whisper_model(model_size)

    # Load audio ourselves — no ffmpeg needed for WAV
    audio_np, sr = load_audio_numpy(wav_path)

    # Whisper expects float32 numpy at 16kHz
    # If sample rate doesn't match, resample
    if sr != 16000:
        # Simple linear interpolation resample
        duration = len(audio_np) / sr
        target_len = int(duration * 16000)
        indices = np.linspace(0, len(audio_np) - 1, target_len)
        audio_np = np.interp(indices, np.arange(len(audio_np)), audio_np)

    audio_np = audio_np.astype(np.float32)

    # Pad or trim to 30-second chunks is handled internally by whisper
    # Just pass the numpy array — whisper skips load_audio() when it gets an array
    return model.transcribe(audio_np, verbose=False, word_timestamps=True, task="transcribe")


def load_audio_numpy(wav_path):
    """Load 16kHz mono WAV → numpy float32. No ffmpeg needed."""
    import numpy as np
    from scipy.io import wavfile
    sr, data = wavfile.read(wav_path)
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    elif data.dtype != np.float32:
        data = data.astype(np.float32)
    if data.ndim > 1:
        data = data[:, 0]
    return data, sr


def simple_speaker_diarization(wav_path, num_speakers=2):
    """Spectral-feature KMeans diarization on a 16kHz WAV."""
    import numpy as np
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    y, sr = load_audio_numpy(wav_path)
    duration = len(y) / sr
    seg_dur = 2.0
    seg_samples = int(seg_dur * sr)
    n_segs = max(1, len(y) // seg_samples)

    features = []
    for i in range(n_segs):
        chunk = y[i * seg_samples : min((i + 1) * seg_samples, len(y))]
        if len(chunk) < 512:
            features.append(np.zeros(5))
            continue
        energy = np.sqrt(np.mean(chunk ** 2))
        zc = np.mean(np.abs(np.diff(np.sign(chunk))))
        spec = np.abs(np.fft.rfft(chunk))
        spec_sum = np.sum(spec) + 1e-8
        freqs = np.arange(len(spec))
        centroid = np.sum(freqs * spec) / spec_sum
        rolloff = np.searchsorted(np.cumsum(spec), 0.85 * np.sum(spec))
        bw = np.sqrt(np.sum(((freqs - centroid) ** 2) * spec) / spec_sum)
        features.append([energy, zc, centroid, rolloff, bw])

    features = np.array(features)
    if len(features) < num_speakers:
        return [{"start": 0, "end": duration, "speaker": 0}]

    labels = KMeans(n_clusters=num_speakers, random_state=42, n_init=10).fit_predict(
        StandardScaler().fit_transform(features)
    )

    segs = [{"start": i * seg_dur, "end": min((i + 1) * seg_dur, duration), "speaker": int(l)} for i, l in enumerate(labels)]
    merged = [segs[0]]
    for s in segs[1:]:
        if s["speaker"] == merged[-1]["speaker"]:
            merged[-1]["end"] = s["end"]
        else:
            merged.append(s)
    return merged


def assign_speakers(transcript_segments, speaker_segments):
    result = []
    for t in transcript_segments:
        mid = (t["start"] + t["end"]) / 2
        spk = 0
        for s in speaker_segments:
            if s["start"] <= mid <= s["end"]:
                spk = s["speaker"]
                break
        result.append({"start": t["start"], "end": t["end"], "text": t["text"].strip(), "speaker": spk})
    return result


def analyze_sentiment(text, pipe):
    if not text.strip():
        return {"label": "NEUTRAL", "score": 0.5}
    r = pipe(text[:512])
    if isinstance(r, list) and isinstance(r[0], list):
        r = r[0]
    return max(r, key=lambda x: x["score"])


def analyze_emotion(text, pipe):
    if not text.strip():
        return [{"label": "neutral", "score": 1.0}]
    r = pipe(text[:512])
    if isinstance(r, list) and isinstance(r[0], list):
        r = r[0]
    return r


def detect_themes(text, pipe, themes=None):
    if themes is None:
        themes = [
            "customer service", "technical support", "billing",
            "product inquiry", "complaint", "feedback",
            "policy discussion", "scheduling", "sales",
            "troubleshooting", "onboarding", "escalation",
            "satisfaction", "cancellation", "renewal",
        ]
    if not text.strip():
        return {}
    r = pipe(text[:1024], themes, multi_label=True)
    return dict(zip(r["labels"], r["scores"]))


def detect_policy_change(text, pipe):
    labels = ["policy change request", "terms modification", "rule exception request", "no policy change"]
    if not text.strip():
        return {"flag": False, "confidence": 0.0}
    r = pipe(text[:1024], labels)
    score = sum(s for l, s in zip(r["labels"], r["scores"]) if "policy" in l or "terms" in l or "exception" in l)
    return {"flag": score > 0.4, "confidence": score, "top_label": r["labels"][0], "top_score": r["scores"][0]}


def generate_summary(text, pipe):
    if len(text.split()) < 30:
        return text
    words = text.split()
    if len(words) > 1024:
        text = " ".join(words[:1024])
    result = pipe(text, max_length=150, min_length=30, do_sample=False)
    # Handle different output formats: "summary_text" (summarization) vs "generated_text" (text2text)
    out = result[0]
    return out.get("summary_text") or out.get("generated_text") or str(out)


def compute_audio_metrics(wav_path):
    import numpy as np
    y, sr = load_audio_numpy(wav_path)
    dur = len(y) / sr
    rms = np.sqrt(np.mean(y ** 2))
    silence = float(np.mean(np.abs(y) < 0.01))
    return {"duration_seconds": dur, "rms_energy": float(rms), "silence_ratio": silence, "talk_ratio": 1.0 - silence, "sample_rate": sr}


def extract_keywords(text, top_n=15):
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    sents = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    if len(sents) < 2:
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
        extra = {"um", "uh", "yeah", "okay", "oh", "like", "know", "just", "really"}
        freq = Counter(w for w in text.lower().split() if w not in ENGLISH_STOP_WORDS.union(extra) and len(w) > 2)
        return freq.most_common(top_n)
    vec = TfidfVectorizer(max_features=500, stop_words="english", ngram_range=(1, 2))
    mat = vec.fit_transform(sents)
    names = vec.get_feature_names_out()
    scores = np.asarray(mat.sum(axis=0)).flatten()
    idx = scores.argsort()[-top_n:][::-1]
    return [(names[i], scores[i]) for i in idx]


def compute_pace(segments):
    out = []
    for s in segments:
        d = s["end"] - s["start"]
        wc = len(s["text"].split())
        out.append({**s, "word_count": wc, "duration": d, "wpm": (wc / d * 60) if d > 0 else 0})
    return out


# ════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ════════════════════════════════════════════════════════════

def fmt_time(sec):
    return str(timedelta(seconds=int(sec)))[2:]

def metric_card(val, label):
    return f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{label}</div></div>'

def speaker_color(sid):
    return ["#00d4aa", "#7b61ff", "#ff6b6b", "#ffd93d", "#ff9f43"][sid % 5]


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    st.markdown("""
    <div class="header-glow">
        <h1>🎙️ Audio Intelligence Suite</h1>
        <p>Transcription · Speaker Diarization · Tone · Themes · Policy Detection · Analytics</p>
    </div>
    """, unsafe_allow_html=True)

    # ── FFMPEG CHECK ──
    ffmpeg_ok, ffmpeg_path = ensure_ffmpeg_on_path()

    if not ffmpeg_ok:
        st.error("⚠️ **ffmpeg not found!** Whisper needs ffmpeg to decode audio.")
        st.markdown("""
        ### Quick fix — pick ONE:

        **Option A — easiest (no admin needed):**
        ```bash
        pip install imageio-ffmpeg
        ```
        Then restart this app. It will auto-detect the bundled ffmpeg.

        **Option B — system install:**

        | OS | Command |
        |---|---|
        | **Windows (winget)** | `winget install Gyan.FFmpeg` |
        | **Windows (choco)** | `choco install ffmpeg` |
        | **Windows (manual)** | Download from [ffmpeg.org](https://ffmpeg.org/download.html), extract, add `bin` to PATH |
        | **macOS** | `brew install ffmpeg` |
        | **Linux** | `sudo apt install ffmpeg` |

        After installing, **restart your terminal** and rerun the app.
        """)
        # Auto-fix attempt
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            ffmpeg_ok = True
            os.environ["PATH"] = str(Path(ffmpeg_path).parent) + os.pathsep + os.environ.get("PATH", "")
            st.success(f"✅ Auto-detected ffmpeg via imageio-ffmpeg!")
        except Exception:
            st.info("💡 Run `pip install imageio-ffmpeg` in your terminal for the fastest fix.")
            return

    if not check_ffmpeg_works(ffmpeg_path):
        st.error(f"⚠️ Found ffmpeg at `{ffmpeg_path}` but it won't run. Try reinstalling.")
        return

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        whisper_model = st.selectbox("Whisper Model", ["tiny", "base", "small", "medium"], index=1)
        num_speakers = st.slider("Expected Speakers", 2, 5, 2)

        st.markdown("---")
        st.markdown("### 🎯 Analyses")
        run_themes = st.checkbox("Theme Detection", True)
        run_emotion = st.checkbox("Emotion Analysis", True)
        run_policy = st.checkbox("Policy Change Detection", True)
        run_summary = st.checkbox("Summary Generation", True)
        run_keywords = st.checkbox("Keyword Extraction", True)

        st.markdown("---")
        st.markdown("### 📝 Custom Themes")
        custom_themes_input = st.text_area("One per line", placeholder="pricing negotiation\ncontract renewal", height=100)

        st.markdown("---")
        st.markdown(f"""
        <div style="padding:12px; background:#12121a; border-radius:8px; border:1px solid #2a2a3e;">
            <p style="color:#00d4aa; font-weight:700; margin:0 0 8px 0;">🔧 Environment</p>
            <p style="color:#888; font-size:0.8rem; margin:0;">
                <b>ffmpeg:</b> ✅ {Path(ffmpeg_path).name}<br>
                <b>Platform:</b> {sys.platform}<br>
                <b>Python:</b> {sys.version.split()[0]}<br>
                <b>100% Local · No APIs</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ── UPLOAD ──
    st.markdown("### 📁 Upload Audio")
    uploaded_file = st.file_uploader(
        "Drag & drop any audio file",
        type=["wav", "mp3", "m4a", "flac", "ogg", "wma", "aac", "webm"],
    )

    if uploaded_file is None:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#666;">
            <div style="font-size:4rem; margin-bottom:16px;">🎧</div>
            <h3 style="color:#aaa;">Upload an audio file to begin</h3>
            <p>WAV, MP3, M4A, FLAC, OGG, WMA, AAC, WebM</p>
            <p style="font-size:0.85rem; margin-top:20px; color:#555;">
                All processing runs locally. No data leaves your machine.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Save to temp
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        raw_path = tmp.name

    st.audio(uploaded_file)

    if not st.button("🚀 Run Full Analysis", type="primary", use_container_width=True):
        return

    # ════════════════════════════════════════════════════════
    #  PIPELINE
    # ════════════════════════════════════════════════════════
    bar = st.progress(0)
    status = st.empty()
    wav_path = raw_path + ".16k.wav"

    try:
        # Step 0: Convert
        status.markdown("**🔄 Converting to 16kHz WAV...**")
        bar.progress(3)
        try:
            convert_audio_to_wav(raw_path, wav_path, ffmpeg_path)
        except Exception as e:
            st.error(f"❌ Audio conversion failed: {e}")
            st.markdown("**Possible causes:** corrupted file, unsupported codec, or ffmpeg issue.")
            return

        if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
            st.error("❌ Converted file is empty. Input may be corrupted.")
            return

        # Step 1: Metrics
        status.markdown("**⏱️ Audio metrics...**")
        bar.progress(5)
        metrics = compute_audio_metrics(wav_path)
        if metrics["duration_seconds"] < 1:
            st.error("❌ Audio too short (< 1s).")
            return

        # Step 2: Transcribe
        status.markdown(f"**🎤 Transcribing ({whisper_model})...**")
        bar.progress(10)
        try:
            tx = transcribe_audio(wav_path, whisper_model)
        except Exception as e:
            st.error(f"❌ Transcription failed: {e}")
            st.info("Try 'tiny' model or check audio quality.")
            return
        full_text = tx["text"].strip()
        segments = tx.get("segments", [])
        bar.progress(35)

        if not full_text:
            st.warning("⚠️ Empty transcript — audio may be silent or non-speech.")
        if not segments:
            segments = [{"start": 0, "end": metrics["duration_seconds"], "text": full_text}]

        # Step 3: Diarize
        status.markdown("**👥 Speaker diarization...**")
        bar.progress(40)
        try:
            spk_segs = simple_speaker_diarization(wav_path, num_speakers)
            diarized = assign_speakers(segments, spk_segs)
        except Exception as e:
            st.warning(f"⚠️ Diarization failed ({e}). All → Speaker 1.")
            diarized = [{"start": s["start"], "end": s["end"], "text": s["text"].strip(), "speaker": 0} for s in segments]
        bar.progress(50)

        # Step 4: Sentiment
        status.markdown("**💭 Sentiment...**")
        bar.progress(55)
        try:
            sent_pipe = load_sentiment_pipeline()
            seg_sent = [{**s, "sentiment": analyze_sentiment(s["text"], sent_pipe)} for s in diarized]
        except Exception as e:
            st.warning(f"⚠️ Sentiment failed ({e}).")
            seg_sent = [{**s, "sentiment": {"label": "NEUTRAL", "score": 0.5}} for s in diarized]
        bar.progress(65)

        # Step 5: Emotions
        seg_emo = []
        if run_emotion:
            status.markdown("**🎭 Emotions...**")
            try:
                emo_pipe = load_emotion_pipeline()
                seg_emo = [{**s, "emotions": analyze_emotion(s["text"], emo_pipe)} for s in seg_sent]
            except Exception as e:
                st.warning(f"⚠️ Emotion failed ({e}).")
                seg_emo = [{**s, "emotions": []} for s in seg_sent]
            bar.progress(72)
        else:
            seg_emo = [{**s, "emotions": []} for s in seg_sent]

        # Step 6: Themes
        theme_results = {}
        spk_theme_results = {}
        seg_themes = []
        zs_pipe = None

        if run_themes:
            status.markdown("**🏷️ Themes...**")
            try:
                zs_pipe = load_zero_shot_pipeline()
                custom = [t.strip() for t in custom_themes_input.strip().split("\n") if t.strip()] if custom_themes_input.strip() else []
                default = ["customer service", "technical support", "billing", "product inquiry", "complaint", "feedback",
                           "policy discussion", "scheduling", "sales", "troubleshooting", "onboarding", "escalation"]
                all_th = list(set(default + custom))

                if full_text.strip():
                    theme_results = detect_themes(full_text, zs_pipe, all_th)

                spk_texts = defaultdict(str)
                for s in diarized:
                    spk_texts[s["speaker"]] += " " + s["text"]
                for spk, txt in spk_texts.items():
                    if txt.strip():
                        spk_theme_results[spk] = detect_themes(txt, zs_pipe, all_th)

                step = max(1, len(seg_emo) // 10)
                for i, s in enumerate(seg_emo):
                    if i % step == 0 and len(s["text"].split()) > 5:
                        seg_themes.append({"start": s["start"], "end": s["end"], "speaker": s["speaker"],
                                           "themes": detect_themes(s["text"], zs_pipe, all_th)})
            except Exception as e:
                st.warning(f"⚠️ Theme detection failed ({e}).")
            bar.progress(82)

        # Step 7: Policy
        policy = {"flag": False, "confidence": 0.0}
        if run_policy:
            status.markdown("**📋 Policy detection...**")
            try:
                if zs_pipe is None:
                    zs_pipe = load_zero_shot_pipeline()
                if full_text.strip():
                    policy = detect_policy_change(full_text, zs_pipe)
            except Exception as e:
                st.warning(f"⚠️ Policy detection failed ({e}).")
            bar.progress(88)

        # Step 8: Summary
        summary = ""
        if run_summary:
            status.markdown("**📝 Summary...**")
            try:
                if full_text.strip() and len(full_text.split()) > 10:
                    summary = generate_summary(full_text, load_summarizer_pipeline())
                else:
                    summary = full_text
            except Exception as e:
                st.warning(f"⚠️ Summary failed ({e}).")
            bar.progress(93)

        # Step 9: Keywords
        keywords = []
        if run_keywords:
            status.markdown("**🔑 Keywords...**")
            try:
                if full_text.strip():
                    keywords = extract_keywords(full_text)
            except Exception as e:
                st.warning(f"⚠️ Keywords failed ({e}).")
            bar.progress(96)

        # Step 10: Pace
        paced = compute_pace(diarized)
        bar.progress(100)
        status.markdown("**✅ Done!**")
        time.sleep(0.4)
        status.empty()
        bar.empty()

        # ════════════════════════════════════════════════════
        #  DASHBOARD
        # ════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown("## 📊 Dashboard")

        dur_str = fmt_time(metrics["duration_seconds"])
        total_words = sum(len(s["text"].split()) for s in diarized)
        avg_wpm = (total_words / (metrics["duration_seconds"] / 60)) if metrics["duration_seconds"] > 0 else 0
        pos_n = sum(1 for s in seg_sent if s["sentiment"]["label"] == "POSITIVE")
        pos_pct = (pos_n / len(seg_sent) * 100) if seg_sent else 0

        for col, (v, l) in zip(st.columns(6), [
            (dur_str, "Duration"), (str(num_speakers), "Speakers"), (str(total_words), "Words"),
            (f"{avg_wpm:.0f}", "Avg WPM"), (f"{pos_pct:.0f}%", "Positive"), (f"{metrics['talk_ratio']*100:.0f}%", "Talk Ratio"),
        ]):
            with col:
                st.markdown(metric_card(v, l), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Policy
        if run_policy:
            fc = "policy-flag-yes" if policy["flag"] else "policy-flag-no"
            ft = "⚠️ YES — Policy Change" if policy["flag"] else "✅ NO — No Policy Change"
            st.markdown(f'<div style="text-align:center;margin:12px 0;"><span class="{fc}">{ft}</span>'
                        f' <span style="color:#888;margin-left:12px;">Confidence: {policy["confidence"]:.1%}</span></div>',
                        unsafe_allow_html=True)

        if run_summary and summary:
            st.markdown("### 📝 Summary")
            st.info(summary)

        # Two columns
        col_l, col_r = st.columns([3, 2])

        with col_l:
            st.markdown("### 🗣️ Diarized Transcript")
            for seg in seg_emo:
                sid = seg["speaker"]
                col = speaker_color(sid)
                sl = seg["sentiment"]["label"]
                sc = "tone-positive" if sl == "POSITIVE" else "tone-negative" if sl == "NEGATIVE" else "tone-neutral"
                si = "🟢" if sl == "POSITIVE" else "🔴" if sl == "NEGATIVE" else "🟡"
                te = ""
                if seg["emotions"]:
                    te = f" · {max(seg['emotions'], key=lambda x: x['score'])['label'].capitalize()}"
                ts = f"{fmt_time(seg['start'])} → {fmt_time(seg['end'])}"

                st.markdown(f"""
                <div class="segment-block" style="border-left-color:{col};">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                        <div>
                            <span class="speaker-tag speaker-{sid%3}">Speaker {sid+1}</span>
                            <span style="color:#666;font-size:0.75rem;margin-left:8px;">{ts}</span>
                        </div>
                        <div style="font-size:0.8rem;">{si} <span class="{sc}">{sl}</span><span style="color:#666;">{te}</span></div>
                    </div>
                    <div style="color:#ccc;font-size:0.9rem;line-height:1.5;">{seg['text']}</div>
                </div>""", unsafe_allow_html=True)

        with col_r:
            import plotly.graph_objects as go

            if run_themes and theme_results:
                st.markdown("### 🏷️ Themes")
                top_th = sorted(theme_results.items(), key=lambda x: x[1], reverse=True)[:8]
                fig = go.Figure(go.Bar(x=[s for _, s in top_th], y=[t for t, _ in top_th], orientation="h",
                    marker=dict(color=[s for _, s in top_th], colorscale=[[0, "#7b61ff"], [1, "#00d4aa"]])))
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc", size=11),
                    xaxis=dict(title="Confidence", gridcolor="#1a1a2e", range=[0, 1]), yaxis=dict(gridcolor="#1a1a2e"))
                st.plotly_chart(fig, use_container_width=True)

            if run_keywords and keywords:
                st.markdown("### 🔑 Keywords")
                st.markdown(" ".join(f'<span class="theme-badge">{k}</span>' for k, _ in keywords[:12]), unsafe_allow_html=True)

            if run_emotion and seg_emo:
                st.markdown("### 🎭 Emotions")
                ae = defaultdict(float)
                ct = 0
                for s in seg_emo:
                    if s["emotions"]:
                        ct += 1
                        for e in s["emotions"]:
                            ae[e["label"]] += e["score"]
                if ct:
                    for k in ae: ae[k] /= ct
                fig2 = go.Figure(go.Pie(labels=list(ae.keys()), values=list(ae.values()), hole=0.5,
                    marker=dict(colors=["#00d4aa", "#7b61ff", "#ff6b6b", "#ffd93d", "#ff9f43", "#4ecdc4", "#a8e6cf"]),
                    textinfo="label+percent", textfont=dict(size=11)))
                fig2.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"), showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

        # ── Timelines ──
        st.markdown("---")
        st.markdown("## 📈 Timeline Analysis")
        import plotly.graph_objects as go

        tab1, tab2, tab3, tab4 = st.tabs(["Sentiment", "Speaker Activity", "Pace", "Theme Evolution"])

        with tab1:
            fig_s = go.Figure()
            for spk in range(num_speakers):
                ss = [s for s in seg_sent if s["speaker"] == spk]
                if ss:
                    fig_s.add_trace(go.Scatter(
                        x=[s["start"] for s in ss],
                        y=[s["sentiment"]["score"] if s["sentiment"]["label"] == "POSITIVE" else -s["sentiment"]["score"] for s in ss],
                        mode="lines+markers", name=f"Speaker {spk+1}",
                        line=dict(color=speaker_color(spk), width=2), marker=dict(size=5)))
            fig_s.add_hline(y=0, line_dash="dash", line_color="#444")
            fig_s.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"),
                xaxis=dict(title="Time (s)", gridcolor="#1a1a2e"),
                yaxis=dict(title="Neg ← → Pos", gridcolor="#1a1a2e", range=[-1.1, 1.1]),
                legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig_s, use_container_width=True)

        with tab2:
            fig_a = go.Figure()
            for spk in range(num_speakers):
                for s in [s for s in diarized if s["speaker"] == spk]:
                    fig_a.add_trace(go.Bar(x=[s["end"]-s["start"]], y=[f"Speaker {spk+1}"], base=[s["start"]],
                        orientation="h", marker=dict(color=speaker_color(spk), opacity=0.7), showlegend=False))
            fig_a.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"),
                xaxis=dict(title="Time (s)", gridcolor="#1a1a2e"), yaxis=dict(gridcolor="#1a1a2e"), barmode="overlay")
            st.plotly_chart(fig_a, use_container_width=True)

            spk_times = defaultdict(float)
            for s in diarized: spk_times[s["speaker"]] += s["end"] - s["start"]
            for i, c in enumerate(st.columns(num_speakers)):
                with c:
                    p = (spk_times.get(i, 0) / metrics["duration_seconds"] * 100) if metrics["duration_seconds"] > 0 else 0
                    st.markdown(metric_card(f"{p:.1f}%", f"Speaker {i+1}"), unsafe_allow_html=True)

        with tab3:
            fig_p = go.Figure()
            for spk in range(num_speakers):
                ps = [s for s in paced if s["speaker"] == spk and s["wpm"] > 0]
                if ps:
                    fig_p.add_trace(go.Scatter(x=[s["start"] for s in ps], y=[s["wpm"] for s in ps],
                        mode="lines+markers", name=f"Speaker {spk+1}",
                        line=dict(color=speaker_color(spk), width=2), marker=dict(size=5)))
            fig_p.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"),
                xaxis=dict(title="Time (s)", gridcolor="#1a1a2e"), yaxis=dict(title="WPM", gridcolor="#1a1a2e"),
                legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig_p, use_container_width=True)

        with tab4:
            if run_themes and seg_themes:
                top5 = [t for t, _ in sorted(theme_results.items(), key=lambda x: x[1], reverse=True)[:5]]
                fig_t = go.Figure()
                for th in top5:
                    xv = [s["start"] for s in seg_themes if th in s["themes"]]
                    yv = [s["themes"][th] for s in seg_themes if th in s["themes"]]
                    if xv:
                        fig_t.add_trace(go.Scatter(x=xv, y=yv, mode="lines+markers", name=th.title(),
                            line=dict(width=2), marker=dict(size=6)))
                fig_t.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"),
                    xaxis=dict(title="Time (s)", gridcolor="#1a1a2e"),
                    yaxis=dict(title="Confidence", gridcolor="#1a1a2e", range=[0, 1]),
                    legend=dict(bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig_t, use_container_width=True)
            else:
                st.info("Enable themes to see evolution.")

        # ── Per Speaker ──
        st.markdown("---")
        st.markdown("## 👤 Per-Speaker Analysis")
        for spk_idx, spk_tab in enumerate(st.tabs([f"Speaker {i+1}" for i in range(num_speakers)])):
            with spk_tab:
                ss = [s for s in seg_emo if s["speaker"] == spk_idx]
                wc = sum(len(s["text"].split()) for s in ss)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Segments", len(ss))
                c2.metric("Words", wc)
                pos = sum(1 for s in ss if s["sentiment"]["label"] == "POSITIVE")
                c3.metric("Sentiment", f"{pos/len(ss)*100:.0f}% pos" if ss else "N/A")
                if ss and ss[0]["emotions"]:
                    ae = defaultdict(float)
                    for s in ss:
                        for e in s["emotions"]: ae[e["label"]] += e["score"]
                    c4.metric("Top Emotion", max(ae, key=ae.get).capitalize())
                else:
                    c4.metric("Top Emotion", "N/A")
                if run_themes and spk_idx in spk_theme_results:
                    st.markdown("**Themes:** " + " ".join(
                        f'<span class="theme-badge">{t} ({s:.0%})</span>'
                        for t, s in sorted(spk_theme_results[spk_idx].items(), key=lambda x: x[1], reverse=True)[:5]
                    ), unsafe_allow_html=True)

        # ── Export ──
        st.markdown("---")
        st.markdown("### 💾 Export")
        export = {
            "audio_metrics": metrics, "summary": summary, "policy_change": policy,
            "themes": theme_results, "keywords": [(k, float(s)) for k, s in keywords],
            "transcript": [{"start": s["start"], "end": s["end"], "speaker": s["speaker"],
                            "text": s["text"], "sentiment": s["sentiment"]} for s in seg_sent],
        }
        c1, c2 = st.columns(2)
        c1.download_button("📥 JSON Report", json.dumps(export, indent=2, default=str),
                           "audio_report.json", "application/json", use_container_width=True)
        c2.download_button("📥 Transcript TXT",
                           "\n".join(f"[{fmt_time(s['start'])}-{fmt_time(s['end'])}] Speaker {s['speaker']+1}: {s['text']}" for s in diarized),
                           "transcript.txt", "text/plain", use_container_width=True)

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        st.exception(e)
    finally:
        for f in [raw_path, wav_path]:
            try:
                if os.path.exists(f): os.unlink(f)
            except Exception:
                pass


if __name__ == "__main__":
    main()
