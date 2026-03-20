"""
google_sync.py — Google Sheets backup sync for eBay IAC Artifact Vault.
Writes vault data to a Google Sheet on every save.
Can also load data FROM the sheet to restore a backup.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CREDENTIALS_PATH = Path("credentials/service_account.json")

try:
    from config import GOOGLE_SHEET_ID, GOOGLE_SYNC_ENABLED
except ImportError:
    GOOGLE_SHEET_ID = ""
    GOOGLE_SYNC_ENABLED = False

_gsheet_client = None
_gsheet_available = None


def _is_placeholder_credentials():
    if not CREDENTIALS_PATH.exists():
        return True
    try:
        with open(CREDENTIALS_PATH) as f:
            creds = json.load(f)
        return "YOUR_PROJECT_ID" in creds.get("project_id", "YOUR_PROJECT_ID")
    except Exception:
        return True


def _get_client():
    global _gsheet_client, _gsheet_available

    if _gsheet_available is False:
        return None
    if _gsheet_client is not None:
        return _gsheet_client

    if not GOOGLE_SYNC_ENABLED:
        _gsheet_available = False
        return None

    if _is_placeholder_credentials():
        logger.warning("Google credentials are placeholder - sync disabled.")
        _gsheet_available = False
        return None

    if not GOOGLE_SHEET_ID:
        logger.warning("GOOGLE_SHEET_ID not set in config.py - sync disabled.")
        _gsheet_available = False
        return None

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(str(CREDENTIALS_PATH), scopes=scopes)
        _gsheet_client = gspread.authorize(creds)
        _gsheet_available = True
        logger.info("Google Sheets client initialized.")
        return _gsheet_client

    except ImportError:
        logger.warning("gspread or google-auth not installed. Run: pip install gspread google-auth")
        _gsheet_available = False
        return None
    except Exception as e:
        logger.error(f"Failed to init Google Sheets client: {e}")
        _gsheet_available = False
        return None


def is_sync_available():
    _get_client()
    return _gsheet_available is True


def get_sync_status():
    if not GOOGLE_SYNC_ENABLED:
        return {"status": "disabled", "message": "Google Sync disabled in config.py", "icon": "⚪"}
    if _is_placeholder_credentials():
        return {"status": "unconfigured", "message": "Credentials are placeholder - replace with real key", "icon": "🟡"}
    if not GOOGLE_SHEET_ID:
        return {"status": "unconfigured", "message": "GOOGLE_SHEET_ID not set in config.py", "icon": "🟡"}
    client = _get_client()
    if client is None:
        return {"status": "error", "message": "Could not connect to Google Sheets", "icon": "🔴"}
    return {"status": "connected", "message": f"Syncing to sheet {GOOGLE_SHEET_ID[:12]}...", "icon": "🟢"}


def _get_or_create_sheet(spreadsheet, title, index):
    try:
        return spreadsheet.worksheet(title)
    except Exception:
        return spreadsheet.add_worksheet(title=title, rows=1000, cols=20, index=index)


def sync_to_sheet(data):
    client = _get_client()
    if client is None:
        return False, "Google Sheets not available."

    try:
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sheet 1: Full JSON backup
        json_sheet = _get_or_create_sheet(spreadsheet, "Vault JSON", 0)
        json_str = json.dumps(data, indent=2, default=str)
        json_sheet.clear()
        json_sheet.update("A1", [[f"Last synced: {now}"]])
        json_sheet.update("A2", [[json_str]])

        # Sheet 2: Flat table view
        flat_sheet = _get_or_create_sheet(spreadsheet, "Flat View", 1)
        flat_sheet.clear()
        headers = ["Team", "Member", "Artifact Name", "Type", "URL / Path", "Notes", "Created"]
        rows = [headers]
        for t_name, t_data in data.get("teams", {}).items():
            for m_name, m_data in t_data.get("members", {}).items():
                if not m_data.get("artifacts"):
                    rows.append([t_name, m_name, "", "", "", "", ""])
                else:
                    for art in m_data["artifacts"]:
                        rows.append([
                            t_name, m_name,
                            art.get("name", ""), art.get("type", ""),
                            art.get("url", art.get("file_path", "")),
                            art.get("notes", ""), art.get("created_at", ""),
                        ])
        flat_sheet.update(f"A1:G{len(rows)}", rows)
        flat_sheet.format("A1:G1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}
        })

        # Sheet 3: Sync log
        log_sheet = _get_or_create_sheet(spreadsheet, "Sync Log", 2)
        existing = log_sheet.get_all_values()
        if not existing:
            log_sheet.update("A1:D1", [["Timestamp", "Teams", "Members", "Artifacts"]])
            log_sheet.format("A1:D1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}
            })
        total_teams = len(data.get("teams", {}))
        total_members = sum(len(t.get("members", {})) for t in data.get("teams", {}).values())
        total_artifacts = sum(
            len(m.get("artifacts", []))
            for t in data.get("teams", {}).values()
            for m in t.get("members", {}).values()
        )
        next_row = len(existing) + 1
        log_sheet.update(f"A{next_row}:D{next_row}", [
            [now, str(total_teams), str(total_members), str(total_artifacts)]
        ])

        return True, f"Synced to Google Sheets at {now}"

    except Exception as e:
        logger.error(f"Google Sheets sync failed: {e}")
        return False, f"Sync failed: {str(e)}"


def load_from_sheet():
    client = _get_client()
    if client is None:
        return None, "Google Sheets not available."
    try:
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        json_sheet = _get_or_create_sheet(spreadsheet, "Vault JSON", 0)
        json_str = json_sheet.acell("A2").value
        if not json_str:
            return None, "No backup found in Google Sheet."
        data = json.loads(json_str)
        return data, "Loaded from Google Sheets successfully."
    except json.JSONDecodeError:
        return None, "Google Sheet contains invalid JSON."
    except Exception as e:
        logger.error(f"Failed to load from Google Sheets: {e}")
        return None, f"Load failed: {str(e)}"
