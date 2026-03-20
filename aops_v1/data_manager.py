"""
data_manager.py — Persistence layer for eBay IAC Artifact Vault.
All data is stored in a single JSON file (vault_data.json) which auto-updates
on every mutation. This serves as the live backup.
"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
BACKUP_DIR = DATA_DIR / "backups"
DATA_FILE = DATA_DIR / "vault_data.json"

ADMIN_DELETE_PASSWORD = "ebay@delete2026"

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


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_data() -> dict:
    _ensure_dirs()
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    data = DEFAULT_STRUCTURE.copy()
    data["created_at"] = _now()
    data["last_updated"] = _now()
    save_data(data)
    return data


def save_data(data: dict):
    _ensure_dirs()
    data["last_updated"] = _now()
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)
    # Rotating backup — keep last 10
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"vault_backup_{ts}.json"
    shutil.copy2(DATA_FILE, backup_path)
    backups = sorted(BACKUP_DIR.glob("vault_backup_*.json"))
    while len(backups) > 10:
        backups[0].unlink()
        backups.pop(0)


# ── Team CRUD ───────────────────────────────────────────────────────────
def add_team(name: str) -> tuple[bool, str]:
    data = load_data()
    key = name.strip()
    if not key:
        return False, "Team name cannot be empty."
    if key in data["teams"]:
        return False, f"Team '{key}' already exists."
    data["teams"][key] = {
        "created_at": _now(),
        "members": {}
    }
    save_data(data)
    return True, f"Team '{key}' added successfully."


def rename_team(old_name: str, new_name: str) -> tuple[bool, str]:
    data = load_data()
    new_name = new_name.strip()
    if not new_name:
        return False, "New team name cannot be empty."
    if old_name not in data["teams"]:
        return False, f"Team '{old_name}' not found."
    if new_name in data["teams"]:
        return False, f"Team '{new_name}' already exists."
    data["teams"][new_name] = data["teams"].pop(old_name)
    save_data(data)
    return True, f"Team renamed from '{old_name}' to '{new_name}'."


def delete_team(name: str, password: str) -> tuple[bool, str]:
    if password != ADMIN_DELETE_PASSWORD:
        return False, "Incorrect admin password."
    data = load_data()
    if name not in data["teams"]:
        return False, f"Team '{name}' not found."
    del data["teams"][name]
    save_data(data)
    return True, f"Team '{name}' deleted."


# ── Member CRUD ─────────────────────────────────────────────────────────
def add_member(team: str, name: str) -> tuple[bool, str]:
    data = load_data()
    key = name.strip()
    if not key:
        return False, "Member name cannot be empty."
    if team not in data["teams"]:
        return False, f"Team '{team}' not found."
    if key in data["teams"][team]["members"]:
        return False, f"Member '{key}' already exists in team '{team}'."
    data["teams"][team]["members"][key] = {
        "created_at": _now(),
        "artifacts": []
    }
    save_data(data)
    return True, f"Member '{key}' added to '{team}'."


def rename_member(team: str, old_name: str, new_name: str) -> tuple[bool, str]:
    data = load_data()
    new_name = new_name.strip()
    if not new_name:
        return False, "New member name cannot be empty."
    if team not in data["teams"]:
        return False, f"Team '{team}' not found."
    members = data["teams"][team]["members"]
    if old_name not in members:
        return False, f"Member '{old_name}' not found."
    if new_name in members:
        return False, f"Member '{new_name}' already exists."
    members[new_name] = members.pop(old_name)
    save_data(data)
    return True, f"Member renamed to '{new_name}'."


def delete_member(team: str, name: str, password: str) -> tuple[bool, str]:
    if password != ADMIN_DELETE_PASSWORD:
        return False, "Incorrect admin password."
    data = load_data()
    if team not in data["teams"]:
        return False, f"Team '{team}' not found."
    if name not in data["teams"][team]["members"]:
        return False, f"Member '{name}' not found."
    del data["teams"][team]["members"][name]
    save_data(data)
    return True, f"Member '{name}' deleted from '{team}'."


# ── Artifact CRUD ───────────────────────────────────────────────────────
ARTIFACT_TYPES = {
    "zeta_link": {"icon": "🔗", "label": "Zeta Link"},
    "github_link": {"icon": "🐙", "label": "GitHub Link"},
    "tableau_link": {"icon": "📊", "label": "Tableau Dashboard"},
    "generic_link": {"icon": "🌐", "label": "Web Link"},
    "powerpoint": {"icon": "📑", "label": "PowerPoint"},
    "excel": {"icon": "📗", "label": "Excel"},
    "pdf": {"icon": "📕", "label": "PDF"},
    "other_file": {"icon": "📎", "label": "Other File"},
}


def add_artifact(team: str, member: str, artifact: dict) -> tuple[bool, str]:
    data = load_data()
    if team not in data["teams"]:
        return False, f"Team '{team}' not found."
    if member not in data["teams"][team]["members"]:
        return False, f"Member '{member}' not found."
    artifact["id"] = str(uuid.uuid4())[:8]
    artifact["created_at"] = _now()
    data["teams"][team]["members"][member]["artifacts"].append(artifact)
    save_data(data)
    return True, f"Artifact '{artifact.get('name', 'Untitled')}' added."


def rename_artifact(team: str, member: str, artifact_id: str, new_name: str) -> tuple[bool, str]:
    data = load_data()
    new_name = new_name.strip()
    if not new_name:
        return False, "New artifact name cannot be empty."
    arts = data["teams"][team]["members"][member]["artifacts"]
    for a in arts:
        if a["id"] == artifact_id:
            a["name"] = new_name
            save_data(data)
            return True, f"Artifact renamed to '{new_name}'."
    return False, "Artifact not found."


def delete_artifact(team: str, member: str, artifact_id: str, password: str) -> tuple[bool, str]:
    if password != ADMIN_DELETE_PASSWORD:
        return False, "Incorrect admin password."
    data = load_data()
    arts = data["teams"][team]["members"][member]["artifacts"]
    for i, a in enumerate(arts):
        if a["id"] == artifact_id:
            arts.pop(i)
            save_data(data)
            return True, "Artifact deleted."
    return False, "Artifact not found."


# ── Stats ───────────────────────────────────────────────────────────────
def get_stats(data: dict) -> dict:
    total_teams = len(data["teams"])
    total_members = sum(len(t["members"]) for t in data["teams"].values())
    total_artifacts = sum(
        len(m["artifacts"])
        for t in data["teams"].values()
        for m in t["members"].values()
    )
    type_counts = {}
    for t in data["teams"].values():
        for m in t["members"].values():
            for a in m["artifacts"]:
                atype = a.get("type", "other_file")
                type_counts[atype] = type_counts.get(atype, 0) + 1
    return {
        "total_teams": total_teams,
        "total_members": total_members,
        "total_artifacts": total_artifacts,
        "type_counts": type_counts,
    }


def save_uploaded_file(uploaded_file) -> str:
    _ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = uploaded_file.name.replace(" ", "_")
    dest = UPLOAD_DIR / f"{ts}_{safe_name}"
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)
