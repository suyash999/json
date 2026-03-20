"""
app.py — eBay IAC Artifact Vault v3
Tree-first design. Clean. No jargon.
"""

import streamlit as st
import streamlit.components.v1 as components
import json, os
from datetime import datetime
from data_manager import (
    load_data, save_data, get_stats,
    add_team, rename_team, delete_team,
    add_member, rename_member, delete_member,
    add_artifact, rename_artifact, delete_artifact,
    save_uploaded_file, classify_link, classify_file,
    load_from_google_sheet,
    ARTIFACT_TYPES, DATA_FILE
)
from tree_renderer import generate_tree_html
from google_sync import get_sync_status, is_sync_available, sync_to_sheet

# ════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="eBay IAC · Artifact Vault",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ebay-red: #E53238;
    --ebay-blue: #0064D2;
    --ebay-yellow: #F5AF02;
    --ebay-green: #86B817;
}

.stApp { font-family: 'Inter', -apple-system, sans-serif; }

section[data-testid="stSidebar"] {
    background: #1a1f2e !important;
}
section[data-testid="stSidebar"] * { color: #c8cdd6 !important; }
section[data-testid="stSidebar"] .stRadio label:hover { color: #fff !important; }

/* Header */
.hdr {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 1.5rem 2rem;
    margin-bottom: 1rem;
    position: relative; overflow: hidden;
}
.hdr::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #E53238, #0064D2, #F5AF02, #86B817);
    border-radius: 10px 10px 0 0;
}
.hdr .ey { font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.8px; color: #8b919e; margin-bottom: 4px; }
.hdr h1 { font-size: 1.4rem; font-weight: 700; color: #1a1d23; margin: 0; }
.hdr .sub { font-size: 0.82rem; color: #8b919e; margin-top: 2px; }

/* Stats */
.stats { display: flex; gap: 10px; margin-bottom: 1rem; }
.sc {
    flex: 1; background: #f9fafb; border: 1px solid #e5e7eb;
    border-radius: 8px; padding: 0.85rem; text-align: center;
}
.sc .n { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 600; color: #1a1d23; }
.sc .l { font-size: 0.6rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px; color: #8b919e; margin-top: 2px; }

/* Cards */
.card {
    background: #fff; border: 1px solid #e5e7eb;
    border-radius: 10px; padding: 1.25rem 1.5rem; margin-bottom: 0.75rem;
}
.card .ct { font-size: 0.95rem; font-weight: 600; color: #1a1d23; }
.card .cm { font-size: 0.75rem; color: #8b919e; }

/* Sidebar brand */
.sb {
    text-align: center; padding: 1.5rem 0 1.2rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 1rem;
}
.sb .logo { font-size: 1.5rem; font-weight: 700; }
.sb .stag { font-size: 0.58rem; text-transform: uppercase; letter-spacing: 2.5px; color: #6b7280 !important; margin-top: 2px; }

/* Section label */
.sl {
    font-size: 0.63rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 2px; color: #8b919e;
    margin: 1.2rem 0 0.6rem; padding-bottom: 0.3rem;
    border-bottom: 1px solid #e5e7eb;
}

/* Artifact row */
.arow {
    background: #f9fafb; border: 1px solid #eef0f3;
    border-radius: 6px; padding: 0.55rem 0.85rem;
    margin: 0.3rem 0; display: flex;
    align-items: center; gap: 0.5rem; font-size: 0.82rem;
}
.arow .an { font-weight: 500; color: #1a1d23; flex: 1; }
.arow .ab {
    padding: 1px 6px; border-radius: 3px;
    font-size: 0.58rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.3px;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════
# SESSION
# ════════════════════════════════════════════════════════════════════════
if "data" not in st.session_state:
    st.session_state.data = load_data()

def refresh():
    st.session_state.data = load_data()

# ════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb">
        <div class="logo">
            <span style="color:#E53238;">e</span><span style="color:#0064D2;">B</span><span style="color:#F5AF02;">a</span><span style="color:#86B817;">y</span>
            <span style="color:#fff;"> IAC</span>
        </div>
        <div class="stag">Artifact Vault</div>
    </div>
    """, unsafe_allow_html=True)

    nav = st.radio("", [
        "🌳 Tree View",
        "📦 Add Artifacts",
        "🏗️ Manage Structure",
        "✏️ Rename",
        "🗑️ Admin Delete",
        "💾 Backup & Export",
    ], label_visibility="collapsed")

    st.markdown("---")
    data = st.session_state.data
    stats = get_stats(data)
    st.caption("VAULT")
    st.markdown(f"**{stats['total_teams']}** teams · **{stats['total_members']}** members · **{stats['total_artifacts']}** artifacts")
    st.caption(f"Local sync: {data.get('last_updated', '—')}")

    # Google Sheets sync status
    st.markdown("---")
    sync_info = get_sync_status()
    st.caption("GOOGLE SHEETS")
    st.markdown(f"{sync_info['icon']} {sync_info['message']}")
    if sync_info["status"] == "connected":
        sheet_ts = data.get("_last_sheet_sync", "never")
        st.caption(f"Last push: {sheet_ts}")
    if sync_info["status"] == "connected":
        if st.button("🔄 Force Sync Now", use_container_width=True, key="sidebar_sync"):
            ok, msg = sync_to_sheet(st.session_state.data)
            if ok:
                st.success("Synced!")
            else:
                st.error(msg)


# ════════════════════════════════════════════════════════════════════════
# 🌳 TREE VIEW
# ════════════════════════════════════════════════════════════════════════
if nav == "🌳 Tree View":
    data = st.session_state.data
    stats = get_stats(data)

    st.markdown("""
    <div class="hdr">
        <div class="ey">eBay Infrastructure &amp; Cloud</div>
        <h1>Artifact Vault — Tree View</h1>
        <div class="sub">Visual hierarchy: Organization → Teams → Members → Artifacts</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    st.markdown(f"""
    <div class="stats">
        <div class="sc"><div class="n">{stats['total_teams']}</div><div class="l">Teams</div></div>
        <div class="sc"><div class="n">{stats['total_members']}</div><div class="l">Members</div></div>
        <div class="sc"><div class="n">{stats['total_artifacts']}</div><div class="l">Artifacts</div></div>
        <div class="sc"><div class="n">{sum(v for k,v in stats['type_counts'].items() if 'link' in k)}</div><div class="l">Links</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Visual Tree ─────────────────────────────────────────────────
    tree_html = generate_tree_html(data, height=550)
    components.html(tree_html, height=570, scrolling=True)

    # ── Inline Actions Below Tree ───────────────────────────────────
    st.markdown('<div class="sl">Quick actions</div>', unsafe_allow_html=True)

    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        with st.popover("➕ Add Team", use_container_width=True):
            tn = st.text_input("Team name", key="qa_team")
            if st.button("Create", key="qa_team_btn"):
                if tn:
                    ok, msg = add_team(tn)
                    refresh()
                    st.success(msg) if ok else st.error(msg)
                    if ok: st.rerun()

    with qa2:
        teams = list(data["teams"].keys())
        with st.popover("➕ Add Member", use_container_width=True):
            if teams:
                sel_t = st.selectbox("To team", teams, key="qa_mem_t")
                mn = st.text_input("Member name", key="qa_mem")
                if st.button("Add", key="qa_mem_btn"):
                    if mn:
                        ok, msg = add_member(sel_t, mn)
                        refresh()
                        st.success(msg) if ok else st.error(msg)
                        if ok: st.rerun()
            else:
                st.info("Create a team first.")

    with qa3:
        with st.popover("➕ Add Artifact", use_container_width=True):
            if teams:
                sel_t2 = st.selectbox("Team", teams, key="qa_art_t")
                mems = list(data["teams"].get(sel_t2, {}).get("members", {}).keys())
                if mems:
                    sel_m = st.selectbox("Member", mems, key="qa_art_m")
                    atype = st.radio("Type", ["Link", "File"], horizontal=True, key="qa_art_type")
                    if atype == "Link":
                        aname = st.text_input("Name", key="qa_art_name")
                        aurl = st.text_input("URL", key="qa_art_url")
                        if st.button("Save", key="qa_art_save"):
                            if aname and aurl:
                                art = {"name": aname.strip(), "type": classify_link(aurl), "url": aurl.strip()}
                                ok, msg = add_artifact(sel_t2, sel_m, art)
                                refresh()
                                st.success(msg) if ok else st.error(msg)
                                if ok: st.rerun()
                    else:
                        files = st.file_uploader("Files", accept_multiple_files=True, key="qa_art_files",
                            type=["pptx","ppt","xlsx","xls","csv","pdf","doc","docx","txt","png","jpg","zip"])
                        if st.button("Upload", key="qa_art_up"):
                            if files:
                                for f in files:
                                    fp = save_uploaded_file(f)
                                    art = {"name": f.name, "type": classify_file(f.name), "file_path": fp, "size_bytes": f.size}
                                    add_artifact(sel_t2, sel_m, art)
                                refresh()
                                st.success(f"Uploaded {len(files)} file(s).")
                                st.rerun()
                else:
                    st.info("Add members to this team first.")
            else:
                st.info("Create a team first.")

    # ── Detailed List Below ─────────────────────────────────────────
    st.markdown('<div class="sl">All artifacts by team</div>', unsafe_allow_html=True)

    for t_name, t_data in data["teams"].items():
        with st.expander(f"📁 **{t_name}** — {len(t_data['members'])} members", expanded=False):
            for m_name, m_data in t_data["members"].items():
                st.markdown(f"**👤 {m_name}**")
                if m_data["artifacts"]:
                    for art in m_data["artifacts"]:
                        info = ARTIFACT_TYPES.get(art.get("type", "other_file"), {"icon": "📎", "label": "File", "color": "#6B7280"})
                        link = ""
                        if art.get("url"):
                            link = f'<a href="{art["url"]}" target="_blank" style="color:#0064D2;font-size:0.72rem;text-decoration:none;">Open ↗</a>'
                        st.markdown(f"""
                        <div class="arow">
                            <span>{info['icon']}</span>
                            <span class="an">{art.get('name','Untitled')}</span>
                            <span class="ab" style="background:{info['color']}12;color:{info['color']};">{info['label']}</span>
                            {link}
                            <span style="font-size:0.65rem;color:#b0b5c0;font-family:'IBM Plex Mono',monospace;">{art.get('created_at','')[:10]}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("  No artifacts yet.")
                st.markdown("")


# ════════════════════════════════════════════════════════════════════════
# 📦 ADD ARTIFACTS
# ════════════════════════════════════════════════════════════════════════
elif nav == "📦 Add Artifacts":
    st.markdown("""
    <div class="hdr">
        <div class="ey">Artifact Management</div>
        <h1>Add Artifacts</h1>
        <div class="sub">Upload files or paste links — they'll show up in the tree</div>
    </div>
    """, unsafe_allow_html=True)

    data = st.session_state.data
    teams = list(data["teams"].keys())

    if not teams:
        st.warning("Create a team first in **Manage Structure**.")
    else:
        c1, c2 = st.columns(2)
        with c1: sel_t = st.selectbox("Team", teams, key="aa_t")
        with c2:
            mems = list(data["teams"].get(sel_t, {}).get("members", {}).keys())
            sel_m = st.selectbox("Member", mems if mems else ["—"], key="aa_m")

        if not mems:
            st.warning("Add a member to this team first.")
        else:
            tab_link, tab_file = st.tabs(["🔗 Add Links", "📁 Upload Files"])

            with tab_link:
                with st.form("link_form", clear_on_submit=True):
                    ln = st.text_input("Name", placeholder="e.g., Q4 Revenue Dashboard")
                    lu = st.text_input("URL", placeholder="https://...")
                    lnotes = st.text_area("Notes (optional)", height=68)
                    if st.form_submit_button("🔗 Add Link", use_container_width=True):
                        if ln and lu:
                            art = {"name": ln.strip(), "type": classify_link(lu), "url": lu.strip(), "notes": lnotes.strip()}
                            ok, msg = add_artifact(sel_t, sel_m, art)
                            refresh()
                            st.success(msg) if ok else st.error(msg)

            with tab_file:
                files = st.file_uploader("Choose files (multi-upload supported)", accept_multiple_files=True,
                    type=["pptx","ppt","xlsx","xls","csv","pdf","doc","docx","txt","png","jpg","zip"], key="aa_files")
                fnotes = st.text_input("Notes (optional)", key="aa_fnotes")
                if st.button("📤 Upload All", use_container_width=True):
                    if files:
                        cnt = 0
                        for f in files:
                            fp = save_uploaded_file(f)
                            art = {"name": f.name, "type": classify_file(f.name), "file_path": fp, "notes": fnotes.strip(), "size_bytes": f.size}
                            ok, _ = add_artifact(sel_t, sel_m, art)
                            if ok: cnt += 1
                        refresh()
                        st.success(f"Uploaded {cnt}/{len(files)} files.")
                    else:
                        st.warning("No files selected.")


# ════════════════════════════════════════════════════════════════════════
# 🏗️ MANAGE STRUCTURE
# ════════════════════════════════════════════════════════════════════════
elif nav == "🏗️ Manage Structure":
    st.markdown("""
    <div class="hdr">
        <div class="ey">Administration</div>
        <h1>Manage Structure</h1>
        <div class="sub">Add teams and members — they instantly appear in the tree</div>
    </div>
    """, unsafe_allow_html=True)

    data = st.session_state.data

    st.markdown('<div class="sl">Add team</div>', unsafe_allow_html=True)
    with st.form("add_team_f", clear_on_submit=True):
        tn = st.text_input("Team Name", placeholder="e.g., Cloud Platform, SRE, DevOps")
        if st.form_submit_button("➕ Create Team", use_container_width=True):
            if tn:
                ok, msg = add_team(tn)
                refresh()
                st.success(msg) if ok else st.error(msg)

    teams = list(st.session_state.data["teams"].keys())
    if teams:
        st.markdown('<div class="sl">Add member</div>', unsafe_allow_html=True)
        with st.form("add_mem_f", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1: sel_t = st.selectbox("Team", teams, key="ms_t")
            with c2: mn = st.text_input("Member Name", placeholder="e.g., Rajesh Kumar")
            if st.form_submit_button("➕ Add Member", use_container_width=True):
                if mn:
                    ok, msg = add_member(sel_t, mn)
                    refresh()
                    st.success(msg) if ok else st.error(msg)

    st.markdown('<div class="sl">Current structure</div>', unsafe_allow_html=True)
    data = st.session_state.data
    if not data["teams"]:
        st.info("No teams yet. Create one above.")
    for t_name, t_data in data["teams"].items():
        members = list(t_data["members"].keys())
        mstr = ", ".join(members) if members else "No members"
        a_count = sum(len(m["artifacts"]) for m in t_data["members"].values())
        st.markdown(f"""
        <div class="card">
            <div class="ct">📁 {t_name}</div>
            <div class="cm">{len(members)} members · {a_count} artifacts — {mstr}</div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════
# ✏️ RENAME
# ════════════════════════════════════════════════════════════════════════
elif nav == "✏️ Rename":
    st.markdown("""
    <div class="hdr">
        <div class="ey">Administration</div>
        <h1>Rename</h1>
        <div class="sub">Rename any team, member, or artifact</div>
    </div>
    """, unsafe_allow_html=True)

    data = st.session_state.data
    teams = list(data["teams"].keys())
    target = st.radio("What to rename?", ["Team", "Member", "Artifact"], horizontal=True)

    if not teams:
        st.info("Nothing to rename yet.")
    elif target == "Team":
        with st.form("ren_t", clear_on_submit=True):
            sel = st.selectbox("Team", teams)
            nn = st.text_input("New name")
            if st.form_submit_button("✏️ Rename", use_container_width=True) and nn:
                ok, msg = rename_team(sel, nn); refresh()
                st.success(msg) if ok else st.error(msg)
    elif target == "Member":
        with st.form("ren_m", clear_on_submit=True):
            sel_t = st.selectbox("Team", teams, key="rm_t")
            mems = list(data["teams"].get(sel_t, {}).get("members", {}).keys())
            if mems:
                sel_m = st.selectbox("Member", mems)
                nn = st.text_input("New name")
                if st.form_submit_button("✏️ Rename", use_container_width=True) and nn:
                    ok, msg = rename_member(sel_t, sel_m, nn); refresh()
                    st.success(msg) if ok else st.error(msg)
            else:
                st.info("No members."); st.form_submit_button("✏️ Rename", disabled=True)
    elif target == "Artifact":
        with st.form("ren_a", clear_on_submit=True):
            sel_t = st.selectbox("Team", teams, key="ra_t")
            mems = list(data["teams"].get(sel_t, {}).get("members", {}).keys())
            if mems:
                sel_m = st.selectbox("Member", mems, key="ra_m")
                arts = data["teams"][sel_t]["members"][sel_m]["artifacts"]
                if arts:
                    opts = {f"{a['name']} ({a['id']})": a["id"] for a in arts}
                    sel_a = st.selectbox("Artifact", list(opts.keys()))
                    nn = st.text_input("New name")
                    if st.form_submit_button("✏️ Rename", use_container_width=True) and nn:
                        ok, msg = rename_artifact(sel_t, sel_m, opts[sel_a], nn); refresh()
                        st.success(msg) if ok else st.error(msg)
                else:
                    st.info("No artifacts."); st.form_submit_button("✏️ Rename", disabled=True)
            else:
                st.info("No members."); st.form_submit_button("✏️ Rename", disabled=True)


# ════════════════════════════════════════════════════════════════════════
# 🗑️ ADMIN DELETE
# ════════════════════════════════════════════════════════════════════════
elif nav == "🗑️ Admin Delete":
    st.markdown("""
    <div class="hdr">
        <div class="ey">Restricted</div>
        <h1>Admin Delete</h1>
        <div class="sub">All deletions require admin password — irreversible</div>
    </div>
    """, unsafe_allow_html=True)

    st.warning("⚠️ Deletions are permanent. A backup is saved automatically.")

    data = st.session_state.data
    teams = list(data["teams"].keys())
    target = st.radio("Delete", ["Team", "Member", "Artifact"], horizontal=True)

    if target == "Team":
        with st.form("del_t"):
            if teams:
                sel = st.selectbox("Team", teams); pw = st.text_input("Password", type="password")
                if st.form_submit_button("🗑️ Delete", use_container_width=True):
                    ok, msg = delete_team(sel, pw); refresh()
                    st.success(msg) if ok else st.error(msg)
            else: st.info("Nothing to delete."); st.form_submit_button("🗑️", disabled=True)

    elif target == "Member":
        with st.form("del_m"):
            if teams:
                sel_t = st.selectbox("Team", teams, key="dm_t")
                mems = list(data["teams"].get(sel_t, {}).get("members", {}).keys())
                if mems:
                    sel_m = st.selectbox("Member", mems); pw = st.text_input("Password", type="password")
                    if st.form_submit_button("🗑️ Delete", use_container_width=True):
                        ok, msg = delete_member(sel_t, sel_m, pw); refresh()
                        st.success(msg) if ok else st.error(msg)
                else: st.info("No members."); st.form_submit_button("🗑️", disabled=True)
            else: st.info("No teams."); st.form_submit_button("🗑️", disabled=True)

    elif target == "Artifact":
        with st.form("del_a"):
            if teams:
                sel_t = st.selectbox("Team", teams, key="da_t")
                mems = list(data["teams"].get(sel_t, {}).get("members", {}).keys())
                if mems:
                    sel_m = st.selectbox("Member", mems, key="da_m")
                    arts = data["teams"][sel_t]["members"][sel_m]["artifacts"]
                    if arts:
                        opts = {f"{a['name']} ({a['id']})": a["id"] for a in arts}
                        sel_a = st.selectbox("Artifact", list(opts.keys())); pw = st.text_input("Password", type="password")
                        if st.form_submit_button("🗑️ Delete", use_container_width=True):
                            ok, msg = delete_artifact(sel_t, sel_m, opts[sel_a], pw); refresh()
                            st.success(msg) if ok else st.error(msg)
                    else: st.info("No artifacts."); st.form_submit_button("🗑️", disabled=True)
                else: st.info("No members."); st.form_submit_button("🗑️", disabled=True)
            else: st.info("No teams."); st.form_submit_button("🗑️", disabled=True)


# ════════════════════════════════════════════════════════════════════════
# 💾 BACKUP & EXPORT
# ════════════════════════════════════════════════════════════════════════
elif nav == "💾 Backup & Export":
    st.markdown("""
    <div class="hdr">
        <div class="ey">Data</div>
        <h1>Backup & Export</h1>
        <div class="sub">Local JSON + Google Sheets — auto-backup on every change</div>
    </div>
    """, unsafe_allow_html=True)

    data = st.session_state.data
    stats = get_stats(data)

    c1, c2, c3 = st.columns(3)
    c1.metric("Teams", stats["total_teams"])
    c2.metric("Members", stats["total_members"])
    c3.metric("Artifacts", stats["total_artifacts"])

    # ── Local Backup ────────────────────────────────────────────────
    st.markdown('<div class="sl">Local backup</div>', unsafe_allow_html=True)

    js = json.dumps(data, indent=2, default=str)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button("⬇️ Download vault_data.json", data=js,
        file_name=f"ebay_iac_vault_{ts}.json", mime="application/json", use_container_width=True)

    with st.expander("Raw JSON"):
        st.json(data)

    st.info("Every change auto-saves a timestamped copy to `data/backups/` (last 10 kept).")
    bd = "data/backups"
    if os.path.exists(bd):
        bk = sorted(os.listdir(bd), reverse=True)
        if bk:
            st.caption(f"{len(bk)} backup(s):")
            for b in bk[:10]:
                st.text(f"  📄 {b}")

    # ── Google Sheets Sync ──────────────────────────────────────────
    st.markdown('<div class="sl">Google Sheets sync</div>', unsafe_allow_html=True)

    sync_info = get_sync_status()

    if sync_info["status"] == "disabled":
        st.markdown(f"""
        <div class="card">
            <div class="ct">⚪ Google Sheets sync is off</div>
            <div class="cm">To enable, edit <code>config.py</code>:</div>
        </div>
        """, unsafe_allow_html=True)
        st.code("""# config.py
GOOGLE_SYNC_ENABLED = True
GOOGLE_SHEET_ID = "your-sheet-id-here"
""", language="python")
        st.markdown("""**Setup steps:**
1. `pip install gspread google-auth`
2. Create a Google Cloud project, enable Sheets API + Drive API
3. Create a service account → download JSON key → save as `credentials/service_account.json`
4. Create a Google Sheet → share with the service account email (Editor)
5. Copy the Sheet ID from the URL into `config.py`
6. Set `GOOGLE_SYNC_ENABLED = True`
""")

    elif sync_info["status"] == "unconfigured":
        st.warning(f"🟡 {sync_info['message']}")
        st.markdown("Check `credentials/service_account.json` and `config.py`.")

    elif sync_info["status"] == "error":
        st.error(f"🔴 {sync_info['message']}")

    elif sync_info["status"] == "connected":
        st.success(f"🟢 Connected to Google Sheets")
        sheet_ts = data.get("_last_sheet_sync", "never")
        st.caption(f"Last push: {sheet_ts}")

        col_push, col_pull = st.columns(2)
        with col_push:
            if st.button("📤 Push to Google Sheets", use_container_width=True):
                ok, msg = sync_to_sheet(st.session_state.data)
                if ok:
                    st.session_state.data["_last_sheet_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success(msg)
                else:
                    st.error(msg)

        with col_pull:
            if st.button("📥 Restore from Google Sheets", use_container_width=True):
                st.session_state.show_restore_confirm = True

        if st.session_state.get("show_restore_confirm"):
            st.warning("⚠️ This will **overwrite** your local data with the Google Sheets backup.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, restore", use_container_width=True):
                    restored, msg = load_from_google_sheet()
                    if restored:
                        save_data(restored, skip_sync=True)
                        st.session_state.data = restored
                        st.session_state.show_restore_confirm = False
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with c2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_restore_confirm = False
                    st.rerun()

        st.markdown("---")
        st.markdown("""**What gets synced to Google Sheets:**
- **Sheet 1 (Vault JSON)** — full JSON backup in a single cell
- **Sheet 2 (Flat View)** — spreadsheet table: Team, Member, Artifact, Type, URL, Date
- **Sheet 3 (Sync Log)** — timestamp + counts for every sync
""")
