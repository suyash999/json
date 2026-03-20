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

# Set to True once your credentials and sheet ID are configured
GOOGLE_SYNC_ENABLED = False

# The ID from your Google Sheet URL:
# https://docs.google.com/spreadsheets/d/THIS_IS_THE_SHEET_ID/edit
GOOGLE_SHEET_ID = ""

# Path to service account credentials (default: credentials/service_account.json)
# Change this if you store the key elsewhere
CREDENTIALS_FILE = "credentials/service_account.json"


# ── Admin Settings ──────────────────────────────────────────────────────

# Password required for delete operations
ADMIN_DELETE_PASSWORD = "ebay@delete2026"


# ── Backup Settings ─────────────────────────────────────────────────────

# Number of local JSON backups to keep (rolling)
MAX_LOCAL_BACKUPS = 10
