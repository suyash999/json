# eBay IAC — Artifact Vault v3

Visual tree-based artifact management for eBay Infrastructure & Cloud.

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## What it does

A visual tree where **eBay IAC** (root) branches into **Teams**, which branch into **Members**, which branch into **Artifacts** (links, files). The tree auto-renders with SVG connector lines and color-coded nodes.

Every save writes to local JSON **and** a Google Sheet (if configured) for enterprise backup.

## Pages

| Page | What |
|---|---|
| Tree View | Visual node tree + quick-add popovers + detailed list below |
| Add Artifacts | Links (Zeta, GitHub, Tableau) and multi-file upload |
| Manage Structure | Create teams and add members |
| Rename | Rename teams, members, artifacts |
| Admin Delete | Password-protected deletion (`ebay@delete2026`) |
| Backup & Export | Download JSON, Google Sheets push/pull, view rolling backups |

## Files

```
ebay_artifact_vault_v3/
├── app.py                          # Streamlit UI
├── data_manager.py                 # CRUD + JSON persistence + Google sync trigger
├── tree_renderer.py                # Visual HTML/SVG tree generator
├── google_sync.py                  # Google Sheets read/write module
├── config.py                       # All settings (Sheet ID, passwords, toggles)
├── credentials/
│   └── service_account.json        # ← Replace with your real key
├── requirements.txt
├── run.sh
└── data/                           # Auto-created at runtime
    ├── vault_data.json
    ├── uploads/
    └── backups/
```

## Google Sheets setup

### 1. Google Cloud project
- Go to [console.cloud.google.com](https://console.cloud.google.com)
- Create a new project (or use existing)
- Enable **Google Sheets API** and **Google Drive API**

### 2. Service account
- Go to **IAM & Admin → Service Accounts**
- Create a service account → download the JSON key
- Save it as `credentials/service_account.json` (replacing the placeholder)

### 3. Google Sheet
- Create a new Google Sheet
- Share it with the service account's `client_email` (from the JSON key) → give **Editor** access
- Copy the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`

### 4. Config
Edit `config.py`:
```python
GOOGLE_SYNC_ENABLED = True
GOOGLE_SHEET_ID = "paste-your-sheet-id-here"
```

### 5. Install dependencies
```bash
pip install gspread google-auth
```

### What gets synced
| Sheet | Content |
|---|---|
| Vault JSON | Full JSON backup in cell A2 (loadable for restore) |
| Flat View | Spreadsheet table: Team, Member, Artifact, Type, URL, Date |
| Sync Log | Timestamp + team/member/artifact counts per sync |

### How it works
- Every `save_data()` call writes to local JSON first, then pushes to Google Sheets
- If Google Sheets is unavailable (no creds, network down), the local save still works — sync failures never break the app
- You can manually push/pull from the **Backup & Export** page
- Restore from Sheet overwrites local data with the Sheet's JSON backup
