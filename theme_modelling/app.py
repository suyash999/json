"""
═══════════════════════════════════════════════════════════════════════════
   ████████╗██╗  ██╗███████╗███╗   ███╗███████╗
   ╚══██╔══╝██║  ██║██╔════╝████╗ ████║██╔════╝
      ██║   ███████║█████╗  ██╔████╔██║█████╗
      ██║   ██╔══██║██╔══╝  ██║╚██╔╝██║██╔══╝
      ██║   ██║  ██║███████╗██║ ╚═╝ ██║███████╗
      ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚══════╝
   MODELLING ENGINE v1.0 — eBay Customer Theme Analyzer
═══════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import io

from utils.eda_engine import run_eda, detect_column_types
from utils.theme_engine import (
    run_theme_analysis, keyword_match_theme, detect_tone,
    detect_policy_indicator, get_cluster_summaries,
)
from config.theme_mappings import (
    GRANULAR_THEMES, UBER_THEMES, TONE_MAPPINGS, POLICY_INDICATORS,
)

# ═══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Theme Modelling Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════
# CUSTOM STYLING
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

    .stApp { font-family: 'DM Sans', sans-serif; }

    .main-header {
        background: linear-gradient(135deg, #0a0a14 0%, #1a1a28 100%);
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        border: 1px solid #2a2a3e;
    }
    .main-header h1 {
        color: #e8a838;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: #8a8578;
        font-size: 0.9rem;
        margin: 4px 0 0;
    }

    .metric-card {
        background: #12121e;
        border: 1px solid #2a2a3e;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .metric-card h3 { color: #e8a838; font-size: 1.6rem; margin: 0; }
    .metric-card p { color: #8a8578; font-size: 0.78rem; margin: 4px 0 0; }

    .theme-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px;
    }

    .step-header {
        background: linear-gradient(90deg, rgba(232,168,56,0.1), transparent);
        padding: 12px 16px;
        border-left: 3px solid #e8a838;
        border-radius: 0 8px 8px 0;
        margin: 16px 0 12px;
    }
    .step-header h3 { margin: 0; color: #f2ece0; font-size: 1rem; }

    div[data-testid="stTabs"] button[data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════════
if 'df' not in st.session_state:
    st.session_state.df = None
if 'col_types' not in st.session_state:
    st.session_state.col_types = None
if 'text_column' not in st.session_state:
    st.session_state.text_column = None
if 'theme_results' not in st.session_state:
    st.session_state.theme_results = None
if 'cluster_summaries' not in st.session_state:
    st.session_state.cluster_summaries = None
if 'user_theme_map' not in st.session_state:
    st.session_state.user_theme_map = {}
if 'user_tone_map' not in st.session_state:
    st.session_state.user_tone_map = {}
if 'user_policy_map' not in st.session_state:
    st.session_state.user_policy_map = {}
if 'final_df' not in st.session_state:
    st.session_state.final_df = None

# ═══════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="main-header">
    <h1>🎯 Theme Modelling Engine</h1>
    <p>BERT-powered customer feedback analysis · eBay-optimized · Upload → Analyze → Visualize</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    st.markdown("**Upload Dataset**")
    uploaded_file = st.file_uploader(
        "CSV, Excel, or JSON",
        type=["csv", "xlsx", "xls", "json", "tsv"],
        help="Upload your customer feedback dataset",
    )

    if uploaded_file:
        try:
            fname = uploaded_file.name.lower()
            if fname.endswith('.csv'):
                st.session_state.df = pd.read_csv(uploaded_file)
            elif fname.endswith('.tsv'):
                st.session_state.df = pd.read_csv(uploaded_file, sep='\t')
            elif fname.endswith(('.xlsx', '.xls')):
                st.session_state.df = pd.read_excel(uploaded_file)
            elif fname.endswith('.json'):
                st.session_state.df = pd.read_json(uploaded_file)
            st.success(f"✓ Loaded {len(st.session_state.df):,} rows × {len(st.session_state.df.columns)} columns")
        except Exception as e:
            st.error(f"Error loading file: {e}")

    st.markdown("---")

    if st.session_state.df is not None:
        st.markdown("**Model Settings**")
        n_clusters = st.slider("Number of clusters", 5, 30, 12)
        clustering_method = st.selectbox(
            "Clustering method",
            ["kmeans", "hdbscan"],
            help="KMeans is faster, HDBSCAN finds natural clusters",
        )
        min_confidence = st.slider("Min confidence threshold", 0.0, 1.0, 0.2, 0.05)

    st.markdown("---")
    st.markdown("### 📋 Pipeline Status")
    steps = ["Upload Data", "EDA", "Select Text Field", "Theme Analysis",
             "Normalization", "Tone & Policy", "Visualizations"]
    for i, step in enumerate(steps):
        if st.session_state.df is not None and i <= 1:
            st.markdown(f"✅ {step}")
        elif st.session_state.text_column and i <= 2:
            st.markdown(f"✅ {step}")
        elif st.session_state.theme_results is not None and i <= 3:
            st.markdown(f"✅ {step}")
        elif st.session_state.final_df is not None and i <= 5:
            st.markdown(f"✅ {step}")
        else:
            st.markdown(f"⬜ {step}")

# ═══════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 EDA & Data Upload",
    "🎯 Theme Analysis",
    "🔄 Theme Normalization",
    "💬 Tone & Policy",
    "📈 Visualizations",
])

# ══════════════════════════════════════════════════════════════════
# TAB 1: EDA
# ══════════════════════════════════════════════════════════════════
with tab1:
    if st.session_state.df is None:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px;">
            <h2 style="color:#e8a838;">Upload Your Dataset</h2>
            <p style="color:#8a8578;">Use the sidebar to upload a CSV, Excel, or JSON file.<br>
            The engine will auto-detect column types and run EDA.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = st.session_state.df

        # Run EDA
        col_types = run_eda(df)
        st.session_state.col_types = col_types

        # ── Select text field ──
        st.markdown("---")
        st.markdown('<div class="step-header"><h3>🎯 Step: Select the Text Field for Theme Analysis</h3></div>', unsafe_allow_html=True)

        text_candidates = col_types.get("text", []) + col_types.get("categorical", [])
        if text_candidates:
            selected_text = st.selectbox(
                "Which column contains the customer feedback text?",
                options=text_candidates,
                help="Select the column with customer messages/comments/feedback",
            )
            st.session_state.text_column = selected_text

            # Preview
            st.markdown(f"**Preview of `{selected_text}`:**")
            sample = df[selected_text].dropna().head(5).tolist()
            for i, text in enumerate(sample):
                st.caption(f"_{str(text)[:200]}{'...' if len(str(text)) > 200 else ''}_")

            st.info("✓ Text field selected. Proceed to the **Theme Analysis** tab.")
        else:
            st.warning("No text columns detected. Please check your dataset.")

# ══════════════════════════════════════════════════════════════════
# TAB 2: THEME ANALYSIS
# ══════════════════════════════════════════════════════════════════
with tab2:
    if st.session_state.df is None or st.session_state.text_column is None:
        st.warning("Please upload data and select a text field in Tab 1 first.")
    else:
        df = st.session_state.df
        text_col = st.session_state.text_column

        st.markdown('<div class="step-header"><h3>🧠 Pre-Built Theme Mappings (eBay-Optimized)</h3></div>', unsafe_allow_html=True)

        # Show existing mappings
        with st.expander("📋 View / Edit Exhaustive Theme Mappings", expanded=False):
            st.markdown("These are the pre-built granular themes. Each maps to an Uber Theme.")

            edit_tabs = st.columns([1, 1])
            with edit_tabs[0]:
                st.markdown("**Granular Themes → Uber Themes**")
                mapping_data = []
                for theme_id, data in GRANULAR_THEMES.items():
                    mapping_data.append({
                        "Theme ID": theme_id,
                        "Uber Theme": data["uber_theme"],
                        "Keywords (sample)": ", ".join(data["keywords"][:5]),
                    })
                mapping_df = pd.DataFrame(mapping_data)
                st.dataframe(mapping_df, use_container_width=True, height=400)

            with edit_tabs[1]:
                st.markdown("**Uber Theme Categories**")
                uber_data = []
                for name, data in UBER_THEMES.items():
                    uber_data.append({
                        "Uber Theme": f"{data['icon']} {name}",
                        "Description": data["description"],
                        "Granular Count": len(data["granular_themes"]),
                    })
                st.dataframe(pd.DataFrame(uber_data), use_container_width=True, height=400)

        # User custom mapping
        with st.expander("✏️ Add Custom Theme Mapping", expanded=False):
            st.markdown("Override or add your own theme mappings.")
            custom_col1, custom_col2 = st.columns(2)
            with custom_col1:
                custom_theme_id = st.text_input("Theme ID (e.g., 'my_custom_theme')")
                custom_uber = st.selectbox(
                    "Map to Uber Theme",
                    options=list(UBER_THEMES.keys()) + ["— Create New —"]
                )
            with custom_col2:
                custom_keywords = st.text_area(
                    "Keywords (comma-separated)",
                    placeholder="keyword1, keyword2, keyword3",
                )
                if custom_uber == "— Create New —":
                    new_uber_name = st.text_input("New Uber Theme Name")

            if st.button("Add Custom Mapping"):
                if custom_theme_id and custom_keywords:
                    uber_name = new_uber_name if custom_uber == "— Create New —" else custom_uber
                    st.session_state.user_theme_map[custom_theme_id] = uber_name
                    st.success(f"✓ Added: {custom_theme_id} → {uber_name}")

        # ── Run Analysis ──
        st.markdown("---")
        st.markdown('<div class="step-header"><h3>🚀 Run Theme Analysis</h3></div>', unsafe_allow_html=True)

        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(f"""
            **Ready to analyze `{text_col}` column**
            - {len(df):,} rows will be processed
            - BERT embeddings + keyword matching + clustering
            - Estimated time: {max(1, len(df) // 500)} - {max(2, len(df) // 200)} minutes
            """)
        with col_b:
            run_analysis = st.button("🎯 Run Theme Analysis", type="primary", use_container_width=True)

        if run_analysis:
            with st.spinner("Running theme analysis... This may take a few minutes."):
                progress = st.progress(0, text="Preprocessing text...")

                try:
                    progress.progress(10, text="Generating BERT embeddings...")

                    result_df, cluster_sums = run_theme_analysis(
                        df,
                        text_col,
                        user_theme_overrides=st.session_state.user_theme_map,
                        n_clusters=n_clusters,
                        clustering_method=clustering_method,
                    )

                    progress.progress(90, text="Finalizing results...")

                    st.session_state.theme_results = result_df
                    st.session_state.cluster_summaries = cluster_sums

                    progress.progress(100, text="Complete!")
                    st.success(f"✓ Theme analysis complete! {len(result_df)} rows processed.")

                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                    st.info("**Tip:** If sentence-transformers isn't installed, run: `pip install sentence-transformers`")
                    # Fall back to keyword-only analysis
                    st.warning("Falling back to keyword-only analysis (no BERT)...")
                    try:
                        result_df = df.copy()
                        from utils.text_preprocessing import preprocess_series
                        from utils.theme_engine import keyword_match_theme, detect_tone, detect_policy_indicator

                        raw_texts = df[text_col].fillna('').astype(str).tolist()
                        themes, ubers, confs = [], [], []
                        tones, severities, tone_confs = [], [], []
                        policies, pol_cats, pol_confs = [], [], []
                        kw_themes, kw_confs, matched_kws = [], [], []

                        for text in raw_texts:
                            t, c, kws = keyword_match_theme(text)
                            kw_themes.append(t)
                            kw_confs.append(c)
                            matched_kws.append(', '.join(kws[:5]))

                            theme_data = GRANULAR_THEMES.get(t, {})
                            uber = theme_data.get("uber_theme", "Other")
                            themes.append(t)
                            ubers.append(uber)
                            confs.append(c)

                            tone_l, sev, tc = detect_tone(text)
                            tones.append(tone_l)
                            severities.append(sev)
                            tone_confs.append(tc)

                            pl, pc, pcf = detect_policy_indicator(text)
                            policies.append(pl)
                            pol_cats.append(pc)
                            pol_confs.append(pcf)

                        result_df['keyword_theme'] = kw_themes
                        result_df['keyword_confidence'] = kw_confs
                        result_df['matched_keywords'] = matched_kws
                        result_df['key_theme'] = themes
                        result_df['uber_theme'] = ubers
                        result_df['theme_confidence'] = confs
                        result_df['tone'] = tones
                        result_df['tone_severity'] = severities
                        result_df['tone_confidence'] = tone_confs
                        result_df['policy_indicator'] = policies
                        result_df['policy_category'] = pol_cats
                        result_df['policy_confidence'] = pol_confs
                        result_df['cluster_id'] = -1
                        result_df['cluster_confidence'] = 0.0

                        st.session_state.theme_results = result_df
                        st.session_state.cluster_summaries = {}
                        st.success("✓ Keyword-based analysis complete!")
                    except Exception as e2:
                        st.error(f"Fallback also failed: {e2}")

        # ── Display Results ──
        if st.session_state.theme_results is not None:
            result_df = st.session_state.theme_results

            st.markdown("---")
            st.markdown("### 📊 Theme Analysis Results")

            # Summary metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Unique Themes", result_df['key_theme'].nunique())
            m2.metric("Uber Themes", result_df['uber_theme'].nunique())
            m3.metric("Avg Confidence", f"{result_df['theme_confidence'].mean():.2f}")
            m4.metric("Unclassified", f"{(result_df['key_theme'] == 'unclassified').sum():,}")

            # Theme distribution
            fig_themes = px.bar(
                result_df['uber_theme'].value_counts().reset_index(),
                x='count', y='uber_theme',
                orientation='h',
                color='uber_theme',
                color_discrete_map={k: v['color'] for k, v in UBER_THEMES.items()},
                title="Theme Distribution (Uber Themes)",
            )
            fig_themes.update_layout(template="plotly_dark", showlegend=False,
                                    yaxis=dict(autorange="reversed"), height=400)
            st.plotly_chart(fig_themes, use_container_width=True)

            # Cluster summaries
            if st.session_state.cluster_summaries:
                st.markdown("### 🔬 Discovered Clusters")
                for cid, summary in st.session_state.cluster_summaries.items():
                    with st.expander(f"Cluster {cid} — {summary['size']} items — Keywords: {', '.join(summary['keywords'][:5])}"):
                        st.markdown(f"**Size:** {summary['size']} items")
                        st.markdown(f"**Top Keywords:** {', '.join(summary['keywords'])}")
                        st.markdown("**Example texts:**")
                        for ex in summary['examples']:
                            st.caption(f"→ _{str(ex)[:200]}_")

            # Results table
            st.markdown("### 📋 Results Table")
            display_cols = [text_col, 'key_theme', 'uber_theme', 'theme_confidence',
                          'tone', 'tone_severity', 'matched_keywords']
            display_cols = [c for c in display_cols if c in result_df.columns]
            st.dataframe(result_df[display_cols].head(100), use_container_width=True, height=400)

            st.info("✓ Analysis complete. Proceed to **Theme Normalization** tab to refine mappings.")

# ══════════════════════════════════════════════════════════════════
# TAB 3: THEME NORMALIZATION
# ══════════════════════════════════════════════════════════════════
with tab3:
    if st.session_state.theme_results is None:
        st.warning("Run theme analysis in Tab 2 first.")
    else:
        result_df = st.session_state.theme_results

        st.markdown('<div class="step-header"><h3>🔄 Theme Normalization</h3></div>', unsafe_allow_html=True)
        st.markdown("""
        Normalize granular themes to consistent Uber Themes. This handles cases like
        "shipping returns" and "payment returns" both mapping to the same category.
        """)

        # ── Current mappings ──
        st.markdown("### Current Granular → Uber Theme Mappings")

        unique_themes = result_df['key_theme'].unique()
        norm_data = []
        for theme in sorted(unique_themes):
            current_uber = GRANULAR_THEMES.get(theme, {}).get("uber_theme", "Other")
            if theme in st.session_state.user_theme_map:
                current_uber = st.session_state.user_theme_map[theme]
            count = (result_df['key_theme'] == theme).sum()
            norm_data.append({
                "Granular Theme": theme,
                "Current Uber Theme": current_uber,
                "Count": count,
                "Avg Confidence": result_df[result_df['key_theme'] == theme]['theme_confidence'].mean(),
            })

        norm_df = pd.DataFrame(norm_data).sort_values("Count", ascending=False)
        st.dataframe(norm_df, use_container_width=True, height=350)

        # ── Edit mappings ──
        st.markdown("### ✏️ Edit Theme Normalization")
        st.markdown("Reassign any granular theme to a different Uber Theme:")

        uber_options = list(UBER_THEMES.keys()) + ["Other"]
        edit_cols = st.columns(3)

        with edit_cols[0]:
            theme_to_edit = st.selectbox(
                "Select theme to reassign",
                options=sorted(unique_themes),
            )
        with edit_cols[1]:
            current = GRANULAR_THEMES.get(theme_to_edit, {}).get("uber_theme", "Other")
            if theme_to_edit in st.session_state.user_theme_map:
                current = st.session_state.user_theme_map[theme_to_edit]
            st.text_input("Current Uber Theme", value=current, disabled=True)
        with edit_cols[2]:
            new_uber = st.selectbox("Reassign to", options=uber_options,
                                    index=uber_options.index(current) if current in uber_options else len(uber_options)-1)

        if st.button("Apply Reassignment"):
            st.session_state.user_theme_map[theme_to_edit] = new_uber
            # Update the results dataframe
            mask = result_df['key_theme'] == theme_to_edit
            result_df.loc[mask, 'uber_theme'] = new_uber
            st.session_state.theme_results = result_df
            st.success(f"✓ Reassigned '{theme_to_edit}' → '{new_uber}'")
            st.rerun()

        # ── Bulk edit via JSON ──
        with st.expander("📝 Bulk Edit (JSON)", expanded=False):
            st.markdown("Paste a JSON mapping to override multiple themes at once:")
            bulk_json = st.text_area(
                "JSON mapping",
                value=json.dumps(st.session_state.user_theme_map, indent=2) if st.session_state.user_theme_map else '{\n  "theme_id": "Uber Theme Name"\n}',
                height=200,
            )
            if st.button("Apply Bulk Mapping"):
                try:
                    new_map = json.loads(bulk_json)
                    st.session_state.user_theme_map.update(new_map)
                    for theme_id, uber in new_map.items():
                        mask = result_df['key_theme'] == theme_id
                        result_df.loc[mask, 'uber_theme'] = uber
                    st.session_state.theme_results = result_df
                    st.success(f"✓ Applied {len(new_map)} mappings")
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("Invalid JSON. Please fix and try again.")

        # ── Finalize ──
        st.markdown("---")
        if st.button("✅ Finalize Normalization & Generate Final Dataset", type="primary"):
            st.session_state.final_df = result_df.copy()
            st.success("✓ Final dataset generated! Proceed to Tone & Policy tab or Visualizations.")

# ══════════════════════════════════════════════════════════════════
# TAB 4: TONE & POLICY
# ══════════════════════════════════════════════════════════════════
with tab4:
    if st.session_state.theme_results is None:
        st.warning("Run theme analysis in Tab 2 first.")
    else:
        result_df = st.session_state.theme_results

        # ── Tone Analysis ──
        st.markdown('<div class="step-header"><h3>💬 Tone / Sentiment Analysis</h3></div>', unsafe_allow_html=True)

        # Show tone mappings
        with st.expander("📋 View / Edit Tone Mappings", expanded=False):
            for tone_id, data in TONE_MAPPINGS.items():
                col_t1, col_t2, col_t3 = st.columns([1, 2, 1])
                col_t1.markdown(f"**{data['label']}**")
                col_t2.caption(f"Keywords: {', '.join(data['keywords'][:8])}")
                col_t3.markdown(f"Severity: `{data['severity']}`")

            st.markdown("**Add custom tone keywords:**")
            ct1, ct2 = st.columns(2)
            with ct1:
                custom_tone = st.selectbox("Tone category", list(TONE_MAPPINGS.keys()))
            with ct2:
                custom_tone_kws = st.text_input("Additional keywords (comma-separated)")
            if st.button("Add Tone Keywords"):
                if custom_tone_kws:
                    new_kws = [k.strip() for k in custom_tone_kws.split(',')]
                    st.session_state.user_tone_map[custom_tone] = new_kws
                    st.success(f"✓ Added {len(new_kws)} keywords to {custom_tone}")

        # Tone distribution
        if 'tone' in result_df.columns:
            st.markdown("### Tone Distribution")
            tone_counts = result_df['tone'].value_counts()
            fig_tone = px.pie(
                values=tone_counts.values,
                names=tone_counts.index,
                title="Customer Tone Breakdown",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_tone.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig_tone, use_container_width=True)

            # Severity breakdown
            if 'tone_severity' in result_df.columns:
                sev_counts = result_df['tone_severity'].value_counts()
                st.markdown("### Severity Levels")
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("🔴 Critical", sev_counts.get('critical', 0))
                s2.metric("🟠 High", sev_counts.get('high', 0))
                s3.metric("🟡 Medium", sev_counts.get('medium', 0))
                s4.metric("🟢 Low / None", sev_counts.get('low', 0) + sev_counts.get('none', 0))

        # ── Policy Change Detection ──
        st.markdown("---")
        st.markdown('<div class="step-header"><h3>📜 Policy Change Detection</h3></div>', unsafe_allow_html=True)

        with st.expander("📋 View / Edit Policy Indicators", expanded=False):
            for ind_id, data in POLICY_INDICATORS.items():
                col_p1, col_p2 = st.columns([1, 2])
                col_p1.markdown(f"**{data['label']}**")
                col_p2.caption(f"Keywords: {', '.join(data['keywords'][:6])}")

            st.markdown("**Add custom policy keywords:**")
            cp1, cp2 = st.columns(2)
            with cp1:
                custom_policy = st.selectbox("Policy category", list(POLICY_INDICATORS.keys()))
            with cp2:
                custom_policy_kws = st.text_input("Additional policy keywords (comma-separated)")
            if st.button("Add Policy Keywords"):
                if custom_policy_kws:
                    new_kws = [k.strip() for k in custom_policy_kws.split(',')]
                    st.session_state.user_policy_map[custom_policy] = new_kws
                    st.success(f"✓ Added {len(new_kws)} keywords to {custom_policy}")

        if 'policy_indicator' in result_df.columns:
            policy_detected = result_df[result_df['policy_indicator'] != 'None']
            st.markdown(f"### Policy-Related Mentions: {len(policy_detected):,} / {len(result_df):,}")

            if len(policy_detected) > 0:
                fig_pol = px.bar(
                    policy_detected['policy_indicator'].value_counts().reset_index(),
                    x='count', y='policy_indicator',
                    orientation='h',
                    title="Policy Indicator Breakdown",
                    color='policy_indicator',
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                fig_pol.update_layout(template="plotly_dark", showlegend=False,
                                     yaxis=dict(autorange="reversed"), height=300)
                st.plotly_chart(fig_pol, use_container_width=True)

                st.markdown("**Sample policy-related feedback:**")
                text_col = st.session_state.text_column
                for _, row in policy_detected.head(5).iterrows():
                    st.caption(f"[{row['policy_indicator']}] _{str(row[text_col])[:200]}_")

# ══════════════════════════════════════════════════════════════════
# TAB 5: VISUALIZATIONS DASHBOARD
# ══════════════════════════════════════════════════════════════════
with tab5:
    viz_df = st.session_state.final_df if st.session_state.final_df is not None else st.session_state.theme_results

    if viz_df is None:
        st.warning("Run theme analysis first to see visualizations.")
    else:
        st.markdown('<div class="step-header"><h3>📈 Theme Modelling Dashboard</h3></div>', unsafe_allow_html=True)

        # ── Key Metrics ──
        vm1, vm2, vm3, vm4, vm5 = st.columns(5)
        vm1.metric("Total Records", f"{len(viz_df):,}")
        vm2.metric("Themes Found", viz_df['uber_theme'].nunique())
        vm3.metric("Avg Confidence", f"{viz_df['theme_confidence'].mean():.2f}")
        if 'tone_severity' in viz_df.columns:
            critical = (viz_df['tone_severity'].isin(['critical', 'high'])).sum()
            vm4.metric("High Severity", f"{critical:,}")
        if 'policy_indicator' in viz_df.columns:
            policy_cnt = (viz_df['policy_indicator'] != 'None').sum()
            vm5.metric("Policy Mentions", f"{policy_cnt:,}")

        st.markdown("---")

        # ── 1. Uber Theme Treemap ──
        st.markdown("### 🗺️ Theme Landscape")
        theme_agg = viz_df.groupby(['uber_theme', 'key_theme']).size().reset_index(name='count')
        fig_tree = px.treemap(
            theme_agg,
            path=['uber_theme', 'key_theme'],
            values='count',
            color='uber_theme',
            color_discrete_map={k: v['color'] for k, v in UBER_THEMES.items()},
            title="Theme Hierarchy — Uber Themes → Granular Themes",
        )
        fig_tree.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig_tree, use_container_width=True)

        # ── 2. Theme × Tone Heatmap ──
        if 'tone' in viz_df.columns:
            st.markdown("### 🔥 Theme × Tone Heatmap")
            cross = pd.crosstab(viz_df['uber_theme'], viz_df['tone'])
            fig_heat = px.imshow(
                cross.values,
                x=cross.columns.tolist(),
                y=cross.index.tolist(),
                color_continuous_scale='YlOrRd',
                title="Which themes have which tones?",
                text_auto=True,
            )
            fig_heat.update_layout(template="plotly_dark", height=450)
            st.plotly_chart(fig_heat, use_container_width=True)

        # ── 3. Confidence Distribution ──
        v_cols = st.columns(2)
        with v_cols[0]:
            fig_conf = px.histogram(
                viz_df, x='theme_confidence', nbins=50,
                title="Theme Confidence Distribution",
                color_discrete_sequence=['#e8a838'],
            )
            fig_conf.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig_conf, use_container_width=True)

        with v_cols[1]:
            fig_uber_bar = px.bar(
                viz_df['uber_theme'].value_counts().reset_index(),
                x='count', y='uber_theme',
                orientation='h',
                color='uber_theme',
                color_discrete_map={k: v['color'] for k, v in UBER_THEMES.items()},
                title="Volume by Uber Theme",
            )
            fig_uber_bar.update_layout(template="plotly_dark", showlegend=False,
                                      yaxis=dict(autorange="reversed"), height=350)
            st.plotly_chart(fig_uber_bar, use_container_width=True)

        # ── 4. Time-based analysis ──
        datetime_cols = []
        for col in viz_df.columns:
            if pd.api.types.is_datetime64_any_dtype(viz_df[col]):
                datetime_cols.append(col)
            elif viz_df[col].dtype == 'object':
                try:
                    sample = pd.to_datetime(viz_df[col].head(30), errors='coerce')
                    if sample.notna().mean() > 0.5:
                        datetime_cols.append(col)
                except Exception:
                    pass

        if datetime_cols:
            st.markdown("### 📅 Time-Based Theme Trends")
            time_col = st.selectbox("Select date column", datetime_cols)

            try:
                viz_df['_date'] = pd.to_datetime(viz_df[time_col], errors='coerce')
                viz_df['_period'] = viz_df['_date'].dt.to_period('W').astype(str)

                time_theme = viz_df.groupby(['_period', 'uber_theme']).size().reset_index(name='count')
                fig_time = px.area(
                    time_theme, x='_period', y='count', color='uber_theme',
                    color_discrete_map={k: v['color'] for k, v in UBER_THEMES.items()},
                    title="Theme Volume Over Time (Weekly)",
                )
                fig_time.update_layout(template="plotly_dark", height=400,
                                      xaxis=dict(tickangle=-45))
                st.plotly_chart(fig_time, use_container_width=True)

                # Tone over time
                if 'tone' in viz_df.columns:
                    time_tone = viz_df.groupby(['_period', 'tone']).size().reset_index(name='count')
                    fig_tone_time = px.line(
                        time_tone, x='_period', y='count', color='tone',
                        title="Tone Trends Over Time",
                        color_discrete_sequence=px.colors.qualitative.Set2,
                    )
                    fig_tone_time.update_layout(template="plotly_dark", height=350,
                                               xaxis=dict(tickangle=-45))
                    st.plotly_chart(fig_tone_time, use_container_width=True)

                viz_df.drop(columns=['_date', '_period'], inplace=True, errors='ignore')
            except Exception as e:
                st.warning(f"Could not parse dates: {e}")

        # ── 5. Sunburst ──
        if 'tone' in viz_df.columns:
            st.markdown("### 🌀 Theme → Tone Sunburst")
            sun_data = viz_df.groupby(['uber_theme', 'key_theme', 'tone']).size().reset_index(name='count')
            fig_sun = px.sunburst(
                sun_data, path=['uber_theme', 'key_theme', 'tone'],
                values='count',
                color='uber_theme',
                color_discrete_map={k: v['color'] for k, v in UBER_THEMES.items()},
                title="Hierarchical View: Uber Theme → Granular Theme → Tone",
            )
            fig_sun.update_layout(template="plotly_dark", height=550)
            st.plotly_chart(fig_sun, use_container_width=True)

        # ── 6. Top granular themes ──
        st.markdown("### 🏷️ Top 20 Granular Themes")
        top_themes = viz_df['key_theme'].value_counts().head(20).reset_index()
        top_themes.columns = ['theme', 'count']
        fig_gran = px.bar(
            top_themes, x='count', y='theme', orientation='h',
            color='count', color_continuous_scale='Oranges',
            title="Most Common Granular Themes",
        )
        fig_gran.update_layout(template="plotly_dark", showlegend=False,
                              yaxis=dict(autorange="reversed"), height=500)
        st.plotly_chart(fig_gran, use_container_width=True)

        # ── 7. Download Final Dataset ──
        st.markdown("---")
        st.markdown("### 💾 Download Final Dataset")

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            csv_buffer = io.StringIO()
            viz_df.to_csv(csv_buffer, index=False)
            st.download_button(
                "⬇ Download as CSV",
                csv_buffer.getvalue(),
                file_name="theme_analysis_results.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl_col2:
            excel_buffer = io.BytesIO()
            viz_df.to_excel(excel_buffer, index=False, engine='openpyxl')
            st.download_button(
                "⬇ Download as Excel",
                excel_buffer.getvalue(),
                file_name="theme_analysis_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.markdown(f"""
        **Final dataset includes {len(viz_df.columns)} columns:**
        All original features + `key_theme`, `uber_theme`, `theme_confidence`,
        `tone`, `tone_severity`, `tone_confidence`, `policy_indicator`,
        `policy_category`, `policy_confidence`, `matched_keywords`,
        `keyword_theme`, `keyword_confidence`, `cluster_id`, `cluster_confidence`
        """)
