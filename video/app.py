"""
eBay Live Stream Analyzer
=========================
A Streamlit app that processes live-stream auction videos to:
1. Extract & analyze buyer chat comments (OCR from video overlay)
2. Detect chat themes in real-time
3. Build buyer behavior profiles & shill-bidding risk scores
4. Capture product/card images from the stream

Runs 100% locally — no APIs, no cost. Optimized for CPU / Apple Silicon.
"""

import streamlit as st
import tempfile
import os
import time
import threading
from pathlib import Path

from video_processor import VideoProcessor
from ocr_engine import OCREngine
from comment_parser import CommentParser
from buyer_analyzer import BuyerAnalyzer
from theme_analyzer import ThemeAnalyzer
from product_detector import ProductDetector
from llm_engine import LLMEngine

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="eBay Live Stream Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark auction-house theme */
    .stApp { background-color: #0e1117; }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.4rem 0;
        text-align: center;
    }
    .metric-card h3 {
        color: #e94560;
        font-size: 2rem;
        margin: 0;
    }
    .metric-card p {
        color: #a8a8b3;
        font-size: 0.85rem;
        margin: 0;
    }
    
    .shill-alert {
        background: linear-gradient(135deg, #4a0000 0%, #2d0000 100%);
        border: 1px solid #e94560;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { border-color: #e94560; }
        50% { border-color: #ff6b6b; }
    }
    
    .buyer-row {
        background: #1a1a2e;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        border-left: 3px solid #0f3460;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .buyer-row.shill-risk {
        border-left: 3px solid #e94560;
        background: #1a0a0e;
    }
    
    .theme-tag {
        display: inline-block;
        background: #0f3460;
        color: #e0e0e0;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-size: 0.85rem;
    }
    
    .comment-feed {
        max-height: 400px;
        overflow-y: auto;
        background: #0a0a14;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #1a1a2e;
    }
    .comment-item {
        padding: 0.4rem 0;
        border-bottom: 1px solid #1a1a2e;
        font-size: 0.85rem;
    }
    .comment-user {
        color: #4fc3f7;
        font-weight: 600;
    }
    .comment-text {
        color: #c8c8d0;
    }
    .comment-bid {
        color: #66bb6a;
        font-weight: 700;
    }
    
    .product-card {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 0.5rem;
        margin: 0.3rem;
        border: 1px solid #0f3460;
        text-align: center;
    }
    
    .status-running { color: #66bb6a; }
    .status-stopped { color: #ef5350; }
    
    div[data-testid="stSidebar"] {
        background: #0a0a14;
    }
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ─────────────────────────────────────────────
def init_session_state():
    defaults = {
        "processing": False,
        "stop_signal": False,
        "video_path": None,
        "comments": [],           # List of parsed comment dicts
        "buyer_profiles": {},     # username -> BuyerProfile
        "themes": [],             # List of (theme_name, keywords, score)
        "products": [],           # List of (timestamp, image_array)
        "shill_alerts": [],       # List of shill alert dicts
        "frame_count": 0,
        "fps_processed": 0.0,
        "total_comments": 0,
        "unique_buyers": 0,
        "current_frame": None,
        "processing_log": [],
        "chat_region": None,      # (x1, y1, x2, y2) for chat overlay region
        "ocr_engine_ready": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ── Sidebar: Config & Upload ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Stream Analyzer")
    st.markdown("---")
    
    # Video Upload
    st.markdown("### 📹 Video Input")
    uploaded_file = st.file_uploader(
        "Upload auction stream recording",
        type=["mp4", "avi", "mov", "mkv", "webm", "flv"],
        help="Any standard video format is supported.",
    )
    
    if uploaded_file:
        # Save to temp file
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(uploaded_file.read())
            st.session_state.video_path = f.name
        st.success(f"✓ Loaded: {uploaded_file.name}")
    
    st.markdown("---")
    
    # Processing Settings
    st.markdown("### ⚙️ Processing Settings")
    
    ocr_fps = st.slider(
        "OCR sample rate (FPS)",
        min_value=0.5, max_value=5.0, value=1.5, step=0.5,
        help="Frames per second to run OCR on. Lower = less CPU load.",
    )
    
    product_fps = st.slider(
        "Product capture rate (FPS)",
        min_value=0.1, max_value=2.0, value=0.5, step=0.1,
        help="How often to check for new products/cards.",
    )
    
    scene_threshold = st.slider(
        "Scene change sensitivity",
        min_value=0.1, max_value=0.9, value=0.4, step=0.05,
        help="Lower = more sensitive to product changes.",
    )
    
    st.markdown("---")
    
    # Chat Region Config
    st.markdown("### 💬 Chat Region")
    st.caption("Define where the chat overlay appears in the video (as % of frame)")
    
    col1, col2 = st.columns(2)
    with col1:
        chat_x1 = st.number_input("Left %", 0, 100, 65, key="cx1")
        chat_y1 = st.number_input("Top %", 0, 100, 10, key="cy1")
    with col2:
        chat_x2 = st.number_input("Right %", 0, 100, 100, key="cx2")
        chat_y2 = st.number_input("Bottom %", 0, 100, 90, key="cy2")
    
    st.session_state.chat_region = (chat_x1 / 100, chat_y1 / 100, chat_x2 / 100, chat_y2 / 100)
    
    st.markdown("---")
    
    # Shill Detection Tuning
    st.markdown("### 🚨 Shill Detection")
    
    shill_bid_freq = st.slider(
        "Bid frequency threshold",
        min_value=2, max_value=20, value=5,
        help="Bids within short window to flag as suspicious.",
    )
    
    shill_price_jump = st.slider(
        "Price jump % threshold",
        min_value=5, max_value=50, value=15,
        help="Minimum price increase % to flag as suspicious.",
    )
    
    st.markdown("---")
    
    # LLM Settings
    st.markdown("### 🧠 LLM Engine (Optional)")
    use_llm = st.checkbox("Enable LLM analysis", value=False,
                          help="Uses llama-cpp-python with a local model for deeper analysis.")
    
    if use_llm:
        llm_model_path = st.text_input(
            "Model path (.gguf)",
            placeholder="/path/to/model.gguf",
            help="Path to a GGUF model file (e.g., TinyLlama, Phi-3-mini).",
        )
        llm_interval = st.slider(
            "LLM analysis interval (sec)",
            min_value=15, max_value=120, value=45, step=15,
        )
    else:
        llm_model_path = None
        llm_interval = 60


# ── Main Content ─────────────────────────────────────────────────────────────
st.markdown("# 🔴 eBay Live Stream Analyzer")
st.caption("Real-time auction stream intelligence — 100% local, zero cost")

# Top-level controls
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 2, 2, 4])

with ctrl_col1:
    start_btn = st.button(
        "▶️ Start Analysis",
        use_container_width=True,
        disabled=st.session_state.processing or st.session_state.video_path is None,
    )
with ctrl_col2:
    stop_btn = st.button(
        "⏹️ Stop",
        use_container_width=True,
        disabled=not st.session_state.processing,
    )
with ctrl_col3:
    reset_btn = st.button("🔄 Reset", use_container_width=True)

with ctrl_col4:
    if st.session_state.processing:
        st.markdown('<span class="status-running">● Processing...</span>', unsafe_allow_html=True)
    elif st.session_state.video_path:
        st.markdown('<span class="status-stopped">● Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-stopped">● Upload a video to begin</span>', unsafe_allow_html=True)

if reset_btn:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()
    st.rerun()

# ── Metric Cards ─────────────────────────────────────────────────────────────
st.markdown("---")
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{st.session_state.total_comments}</h3>
        <p>Total Comments</p>
    </div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{st.session_state.unique_buyers}</h3>
        <p>Unique Buyers</p>
    </div>""", unsafe_allow_html=True)

with m3:
    shill_count = len(st.session_state.shill_alerts)
    st.markdown(f"""
    <div class="metric-card">
        <h3>{shill_count}</h3>
        <p>Shill Alerts</p>
    </div>""", unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{len(st.session_state.themes)}</h3>
        <p>Active Themes</p>
    </div>""", unsafe_allow_html=True)

with m5:
    st.markdown(f"""
    <div class="metric-card">
        <h3>{len(st.session_state.products)}</h3>
        <p>Products Captured</p>
    </div>""", unsafe_allow_html=True)


# ── Processing Engine ────────────────────────────────────────────────────────
def run_processing():
    """Main processing loop — runs in the background via Streamlit rerun cycle."""
    video_path = st.session_state.video_path
    chat_region = st.session_state.chat_region
    
    # Initialize engines
    vp = VideoProcessor(video_path)
    ocr = OCREngine()
    parser = CommentParser()
    buyer_analyzer = BuyerAnalyzer(
        bid_freq_threshold=shill_bid_freq,
        price_jump_threshold=shill_price_jump,
    )
    theme_analyzer = ThemeAnalyzer()
    product_detector = ProductDetector(threshold=scene_threshold)
    
    llm = None
    if use_llm and llm_model_path and os.path.exists(llm_model_path):
        try:
            llm = LLMEngine(llm_model_path)
        except Exception as e:
            st.session_state.processing_log.append(f"LLM load failed: {e}")
    
    total_frames = vp.total_frames
    fps = vp.fps
    
    ocr_interval = int(fps / ocr_fps) if ocr_fps > 0 else int(fps)
    product_interval = int(fps / product_fps) if product_fps > 0 else int(fps * 2)
    llm_frame_interval = int(fps * llm_interval)
    
    frame_idx = 0
    
    progress_bar = st.progress(0, text="Processing video...")
    
    while not st.session_state.stop_signal:
        frame = vp.read_frame()
        if frame is None:
            break
        
        frame_idx += 1
        st.session_state.frame_count = frame_idx
        
        # Update progress
        progress = min(frame_idx / max(total_frames, 1), 1.0)
        progress_bar.progress(progress, text=f"Frame {frame_idx}/{total_frames}")
        
        # ── OCR & Comment Extraction ──
        if frame_idx % ocr_interval == 0:
            h, w = frame.shape[:2]
            x1 = int(chat_region[0] * w)
            y1 = int(chat_region[1] * h)
            x2 = int(chat_region[2] * w)
            y2 = int(chat_region[3] * h)
            
            chat_crop = frame[y1:y2, x1:x2]
            
            if chat_crop.size > 0:
                raw_texts = ocr.extract_text(chat_crop)
                timestamp = frame_idx / fps
                
                new_comments = parser.parse_comments(raw_texts, timestamp)
                
                for comment in new_comments:
                    st.session_state.comments.append(comment)
                    buyer_analyzer.process_comment(comment)
                
                st.session_state.total_comments = len(st.session_state.comments)
                st.session_state.unique_buyers = buyer_analyzer.unique_buyer_count()
                st.session_state.buyer_profiles = buyer_analyzer.get_profiles()
                st.session_state.shill_alerts = buyer_analyzer.get_shill_alerts()
                
                # Update themes every 10 OCR cycles
                if (frame_idx // ocr_interval) % 10 == 0 and st.session_state.comments:
                    all_texts = [c["text"] for c in st.session_state.comments]
                    st.session_state.themes = theme_analyzer.extract_themes(all_texts)
        
        # ── Product Detection ──
        if frame_idx % product_interval == 0:
            # Use center-left region (where seller typically shows products)
            h, w = frame.shape[:2]
            product_crop = frame[int(h*0.1):int(h*0.9), int(w*0.05):int(w*0.6)]
            
            is_new, snapshot = product_detector.detect_new_product(product_crop, frame_idx / fps)
            if is_new and snapshot is not None:
                st.session_state.products.append({
                    "timestamp": frame_idx / fps,
                    "image": snapshot,
                    "frame": frame_idx,
                })
        
        # ── LLM Analysis (periodic) ──
        if llm and frame_idx % llm_frame_interval == 0 and st.session_state.comments:
            recent = st.session_state.comments[-50:]
            analysis = llm.analyze_chat_batch(recent, st.session_state.buyer_profiles)
            if analysis:
                st.session_state.processing_log.append(f"[LLM @ {frame_idx/fps:.0f}s] {analysis}")
        
        # Store current frame for display
        if frame_idx % int(fps) == 0:  # Update display frame once per second
            st.session_state.current_frame = frame
    
    vp.release()
    st.session_state.processing = False
    st.session_state.stop_signal = False
    progress_bar.progress(1.0, text="Processing complete!")


# ── Trigger Processing ───────────────────────────────────────────────────────
if start_btn and st.session_state.video_path:
    st.session_state.processing = True
    st.session_state.stop_signal = False
    run_processing()
    st.rerun()

if stop_btn:
    st.session_state.stop_signal = True
    st.session_state.processing = False
    st.rerun()


# ── Dashboard Panels ─────────────────────────────────────────────────────────
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Chat Themes",
    "👥 Buyer Dashboard",
    "🚨 Shill Detection",
    "📦 Products",
    "🖥️ Video Feed",
])

# ── TAB 1: Chat Themes ──────────────────────────────────────────────────────
with tab1:
    col_themes, col_feed = st.columns([3, 2])
    
    with col_themes:
        st.markdown("### 🏷️ Detected Themes")
        
        if st.session_state.themes:
            for theme_name, keywords, score in st.session_state.themes:
                score_bar = "█" * int(score * 20)
                st.markdown(f"""
                <div style="background:#1a1a2e;border-radius:10px;padding:1rem;margin:0.5rem 0;border-left:4px solid #4fc3f7;">
                    <strong style="color:#4fc3f7;font-size:1.1rem;">{theme_name}</strong>
                    <span style="color:#66bb6a;float:right;">{score:.0%}</span><br>
                    <span style="color:#a8a8b3;font-size:0.85rem;">
                        {"  ".join([f'<span class="theme-tag">{k}</span>' for k in keywords[:6]])}
                    </span><br>
                    <span style="color:#0f3460;font-size:0.7rem;">{score_bar}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Themes will appear here once enough comments are processed.")
    
    with col_feed:
        st.markdown("### 📜 Live Comment Feed")
        
        if st.session_state.comments:
            comments_display = st.session_state.comments[-50:][::-1]
            feed_html = '<div class="comment-feed">'
            for c in comments_display:
                bid_tag = f' <span class="comment-bid">[BID: {c.get("bid_amount", "")}]</span>' if c.get("is_bid") else ""
                feed_html += f"""
                <div class="comment-item">
                    <span class="comment-user">{c.get('username', 'Unknown')}</span>{bid_tag}
                    <br><span class="comment-text">{c.get('text', '')}</span>
                    <span style="color:#555;font-size:0.7rem;float:right;">{c.get('timestamp', 0):.1f}s</span>
                </div>"""
            feed_html += "</div>"
            st.markdown(feed_html, unsafe_allow_html=True)
        else:
            st.info("Comments will stream here during processing.")


# ── TAB 2: Buyer Dashboard ──────────────────────────────────────────────────
with tab2:
    st.markdown("### 👥 Buyer Behavior Profiles")
    
    profiles = st.session_state.buyer_profiles
    
    if profiles:
        # Summary stats
        s1, s2, s3 = st.columns(3)
        active_bidders = sum(1 for p in profiles.values() if p.get("bid_count", 0) > 0)
        avg_engagement = sum(p.get("comment_count", 0) for p in profiles.values()) / max(len(profiles), 1)
        
        with s1:
            st.metric("Active Bidders", active_bidders)
        with s2:
            st.metric("Avg Comments/Buyer", f"{avg_engagement:.1f}")
        with s3:
            high_interest = sum(1 for p in profiles.values() if p.get("interest_score", 0) > 0.6)
            st.metric("High Interest Buyers", high_interest)
        
        st.markdown("---")
        
        # Buyer table
        import pandas as pd
        
        buyer_data = []
        for username, profile in sorted(profiles.items(), key=lambda x: x[1].get("interest_score", 0), reverse=True):
            buyer_data.append({
                "Buyer": username,
                "Comments": profile.get("comment_count", 0),
                "Bids": profile.get("bid_count", 0),
                "Avg Bid ($)": f"${profile.get('avg_bid', 0):.2f}" if profile.get("avg_bid") else "—",
                "Interest Score": f"{profile.get('interest_score', 0):.0%}",
                "Shill Risk": f"{profile.get('shill_score', 0):.0%}",
                "First Seen": f"{profile.get('first_seen', 0):.0f}s",
                "Last Active": f"{profile.get('last_seen', 0):.0f}s",
                "Behavior": profile.get("behavior_tag", "observer"),
            })
        
        if buyer_data:
            df = pd.DataFrame(buyer_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Shill Risk": st.column_config.TextColumn("Shill Risk", help="Risk of shill bidding behavior"),
                    "Interest Score": st.column_config.TextColumn("Interest", help="How interested this buyer appears"),
                },
            )
    else:
        st.info("Buyer profiles will build up as comments are processed.")


# ── TAB 3: Shill Detection ──────────────────────────────────────────────────
with tab3:
    st.markdown("### 🚨 Shill Bidding Detection")
    st.caption("Flagged buyers exhibiting suspicious bidding patterns")
    
    alerts = st.session_state.shill_alerts
    
    if alerts:
        for alert in sorted(alerts, key=lambda a: a.get("risk_score", 0), reverse=True):
            risk = alert.get("risk_score", 0)
            color = "#e94560" if risk > 0.7 else "#ff9800" if risk > 0.4 else "#ffeb3b"
            
            st.markdown(f"""
            <div class="shill-alert" style="border-color:{color};">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong style="color:{color};font-size:1.1rem;">⚠️ {alert.get('username', 'Unknown')}</strong>
                    <span style="color:{color};font-size:1.3rem;font-weight:700;">{risk:.0%} Risk</span>
                </div>
                <div style="color:#a8a8b3;margin-top:0.5rem;font-size:0.9rem;">
                    <strong>Reasons:</strong><br>
                    {"<br>".join(f"• {r}" for r in alert.get('reasons', []))}
                </div>
                <div style="color:#666;margin-top:0.3rem;font-size:0.8rem;">
                    Bids: {alert.get('bid_count', 0)} | 
                    Avg interval: {alert.get('avg_bid_interval', 0):.1f}s |
                    Price range: ${alert.get('min_bid', 0):.0f}–${alert.get('max_bid', 0):.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No shill bidding alerts detected. The auction appears clean so far.")
    
    st.markdown("---")
    st.markdown("#### Detection Criteria")
    st.markdown(f"""
    The shill detection engine flags buyers based on multiple signals:
    
    - **Rapid-fire bidding**: More than **{shill_bid_freq}** bids within a short time window  
    - **Strategic price jumps**: Bids that inflate price by more than **{shill_price_jump}%** over previous bids  
    - **Bid-then-vanish pattern**: Buyer places aggressive bids but never wins / always gets outbid at the last moment  
    - **Late-entry aggression**: Buyer appears only during bidding wars, no general chat engagement  
    - **Coordinated patterns**: Multiple accounts bidding in lockstep or relay patterns  
    """)


# ── TAB 4: Products ─────────────────────────────────────────────────────────
with tab4:
    st.markdown("### 📦 Captured Products / Cards")
    
    products = st.session_state.products
    
    if products:
        import numpy as np
        
        cols = st.columns(4)
        for i, product in enumerate(products):
            with cols[i % 4]:
                st.image(
                    product["image"],
                    caption=f"Product @ {product['timestamp']:.1f}s (Frame {product['frame']})",
                    use_container_width=True,
                )
        
        st.markdown("---")
        
        # Product catalog as DataFrame
        import pandas as pd
        catalog = pd.DataFrame([
            {
                "Product #": i + 1,
                "Timestamp": f"{p['timestamp']:.1f}s",
                "Frame": p["frame"],
            }
            for i, p in enumerate(products)
        ])
        st.dataframe(catalog, use_container_width=True, hide_index=True)
    else:
        st.info("Product captures will appear here as new items are detected in the stream.")


# ── TAB 5: Video Feed ───────────────────────────────────────────────────────
with tab5:
    st.markdown("### 🖥️ Video Feed & Processing Status")
    
    vid_col, log_col = st.columns([3, 2])
    
    with vid_col:
        if st.session_state.current_frame is not None:
            st.image(st.session_state.current_frame, channels="BGR", caption="Current Frame", use_container_width=True)
        elif st.session_state.video_path:
            # Show first frame as preview
            import cv2
            cap = cv2.VideoCapture(st.session_state.video_path)
            ret, frame = cap.read()
            if ret:
                st.image(frame, channels="BGR", caption="Video Preview (first frame)", use_container_width=True)
            cap.release()
        else:
            st.info("Upload a video to see the feed here.")
        
        # Show chat region overlay info
        if st.session_state.chat_region:
            cr = st.session_state.chat_region
            st.caption(
                f"Chat region: ({cr[0]:.0%}, {cr[1]:.0%}) → ({cr[2]:.0%}, {cr[3]:.0%})"
            )
    
    with log_col:
        st.markdown("#### Processing Log")
        if st.session_state.processing_log:
            for log in st.session_state.processing_log[-20:][::-1]:
                st.text(log)
        else:
            st.caption("Processing events will appear here.")
        
        st.markdown("#### Stats")
        st.text(f"Frames processed: {st.session_state.frame_count}")
        st.text(f"Total comments:   {st.session_state.total_comments}")
        st.text(f"Unique buyers:    {st.session_state.unique_buyers}")
        st.text(f"Products found:   {len(st.session_state.products)}")
        st.text(f"Shill alerts:     {len(st.session_state.shill_alerts)}")


# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Built with Streamlit • OpenCV • EasyOCR • scikit-learn • llama-cpp-python | "
    "100% local processing — no data leaves your machine."
)
