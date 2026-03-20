# 🏛️ eBay IAC — Artifact Vault

**Enterprise-grade artifact management portal for eBay Infrastructure & Cloud teams.**

A Streamlit application that provides a visual, hierarchical interface for storing and organizing team artifacts — links (Zeta, GitHub, Tableau), files (PowerPoint, Excel, PDF), and more.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Hierarchical View** | eBay IAC → Teams → Members → Artifacts |
| **Multi-Upload** | Drag-and-drop multiple files at once (pptx, xlsx, pdf, etc.) |
| **Link Support** | Auto-classifies Zeta, GitHub, Tableau, and generic URLs |
| **Renaming** | Rename teams, members, and artifacts freely |
| **Access Control** | Anyone can add; delete requires admin password |
| **Tree View** | Full organization tree in a single view |
| **Auto-Backup** | JSON backup on every data change (keeps 10 rolling) |
| **Export** | Download full vault as JSON any time |
| **Enterprise UI** | Dark theme with eBay brand colors |

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+

### 2. Install Dependencies
```bash
cd ebay_artifact_vault
pip install -r requirements.txt
```

Or install individually:
```bash
pip install streamlit==1.41.1 Pillow==11.1.0 watchdog==6.0.0
```

### 3. Run the App
```bash
streamlit run app.py --server.port 8501
```

The app opens at **http://localhost:8501**

---

## 📁 Project Structure

```
ebay_artifact_vault/
├── app.py                  # Main Streamlit application
├── data_manager.py         # Data persistence & CRUD operations
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── data/                   # Auto-created at runtime
    ├── vault_data.json     # Live data (auto-backup)
    ├── uploads/            # Uploaded files stored here
    └── backups/            # Rolling JSON backups (last 10)
```

---

## 🔐 Admin Password

Delete operations require the admin password: `ebay@delete2026`

To change it, edit the `ADMIN_DELETE_PASSWORD` constant in `data_manager.py`.

---

## 🧭 Navigation Guide

| Page | Purpose |
|---|---|
| 🏠 Dashboard | Overview stats + browse all teams/members/artifacts |
| 🏗️ Manage Teams | Create and rename teams |
| 👤 Manage Members | Add and rename team members |
| 📦 Add Artifacts | Upload files or add links to a member |
| 🗑️ Admin Delete | Password-protected deletion of teams/members/artifacts |
| 🌳 Tree View | Full org hierarchy in tree format |
| 💾 Backup & Export | Download JSON backup, view backup history |

---

## 🔗 Supported Artifact Types

**Links (auto-detected by URL):**
- 🔗 Zeta Link (URLs containing "zeta")
- 🐙 GitHub Link (URLs containing "github")
- 📊 Tableau Dashboard (URLs containing "tableau")
- 🌐 Generic Web Link (all other URLs)

**Files (auto-detected by extension):**
- 📑 PowerPoint (.ppt, .pptx)
- 📗 Excel (.xls, .xlsx, .csv)
- 📕 PDF (.pdf)
- 📎 Other File (all other types)

---

## 🛡️ Enterprise Considerations

- **Data Integrity**: All mutations auto-save with timestamped backups
- **Access Control**: Write-open, delete-restricted model
- **Audit Trail**: Created-at timestamps on all entities
- **Portability**: Single JSON file — easy to migrate or integrate with Google Drive
- **Extensibility**: Modular `data_manager.py` can be swapped for any backend (GDrive API, S3, database)

---

## 🔄 Google Drive Integration (Future)

To sync `vault_data.json` to Google Drive, you can:
1. Use the Google Drive API with a service account
2. Use `pydrive2` or `google-api-python-client`
3. Set up a cron job or use Streamlit's `on_change` callbacks to push on every save

The `save_data()` function in `data_manager.py` is the single point of persistence — add your GDrive upload call there.
