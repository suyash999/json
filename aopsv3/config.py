"""
config.py — Vault configuration.

Google Sheets Sync Setup:
  1. pip install gspread google-auth
  2. Replace credentials/service_account.json with your real service account key
  3. Create a Google Sheet and share it with the service account email (Editor)
  4. Paste the Sheet ID below (the long string between /d/ and /edit in the URL)
  5. Set GOOGLE_SYNC_ENABLED = True
"""

# ── Google Sheets Sync ──────────────────────────────────────────────────
GOOGLE_SYNC_ENABLED = False
GOOGLE_SHEET_ID = ""
CREDENTIALS_FILE = "credentials/service_account.json"

# ── Admin Settings ──────────────────────────────────────────────────────
ADMIN_DELETE_PASSWORD = "ebay@delete2026"

# ── Backup Settings ─────────────────────────────────────────────────────
MAX_LOCAL_BACKUPS = 10
