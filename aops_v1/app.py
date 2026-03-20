"""
app.py — eBay IAC Artifact Vault
Enterprise-grade artifact management portal built with Streamlit.
"""

import streamlit as st
import json
import os
from datetime import datetime
from data_manager import (
    load_data, save_data, get_stats,
    add_team, rename_team, delete_team,
    add_member, rename_member, delete_member,
    add_artifact, rename_artifact, delete_artifact,
    save_uploaded_file, ARTIFACT_TYPES, DATA_FILE
)

# ════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="eBay IAC · Artifact Vault",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════════════
# CUSTOM CSS — Enterprise dark theme with eBay brand accents
# ════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,700;1,9..40,300&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
    --ebay-blue: #0064D2;
    --ebay-red: #E53238;
    --ebay-yellow: #F5AF02;
    --ebay-green: #86B817;
    --bg-primary: #0a0e17;
    --bg-card: #111827;
    --bg-card-hover: #1a2332;
    --border-subtle: #1e293b;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-glow: rgba(0, 100, 210, 0.15);
}

/* ── Global ─────────────────────────────────────────── */
.stApp {
    font-family: 'DM Sans', sans-serif;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070b14 0%, #0d1321 100%);
    border-right: 1px solid var(--border-subtle);
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li {
    color: var(--text-secondary);
}

/* ── Header Banner ──────────────────────────────────── */
.vault-header {
    background: linear-gradient(135deg, #0a0e17 0%, #111d35 50%, #0a0e17 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.vault-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--ebay-blue), var(--ebay-red), var(--ebay-yellow), var(--ebay-green));
}
.vault-header h1 {
    font-family: 'DM Sans', sans-serif;
    font-weight: 700; font-size: 2.2rem;
    color: var(--text-primary); margin: 0 0 0.3rem 0;
    letter-spacing: -0.5px;
}
.vault-header .subtitle {
    color: var(--text-muted); font-size: 0.95rem;
    font-weight: 300; letter-spacing: 0.5px;
}
.vault-header .org-badge {
    display: inline-block;
    background: rgba(0,100,210,0.12);
    border: 1px solid rgba(0,100,210,0.3);
    color: #60a5fa;
    padding: 0.25rem 0.85rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

/* ── Stat Cards ─────────────────────────────────────── */
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    transition: all 0.25s ease;
}
.stat-card:hover {
    border-color: rgba(0,100,210,0.4);
    box-shadow: 0 0 20px var(--accent-glow);
    transform: translateY(-2px);
}
.stat-number {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.4rem; font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1.1;
}
.stat-label {
    color: var(--text-muted); font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-top: 0.35rem; font-weight: 500;
}

/* ── Team Section ───────────────────────────────────── */
.team-block {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.2rem;
    transition: all 0.2s ease;
}
.team-block:hover {
    border-color: rgba(0,100,210,0.3);
}
.team-title {
    font-size: 1.35rem; font-weight: 700;
    color: var(--text-primary);
    display: flex; align-items: center; gap: 0.6rem;
}
.team-meta {
    color: var(--text-muted); font-size: 0.78rem;
    margin-top: 0.2rem;
}

/* ── Member Card ────────────────────────────────────── */
.member-card {
    background: linear-gradient(135deg, #0f172a 0%, #131d2e 100%);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
}
.member-name {
    font-size: 1.05rem; font-weight: 600;
    color: #e2e8f0;
    display: flex; align-items: center; gap: 0.5rem;
}

/* ── Artifact Row ───────────────────────────────────── */
.artifact-row {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(30, 41, 59, 0.7);
    border-radius: 10px;
    padding: 0.85rem 1.2rem;
    margin: 0.45rem 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.2s ease;
}
.artifact-row:hover {
    border-color: rgba(0,100,210,0.35);
    background: rgba(17, 24, 39, 0.9);
}
.artifact-icon {
    font-size: 1.3rem;
    margin-right: 0.6rem;
}
.artifact-name {
    color: #e2e8f0;
    font-weight: 500;
    font-size: 0.92rem;
}
.artifact-type-badge {
    display: inline-block;
    padding: 0.15rem 0.55rem;
    border-radius: 6px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.badge-link { background: rgba(96,165,250,0.15); color: #60a5fa; }
.badge-file { background: rgba(134,184,23,0.15); color: #86B817; }
.artifact-date {
    color: var(--text-muted); font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Sidebar Branding ───────────────────────────────── */
.sidebar-brand {
    text-align: center;
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid var(--border-subtle);
    margin-bottom: 1rem;
}
.sidebar-brand .logo-text {
    font-size: 1.4rem; font-weight: 700;
    letter-spacing: -0.3px;
}
.sidebar-brand .logo-sub {
    font-size: 0.7rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 2px;
    margin-top: 0.2rem;
}

.color-e { color: var(--ebay-red); }
.color-b { color: var(--ebay-blue); }
.color-a { color: var(--ebay-yellow); }
.color-y { color: var(--ebay-green); }

/* ── Tree View ──────────────────────────────────────── */
.tree-org {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.8;
    padding: 1rem 1.2rem;
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    max-height: 65vh;
    overflow-y: auto;
}
.tree-org .t-org { color: #f59e0b; font-weight: 700; }
.tree-org .t-team { color: #60a5fa; font-weight: 600; }
.tree-org .t-member { color: #a78bfa; }
.tree-org .t-artifact { color: var(--text-muted); }

/* ── Empty State ────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: var(--text-muted);
}
.empty-state .empty-icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.4; }
.empty-state p { font-size: 0.9rem; max-width: 320px; margin: 0 auto; }

/* ── Misc ───────────────────────────────────────────── */
.divider {
    height: 1px;
    background: var(--border-subtle);
    margin: 1.5rem 0;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ════════════════════════════════════════════════════════════════════════
if "data" not in st.session_state:
    st.session_state.data = load_data()
if "show_delete_modal" not in st.session_state:
    st.session_state.show_delete_modal = None
if "current_view" not in st.session_state:
    st.session_state.current_view = "dashboard"


def refresh():
    st.session_state.data = load_data()


# ════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo-text">
            <span class="color-e">e</span><span class="color-b">B</span><span class="color-a">a</span><span class="color-y">y</span> Vault
        </div>
        <div class="logo-sub">Infrastructure &amp; Cloud</div>
    </div>
    """, unsafe_allow_html=True)

    nav = st.radio(
        "Navigation",
        ["🏠 Dashboard", "🏗️ Manage Teams", "👤 Manage Members", "📦 Add Artifacts", "🗑️ Admin Delete", "🌳 Tree View", "💾 Backup & Export"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Quick stats in sidebar
    data = st.session_state.data
    stats = get_stats(data)
    st.caption("QUICK STATS")
    st.markdown(f"**{stats['total_teams']}** Teams · **{stats['total_members']}** Members · **{stats['total_artifacts']}** Artifacts")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.caption(f"Last synced: {data.get('last_updated', 'N/A')}")


# ════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════
def classify_link(url: str) -> str:
    url_lower = url.lower()
    if "github" in url_lower:
        return "github_link"
    if "tableau" in url_lower:
        return "tableau_link"
    if "zeta" in url_lower:
        return "zeta_link"
    return "generic_link"


def classify_file(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("ppt", "pptx"):
        return "powerpoint"
    if ext in ("xls", "xlsx", "csv"):
        return "excel"
    if ext == "pdf":
        return "pdf"
    return "other_file"


def render_artifact_badge(atype: str) -> str:
    info = ARTIFACT_TYPES.get(atype, {"icon": "📎", "label": "File"})
    is_link = "link" in atype
    badge_class = "badge-link" if is_link else "badge-file"
    return f'{info["icon"]} <span class="artifact-type-badge {badge_class}">{info["label"]}</span>'


# ════════════════════════════════════════════════════════════════════════
# VIEWS
# ════════════════════════════════════════════════════════════════════════

# ── DASHBOARD ───────────────────────────────────────────────────────────
if nav == "🏠 Dashboard":
    data = st.session_state.data
    stats = get_stats(data)

    st.markdown("""
    <div class="vault-header">
        <div class="org-badge">Enterprise Platform</div>
        <h1>🏛️ Artifact Vault</h1>
        <div class="subtitle">Centralized artifact management for eBay Infrastructure &amp; Cloud teams</div>
    </div>
    """, unsafe_allow_html=True)

    # Stat cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{stats['total_teams']}</div>
            <div class="stat-label">Teams</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{stats['total_members']}</div>
            <div class="stat-label">Members</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{stats['total_artifacts']}</div>
            <div class="stat-label">Artifacts</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        link_count = sum(v for k, v in stats['type_counts'].items() if 'link' in k)
        st.markdown(f"""<div class="stat-card">
            <div class="stat-number">{link_count}</div>
            <div class="stat-label">Links</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Hierarchical Browse ─────────────────────────────────────────────
    if not data["teams"]:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <p>No teams yet. Head over to <strong>Manage Teams</strong> to create your first team.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for team_name, team_data in data["teams"].items():
            member_count = len(team_data["members"])
            artifact_count = sum(len(m["artifacts"]) for m in team_data["members"].values())

            st.markdown(f"""
            <div class="team-block">
                <div class="team-title">📁 {team_name}</div>
                <div class="team-meta">{member_count} members · {artifact_count} artifacts · Created {team_data.get('created_at', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)

            if team_data["members"]:
                cols_per_row = 2
                members_list = list(team_data["members"].items())
                for i in range(0, len(members_list), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        idx = i + j
                        if idx >= len(members_list):
                            break
                        m_name, m_data = members_list[idx]
                        with col:
                            st.markdown(f"""
                            <div class="member-card">
                                <div class="member-name">👤 {m_name}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            if m_data["artifacts"]:
                                for art in m_data["artifacts"]:
                                    info = ARTIFACT_TYPES.get(art.get("type", "other_file"), {"icon": "📎", "label": "File"})
                                    is_link = "link" in art.get("type", "")
                                    badge_cls = "badge-link" if is_link else "badge-file"
                                    value_display = ""
                                    if art.get("url"):
                                        value_display = f'<a href="{art["url"]}" target="_blank" style="color:#60a5fa;font-size:0.78rem;text-decoration:none;">Open ↗</a>'
                                    elif art.get("file_path"):
                                        value_display = f'<span style="color:var(--text-muted);font-size:0.75rem;">📄 Local file</span>'

                                    st.markdown(f"""
                                    <div class="artifact-row">
                                        <div>
                                            <span class="artifact-icon">{info['icon']}</span>
                                            <span class="artifact-name">{art.get('name', 'Untitled')}</span>
                                            <span class="artifact-type-badge {badge_cls}">{info['label']}</span>
                                        </div>
                                        <div style="display:flex;align-items:center;gap:1rem;">
                                            {value_display}
                                            <span class="artifact-date">{art.get('created_at', '')}</span>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.caption("   No artifacts yet.")


# ── MANAGE TEAMS ────────────────────────────────────────────────────────
elif nav == "🏗️ Manage Teams":
    st.markdown("""
    <div class="vault-header">
        <div class="org-badge">Administration</div>
        <h1>🏗️ Manage Teams</h1>
        <div class="subtitle">Create, rename, and organize your IAC teams</div>
    </div>
    """, unsafe_allow_html=True)

    # Add team
    st.subheader("Add New Team")
    with st.form("add_team_form", clear_on_submit=True):
        new_team = st.text_input("Team Name", placeholder="e.g., Cloud Platform, SRE, DevOps")
        submitted = st.form_submit_button("➕ Add Team", use_container_width=True)
        if submitted and new_team:
            ok, msg = add_team(new_team)
            refresh()
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Rename team
    data = st.session_state.data
    teams = list(data["teams"].keys())
    if teams:
        st.subheader("Rename Team")
        with st.form("rename_team_form", clear_on_submit=True):
            sel_team = st.selectbox("Select Team", teams, key="rename_team_sel")
            new_name = st.text_input("New Name", placeholder="Enter new team name")
            submitted = st.form_submit_button("✏️ Rename Team", use_container_width=True)
            if submitted and new_name:
                ok, msg = rename_team(sel_team, new_name)
                refresh()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.subheader("Existing Teams")
        for t in teams:
            m_count = len(data["teams"][t]["members"])
            st.markdown(f"""
            <div class="team-block">
                <div class="team-title">📁 {t}</div>
                <div class="team-meta">{m_count} members · Created {data['teams'][t].get('created_at','N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No teams created yet. Add one above!")


# ── MANAGE MEMBERS ──────────────────────────────────────────────────────
elif nav == "👤 Manage Members":
    st.markdown("""
    <div class="vault-header">
        <div class="org-badge">Administration</div>
        <h1>👤 Manage Members</h1>
        <div class="subtitle">Add and organize team members across IAC</div>
    </div>
    """, unsafe_allow_html=True)

    data = st.session_state.data
    teams = list(data["teams"].keys())

    if not teams:
        st.warning("Create a team first in **Manage Teams**.")
    else:
        st.subheader("Add New Member")
        with st.form("add_member_form", clear_on_submit=True):
            sel_team = st.selectbox("Select Team", teams, key="add_member_team")
            member_name = st.text_input("Member Name", placeholder="e.g., John Doe")
            submitted = st.form_submit_button("➕ Add Member", use_container_width=True)
            if submitted and member_name:
                ok, msg = add_member(sel_team, member_name)
                refresh()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Rename member
        st.subheader("Rename Member")
        with st.form("rename_member_form", clear_on_submit=True):
            sel_team_r = st.selectbox("Select Team", teams, key="rename_member_team")
            members_in_team = list(data["teams"].get(sel_team_r, {}).get("members", {}).keys())
            if members_in_team:
                sel_member = st.selectbox("Select Member", members_in_team, key="rename_member_sel")
                new_mname = st.text_input("New Name", placeholder="Enter new member name")
                submitted = st.form_submit_button("✏️ Rename Member", use_container_width=True)
                if submitted and new_mname:
                    ok, msg = rename_member(sel_team_r, sel_member, new_mname)
                    refresh()
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                st.info("No members in this team yet.")
                st.form_submit_button("✏️ Rename Member", disabled=True, use_container_width=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Show members by team
        st.subheader("Current Members")
        for t_name, t_data in data["teams"].items():
            st.markdown(f"**📁 {t_name}**")
            if t_data["members"]:
                for m_name, m_data in t_data["members"].items():
                    a_count = len(m_data["artifacts"])
                    st.markdown(f"""
                    <div class="member-card">
                        <div class="member-name">👤 {m_name} <span style="color:var(--text-muted);font-size:0.75rem;margin-left:0.5rem;">{a_count} artifacts</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("   No members yet.")


# ── ADD ARTIFACTS ───────────────────────────────────────────────────────
elif nav == "📦 Add Artifacts":
    st.markdown("""
    <div class="vault-header">
        <div class="org-badge">Artifacts</div>
        <h1>📦 Add Artifacts</h1>
        <div class="subtitle">Upload files or add links — Zeta, GitHub, Tableau, and more</div>
    </div>
    """, unsafe_allow_html=True)

    data = st.session_state.data
    teams = list(data["teams"].keys())

    if not teams:
        st.warning("Create a team and add members first.")
    else:
        sel_team = st.selectbox("Select Team", teams, key="art_team")
        members = list(data["teams"].get(sel_team, {}).get("members", {}).keys())

        if not members:
            st.warning(f"No members in **{sel_team}**. Add members first.")
        else:
            sel_member = st.selectbox("Select Member", members, key="art_member")

            tab_link, tab_upload, tab_rename = st.tabs(["🔗 Add Links", "📁 Upload Files", "✏️ Rename Artifacts"])

            # ── Add Links ───────────────────────────────────────────────
            with tab_link:
                st.markdown("Add links to Zeta dashboards, GitHub repos, Tableau views, or any URL.")
                with st.form("add_link_form", clear_on_submit=True):
                    link_name = st.text_input("Artifact Name", placeholder="e.g., Q4 Revenue Dashboard")
                    link_url = st.text_input("URL", placeholder="https://...")
                    link_notes = st.text_area("Notes (optional)", placeholder="Brief description...", height=80)
                    submitted = st.form_submit_button("🔗 Add Link", use_container_width=True)
                    if submitted and link_name and link_url:
                        atype = classify_link(link_url)
                        artifact = {
                            "name": link_name.strip(),
                            "type": atype,
                            "url": link_url.strip(),
                            "notes": link_notes.strip(),
                        }
                        ok, msg = add_artifact(sel_team, sel_member, artifact)
                        refresh()
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)

            # ── Upload Files ────────────────────────────────────────────
            with tab_upload:
                st.markdown("Upload PowerPoint, Excel, PDF, or any files. **Multi-upload supported.**")
                uploaded_files = st.file_uploader(
                    "Choose files",
                    accept_multiple_files=True,
                    type=["pptx", "ppt", "xlsx", "xls", "csv", "pdf", "doc", "docx", "txt", "png", "jpg", "zip"],
                    key="multi_upload"
                )
                upload_notes = st.text_input("Notes for all uploads (optional)", key="upload_notes_input")
                if st.button("📤 Upload All", use_container_width=True, key="upload_btn"):
                    if uploaded_files:
                        success_count = 0
                        for uf in uploaded_files:
                            file_path = save_uploaded_file(uf)
                            atype = classify_file(uf.name)
                            artifact = {
                                "name": uf.name,
                                "type": atype,
                                "file_path": file_path,
                                "notes": upload_notes.strip(),
                                "size_bytes": uf.size,
                            }
                            ok, msg = add_artifact(sel_team, sel_member, artifact)
                            if ok:
                                success_count += 1
                        refresh()
                        st.success(f"Uploaded {success_count}/{len(uploaded_files)} files successfully.")
                    else:
                        st.warning("No files selected.")

            # ── Rename Artifacts ────────────────────────────────────────
            with tab_rename:
                data = st.session_state.data  # re-read
                artifacts = data["teams"].get(sel_team, {}).get("members", {}).get(sel_member, {}).get("artifacts", [])
                if artifacts:
                    art_options = {f"{a['name']} ({a['id']})": a['id'] for a in artifacts}
                    with st.form("rename_art_form", clear_on_submit=True):
                        sel_art = st.selectbox("Select Artifact", list(art_options.keys()))
                        new_art_name = st.text_input("New Name", placeholder="Enter new artifact name")
                        submitted = st.form_submit_button("✏️ Rename Artifact", use_container_width=True)
                        if submitted and new_art_name:
                            art_id = art_options[sel_art]
                            ok, msg = rename_artifact(sel_team, sel_member, art_id, new_art_name)
                            refresh()
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                else:
                    st.info("No artifacts to rename for this member.")


# ── ADMIN DELETE ────────────────────────────────────────────────────────
elif nav == "🗑️ Admin Delete":
    st.markdown("""
    <div class="vault-header">
        <div class="org-badge">Restricted Access</div>
        <h1>🗑️ Admin Delete</h1>
        <div class="subtitle">Delete operations require admin password authentication</div>
    </div>
    """, unsafe_allow_html=True)

    st.warning("⚠️ All delete operations are **irreversible** and require the admin password.")

    data = st.session_state.data
    teams = list(data["teams"].keys())

    del_target = st.radio("What to delete?", ["Team", "Member", "Artifact"], horizontal=True)

    if del_target == "Team":
        with st.form("delete_team_form"):
            if teams:
                sel = st.selectbox("Select Team to Delete", teams)
                pwd = st.text_input("Admin Password", type="password")
                submitted = st.form_submit_button("🗑️ Delete Team", use_container_width=True)
                if submitted:
                    ok, msg = delete_team(sel, pwd)
                    refresh()
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            else:
                st.info("No teams to delete.")
                st.form_submit_button("🗑️ Delete Team", disabled=True)

    elif del_target == "Member":
        with st.form("delete_member_form"):
            if teams:
                sel_team = st.selectbox("Team", teams, key="del_mem_team")
                members = list(data["teams"].get(sel_team, {}).get("members", {}).keys())
                if members:
                    sel_member = st.selectbox("Member", members)
                    pwd = st.text_input("Admin Password", type="password")
                    submitted = st.form_submit_button("🗑️ Delete Member", use_container_width=True)
                    if submitted:
                        ok, msg = delete_member(sel_team, sel_member, pwd)
                        refresh()
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                else:
                    st.info("No members in this team.")
                    st.form_submit_button("🗑️ Delete Member", disabled=True)
            else:
                st.info("No teams available.")
                st.form_submit_button("🗑️ Delete Member", disabled=True)

    elif del_target == "Artifact":
        with st.form("delete_artifact_form"):
            if teams:
                sel_team = st.selectbox("Team", teams, key="del_art_team")
                members = list(data["teams"].get(sel_team, {}).get("members", {}).keys())
                if members:
                    sel_member = st.selectbox("Member", members, key="del_art_mem")
                    arts = data["teams"][sel_team]["members"][sel_member]["artifacts"]
                    if arts:
                        art_opts = {f"{a['name']} ({a['id']})": a["id"] for a in arts}
                        sel_art = st.selectbox("Artifact", list(art_opts.keys()))
                        pwd = st.text_input("Admin Password", type="password")
                        submitted = st.form_submit_button("🗑️ Delete Artifact", use_container_width=True)
                        if submitted:
                            ok, msg = delete_artifact(sel_team, sel_member, art_opts[sel_art], pwd)
                            refresh()
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
                    else:
                        st.info("No artifacts for this member.")
                        st.form_submit_button("🗑️ Delete Artifact", disabled=True)
                else:
                    st.info("No members in this team.")
                    st.form_submit_button("🗑️ Delete Artifact", disabled=True)
            else:
                st.info("No teams available.")
                st.form_submit_button("🗑️ Delete Artifact", disabled=True)


# ── TREE VIEW ───────────────────────────────────────────────────────────
elif nav == "🌳 Tree View":
    st.markdown("""
    <div class="vault-header">
        <div class="org-badge">Hierarchy</div>
        <h1>🌳 Organization Tree</h1>
        <div class="subtitle">Full hierarchical view of eBay IAC — teams, members, and all artifacts</div>
    </div>
    """, unsafe_allow_html=True)

    data = st.session_state.data
    lines = [f'<span class="t-org">🏢 {data["organization"]}</span>']

    team_names = list(data["teams"].keys())
    for ti, (t_name, t_data) in enumerate(data["teams"].items()):
        is_last_team = ti == len(team_names) - 1
        t_prefix = "└── " if is_last_team else "├── "
        t_cont = "    " if is_last_team else "│   "
        lines.append(f'{t_prefix}<span class="t-team">📁 {t_name}</span>')

        member_names = list(t_data["members"].keys())
        for mi, (m_name, m_data) in enumerate(t_data["members"].items()):
            is_last_member = mi == len(member_names) - 1
            m_prefix = "└── " if is_last_member else "├── "
            m_cont = "    " if is_last_member else "│   "
            lines.append(f'{t_cont}{m_prefix}<span class="t-member">👤 {m_name}</span>')

            for ai, art in enumerate(m_data["artifacts"]):
                is_last_art = ai == len(m_data["artifacts"]) - 1
                a_prefix = "└── " if is_last_art else "├── "
                icon = ARTIFACT_TYPES.get(art.get("type", "other_file"), {"icon": "📎"})["icon"]
                lines.append(f'{t_cont}{m_cont}{a_prefix}<span class="t-artifact">{icon} {art.get("name", "Untitled")}</span>')

    if len(lines) == 1:
        lines.append('    <span class="t-artifact">(empty — add teams to get started)</span>')

    tree_html = "<br>".join(lines)
    st.markdown(f'<div class="tree-org">{tree_html}</div>', unsafe_allow_html=True)


# ── BACKUP & EXPORT ─────────────────────────────────────────────────────
elif nav == "💾 Backup & Export":
    st.markdown("""
    <div class="vault-header">
        <div class="org-badge">Data Management</div>
        <h1>💾 Backup &amp; Export</h1>
        <div class="subtitle">Download your vault data as JSON — auto-backup runs on every change</div>
    </div>
    """, unsafe_allow_html=True)

    data = st.session_state.data
    stats = get_stats(data)

    st.subheader("Current Vault Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Teams", stats["total_teams"])
    c2.metric("Members", stats["total_members"])
    c3.metric("Artifacts", stats["total_artifacts"])

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.subheader("Download Full Backup")
    json_str = json.dumps(data, indent=2, default=str)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="⬇️ Download vault_data.json",
        data=json_str,
        file_name=f"ebay_iac_vault_backup_{ts}.json",
        mime="application/json",
        use_container_width=True,
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Show raw JSON
    st.subheader("Raw Data Preview")
    with st.expander("View JSON", expanded=False):
        st.json(data)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.subheader("Auto-Backup Info")
    st.info("Every change to the vault automatically saves a timestamped backup to `data/backups/`. The system retains the 10 most recent backups.")

    # List backups
    backup_dir = "data/backups"
    if os.path.exists(backup_dir):
        backups = sorted(os.listdir(backup_dir), reverse=True)
        if backups:
            st.caption(f"Found {len(backups)} backup(s):")
            for b in backups[:10]:
                st.text(f"  📄 {b}")
