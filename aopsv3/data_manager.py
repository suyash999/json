"""
data_manager.py — Persistence layer for eBay IAC Artifact Vault.
Simple hierarchy: Organization -> Teams -> Members -> Artifacts.
Every save writes to local JSON + Google Sheets (if configured).
"""

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
BACKUP_DIR = DATA_DIR / "backups"
DATA_FILE = DATA_DIR / "vault_data.json"

try:
    from config import ADMIN_DELETE_PASSWORD, MAX_LOCAL_BACKUPS
except ImportError:
    ADMIN_DELETE_PASSWORD = "ebay@delete2026"
    MAX_LOCAL_BACKUPS = 10

ARTIFACT_TYPES = {
    "zeta_link":   {"icon": "\U0001f517", "label": "Zeta",       "color": "#0064D2"},
    "github_link": {"icon": "\U0001f419", "label": "GitHub",     "color": "#24292e"},
    "tableau_link":{"icon": "\U0001f4ca", "label": "Tableau",    "color": "#E97627"},
    "generic_link":{"icon": "\U0001f310", "label": "Link",       "color": "#6366f1"},
    "powerpoint":  {"icon": "\U0001f4d1", "label": "PowerPoint", "color": "#D04423"},
    "excel":       {"icon": "\U0001f4d7", "label": "Excel",      "color": "#217346"},
    "pdf":         {"icon": "\U0001f4d5", "label": "PDF",        "color": "#E53238"},
    "other_file":  {"icon": "\U0001f4ce", "label": "File",       "color": "#6B7280"},
}

DEFAULT_STRUCTURE = {
    "organization": "eBay IAC",
    "created_at": "",
    "last_updated": "",
    "teams": {}
}


def _ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_data():
    _ensure_dirs()
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    data = DEFAULT_STRUCTURE.copy()
    data["created_at"] = _now()
    data["last_updated"] = _now()
    save_data(data, skip_sync=True)
    return data


def save_data(data, skip_sync=False):
    _ensure_dirs()
    data["last_updated"] = _now()

    # 1. Write local JSON
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)

    # 2. Rolling local backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"vault_backup_{ts}.json"
    shutil.copy2(DATA_FILE, backup_path)
    backups = sorted(BACKUP_DIR.glob("vault_backup_*.json"))
    while len(backups) > MAX_LOCAL_BACKUPS:
        backups[0].unlink()
        backups.pop(0)

    # 3. Sync to Google Sheets (non-blocking)
    if not skip_sync:
        try:
            from google_sync import sync_to_sheet, is_sync_available
            if is_sync_available():
                ok, msg = sync_to_sheet(data)
                if ok:
                    logger.info(f"Google Sheets sync: {msg}")
                    data["_last_sheet_sync"] = _now()
                else:
                    logger.warning(f"Google Sheets sync failed: {msg}")
        except Exception as e:
            logger.warning(f"Google Sheets sync skipped: {e}")


def load_from_google_sheet():
    """Load vault data from Google Sheet backup. Returns (data, message)."""
    try:
        from google_sync import load_from_sheet
        return load_from_sheet()
    except Exception as e:
        return None, f"Failed: {e}"


# ── Team CRUD ───────────────────────────────────────────────────────────

def add_team(name):
    data = load_data()
    key = name.strip()
    if not key:
        return False, "Team name cannot be empty."
    if key in data["teams"]:
        return False, f"Team '{key}' already exists."
    data["teams"][key] = {"created_at": _now(), "members": {}}
    save_data(data)
    return True, f"Team '{key}' created."


def rename_team(old, new):
    data = load_data()
    new = new.strip()
    if not new:
        return False, "Name cannot be empty."
    if old not in data["teams"]:
        return False, "Team not found."
    if new in data["teams"]:
        return False, f"'{new}' already exists."
    data["teams"][new] = data["teams"].pop(old)
    save_data(data)
    return True, f"Renamed to '{new}'."


