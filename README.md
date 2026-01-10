# Supabase Backup - CLI & GUI

This tool provides a secure, automated way to backup your Supabase PostgreSQL databases. It now offers two modes of operation:

1. **Supabase Manager (GUI):** A user-friendly desktop application to manage environments, retention policies, and trigger backups manually.
2. **Backup Engine (CLI):** A headless executable designed for Cron jobs, GitHub Actions, and automated scheduling.

**CLI**

![Demo](assets/readme_demo.png)

**PORTABLE GUI**

![1767910751309](assets/demo_gui.png "GUI Interface")

## Overview

## 🚀 Features

- **🆕 Modern GUI Dashboard** : Manage multiple projects, create configs, and view execution logs in a beautiful Catppuccin-themed interface.
- **🆕 Portable Application** : Runs as a standalone Windows executable (`.exe`) without needing Python installed.
- **🆕 Integrated Config Manager** : Create and edit connection details directly inside the app—no more manual file editing.
- **Modular Architecture** : Splits backups into `roles.sql`, `schema.sql`, and `data.sql` for granular restoration.
- **AES-256 Encryption** : Automatically compresses and encrypts backups into protected `.zip` archives.
- **Automated Retention** : Built-in policy engine cleans up old backups based on your settings (e.g., "Keep last 5 files").
- **Permanent Snapshots** : Tag specific backups as "Permanent" to protect them from auto-deletion forever.
- **Headless Mode** : Full CLI argument support for automation.

## ⚠️ Critical Prerequisites

Before using this tool, please ensure you meet the following requirements.

### 1. PostgreSQL Binaries (Required for Backup)

Whether you use the GUI or the CLI, **this tool requires PostgreSQL Client Tools to be available** to perform the actual extraction.

- **Option A: Install Globally (Recommended)**
  - Download and install [PostgreSQL Command Line Tools for Windows](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads "null").
- **Option B: Portable Mode**
  - If you cannot install PostgreSQL globally, download the binaries zip, extract `pg_dump.exe` (and its DLL dependencies), and place them **inside the same folder** as `SupabaseManager.exe`.

### 2. Encryption-Compatible Archiver (Required for Extraction)

This tool uses **AES-256** encryption to secure your backups.
❌ **Windows File Explorer** (the default zip tool) **cannot** open AES-encrypted zip files. It will likely show an empty folder or throw an error.

✅ **You must use a compatible tool to extract your backups:**

- [7-Zip](https://www.7-zip.org/ "null"), NanaZip, PeaZip

## 📥 Installation

### Method 1: Portable App (Recommended for Users)

1. Download the latest **Release ZIP** (`SupabaseBackupTool.zip`) from GitHub.
2. Extract the folder to a location of your choice (e.g., Desktop or Documents).
3. Ensure `pg_dump` is installed (see Prerequisites above).
4. Double-click **`SupabaseManager.exe`** to launch the dashboard.

### Method 2: Running from Source (Developers)

1. **Clone the repository**:
   ```
   git clone [https://github.com/Double77x/supabase-backup-tool.git](https://github.com/your-username/supabase-backup-tool.git)
   cd supabase-backup-tool
   ```
2. **Install Dependencies** (Using `uv` is recommended for speed):
   ```
   pip install uv
   uv pip install -r requirements.txt
   ```
3. **Run the GUI**:
   ```
   python gui.py
   ```

## 🖥️ Using the GUI (Supabase Manager)

The GUI acts as a central control center for your backups.

1. **Create a Project** : Click the **+ New** button. Enter your Project Name (e.g., "Production") and Connection URI.
2. **Run a Backup** : Select your project from the dropdown and click **START BACKUP** .
3. **Logs** : Real-time logs will appear in the terminal window at the bottom.
4. **Settings** : Click the ⚙️ (Gear Icon) to configure retention rules (e.g., "Max 5 backups").
5. **Edit Configs** : Select a project and click the **Edit** (Pencil Icon) to update passwords or URIs.

> **Note:** The GUI saves your configurations as `.env` files in the `envs/` folder and your preferences in `settings.json`.

## 🤖 Automation & Headless Mode

For scheduled tasks (Cron) or CI/CD pipelines, use the CLI engine.

### If using the Portable App:

Use `backup_engine.exe` located in your extracted folder.

```
# Run a backup for the 'production' environment (looks for .production.env)
.\backup_engine.exe --env .production.env --non-interactive

# Create a permanent backup that won't be deleted
.\backup_engine.exe --env .production.env --non-interactive --permanent
```

### If running from Source (Python):

```
python backup.py --env .production.env --non-interactive
```

## 🔐 Configuration Details

### Connection String Guide

To ensure stability during large backups, use the **Transaction Pooler** connection string.

1. Go to your Supabase Project Dashboard.
2. Navigate to **Settings** > **Database** .
3. Copy the **URI** (Mode: Transaction) and paste it into the tool.
   - _Format:_ `postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres?pgbouncer=true`

### Environment Files

The tool stores credentials in `envs/`. The file name determines the backup prefix.

- `envs/.production.env` → Backup file: `production_backup_2024...zip`

### Global Settings (`settings.json`)

Managed via the GUI Settings menu, but can be edited manually:

```
{
    "max_backups": 5,        // Keep last 5 files per project
    "retention_days": 30     // Delete files older than 30 days
}
```

## ☁️ GitHub Actions (Cloud Automation)

You can run this tool entirely in the cloud using GitHub Actions.

1. **Set Secrets** in your Repo (Settings > Secrets > Actions):
   - `PROD_DB_URI`
   - `ZIP_PASSWORD`
2. **Add the Workflow** : Uncomment the schedule block in `.github/workflows/backup.yml` to enable daily runs.

The workflow will spin up a runner, inject credentials, perform the backup, and commit the encrypted zip back to your repository.

## ♻️ Restoration Guide

Since backups are modular, you can restore the entire database or specific parts.

1. **Unzip the Archive** :
   **Important:** Use 7-Zip or a similar tool (see Prerequisites) to handle the encryption.

```
   # Example using command line unzip (if installed) or 7z.exe
   7z x production_backup_2024-01-01.zip -orestore_folder
   # You will be prompted for your ZIP_PASSWORD
```

1. **Run Restoration Commands** :
   Use the [Supabase CLI](https://supabase.com/docs/guides/cli "null") or `psql` to restore:

```
   # 1. Restore Roles (Caution: Overwrites permissions)
   supabase db execute --db-url "$SUPABASE_DB_URI" -f restore_folder/roles.sql

   # 2. Restore Schema (Tables, Views, Functions)
   supabase db execute --db-url "$SUPABASE_DB_URI" -f restore_folder/schema.sql

   # 3. Restore Data (Rows)
   supabase db execute --db-url "$SUPABASE_DB_URI" -f restore_folder/data.sql
```

## 🔮 Roadmap

- [ ] **Cloud Storage Integration** : Direct upload to AWS S3, Cloudflare R2, or Google Cloud Storage.
- [ ] **Notification Webhooks** : Slack/Discord alerts on backup success/failure.
- [ ] **One-Click Restore** : A `restore.exe` utility to automate the import process.

## 📝 License

This project is licensed under the MIT License.