def delete_team(name, pw):
    if pw != ADMIN_DELETE_PASSWORD:
        return False, "Wrong password."
    data = load_data()
    if name not in data["teams"]:
        return False, "Not found."
    del data["teams"][name]
    save_data(data)
    return True, f"'{name}' deleted."


# ── Member CRUD ─────────────────────────────────────────────────────────

def add_member(team, name):
    data = load_data()
    key = name.strip()
    if not key:
        return False, "Name cannot be empty."
    if team not in data["teams"]:
        return False, "Team not found."
    if key in data["teams"][team]["members"]:
        return False, f"'{key}' already exists."
    data["teams"][team]["members"][key] = {"created_at": _now(), "artifacts": []}
    save_data(data)
    return True, f"'{key}' added."


def rename_member(team, old, new):
    data = load_data()
    new = new.strip()
    if not new:
        return False, "Name cannot be empty."
    if team not in data["teams"]:
        return False, "Team not found."
    m = data["teams"][team]["members"]
    if old not in m:
        return False, "Not found."
    if new in m:
        return False, f"'{new}' already exists."
    m[new] = m.pop(old)
    save_data(data)
    return True, f"Renamed to '{new}'."


def delete_member(team, name, pw):
    if pw != ADMIN_DELETE_PASSWORD:
        return False, "Wrong password."
    data = load_data()
    if team not in data["teams"]:
        return False, "Team not found."
    if name not in data["teams"][team]["members"]:
        return False, "Not found."
    del data["teams"][team]["members"][name]
    save_data(data)
    return True, f"'{name}' deleted."


# ── Artifact CRUD ───────────────────────────────────────────────────────

def add_artifact(team, member, artifact):
    data = load_data()
    if team not in data["teams"]:
        return False, "Team not found."
    if member not in data["teams"][team]["members"]:
        return False, "Member not found."
    artifact["id"] = str(uuid.uuid4())[:8]
    artifact["created_at"] = _now()
    data["teams"][team]["members"][member]["artifacts"].append(artifact)
    save_data(data)
    return True, f"'{artifact.get('name', 'Untitled')}' added."


def rename_artifact(team, member, aid, new):
    data = load_data()
    new = new.strip()
    if not new:
        return False, "Name cannot be empty."
    for a in data["teams"][team]["members"][member]["artifacts"]:
        if a["id"] == aid:
            a["name"] = new
            save_data(data)
            return True, f"Renamed to '{new}'."
    return False, "Not found."


def delete_artifact(team, member, aid, pw):
    if pw != ADMIN_DELETE_PASSWORD:
        return False, "Wrong password."
    data = load_data()
    arts = data["teams"][team]["members"][member]["artifacts"]
    for i, a in enumerate(arts):
        if a["id"] == aid:
            arts.pop(i)
            save_data(data)
            return True, "Deleted."
    return False, "Not found."


# ── Helpers ─────────────────────────────────────────────────────────────

def classify_link(url):
    u = url.lower()
    if "github" in u:
        return "github_link"
    if "tableau" in u:
        return "tableau_link"
    if "zeta" in u:
        return "zeta_link"
    return "generic_link"


def classify_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("ppt", "pptx"):
        return "powerpoint"
    if ext in ("xls", "xlsx", "csv"):
        return "excel"
    if ext == "pdf":
        return "pdf"
    return "other_file"


def save_uploaded_file(uploaded_file):
    _ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = uploaded_file.name.replace(" ", "_")
    dest = UPLOAD_DIR / f"{ts}_{safe}"
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)


def get_stats(data):
    tt = len(data["teams"])
    tm = sum(len(t["members"]) for t in data["teams"].values())
    ta = sum(len(m["artifacts"]) for t in data["teams"].values() for m in t["members"].values())
    tc = {}
    for t in data["teams"].values():
        for m in t["members"].values():
            for a in m["artifacts"]:
                k = a.get("type", "other_file")
                tc[k] = tc.get(k, 0) + 1
    return {"total_teams": tt, "total_members": tm, "total_artifacts": ta, "type_counts": tc}
