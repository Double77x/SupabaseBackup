# Supabase Backup CLI

A simple and interactive command-line tool to back up your Supabase PostgreSQL databases.

V2: This tool now goes beyond simple database dumps. It splits your backup into granular components (Roles, Schema, Data), encrypts them with AES-256, manages retention policies automatically, and supports headless execution for CI/CD pipelines.

![Demo](assets/readme_demo.png)

## Overview

## 🚀 Features

- **Modular Architecture** : Splits backups into `roles.sql`, `schema.sql`, and `data.sql` for granular debugging and partial restoration.
- **AES-256 Encryption** : Automatically compresses and encrypts backups into protected `.zip` archives.
- **Multi-Project Support** : Seamlessly switch between Production, Staging, and Dev environments using config files.
- **Automated Retention** : Built-in policy engine to clean up old backups while preserving "Permanent" tagged snapshots.
- **Headless Mode** : Full CLI argument support for running in Cron jobs or GitHub Actions.
- **Smart Naming** : Automatically detects project names from config files (e.g., `.production.env` -> `production_backup_...`).

---

## 🛠 Prerequisites

- **Python 3.9+** installed.
- **PostgreSQL Client Tools** (`pg_dump` and `pg_dumpall`) must be in your system PATH.
  - _Windows_ : Install [PostgreSQL](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) (Command Line Tools only).
  - _macOS_ : `brew install libpq && brew link --force libpq`
  - _Linux_ : `sudo apt-get install postgresql-client`

---

## ⚙️ Installation & Setup

1. **Clone the repository**
   **Bash**

   ```
   git clone https://github.com/your-username/supabase-backup-tool.git
   cd supabase-backup-tool
   ```

2. **Install Python Dependencies**
   The script will verify and install dependencies on the first run, or you can do it manually:
   **Bash**

   ```
   pip install -r requirements.txt
   # OR using uv (recommended)
   pip install uv
   uv pip install -r requirements.txt
   ```

3. **Create the `envs` Directory**
   This folder keeps your configuration files organized and ignored by Git.
   **Bash**

   ```
   mkdir envs
   ```

---

## 🔐 Configuration

This tool uses environment files located in the `envs/` folder to manage credentials.

### 1. Create Config Files

Create a file for each project you want to backup. **Naming convention matters** : the name of the file becomes the prefix of your backup.

- `envs/.production.env` → `production_backup_2024...zip`
- `envs/.staging.env` → `staging_backup_2024...zip`

### 2. File Content

Inside each `.env` file, add your credentials:

```
# envs/.production.env

# 1. Connection String (Recommended)
SUPABASE_DB_URI=postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres?pgbouncer=true

# 2. Encryption Password
ZIP_PASSWORD=YourStrongPasswordHere!
```

### 3. How to get your Connection String

To ensure stability, use the **Transaction Pooler** connection string.

1. Go to your Supabase Project Dashboard.
2. Navigate to **Settings** > **Database** .
3. Or use this direct link (replace `[YOUR-PROJECT-REF]` with your project ID):
   > [https://supabase.com/dashboard/project/](https://supabase.com/dashboard/project/)[YOUR-PROJECT-REF]/settings/database?showConnect=true&method=transaction
4. Copy the **URI** (Mode: Transaction) and paste it into `SUPABASE_DB_URI`.

---

## 🖥️ Usage

### Interactive Mode (Local)

Simply run the script. It will scan your `envs/` folder and ask you which project to back up.

**Bash**

```
python backup.py
```

- **Select Project** : Choose from the detected `.env` files.
- **Permanent Tag** : You can optionally mark a backup as "Permanent" to prevent the cleanup script from ever deleting it.

### Headless Mode (Automation)

For cron jobs or scripts, bypass the UI using arguments:

**Bash**

```
# Syntax: python backup.py --env [FILENAME] --non-interactive [--permanent]

python backup.py --env .production.env --non-interactive
```

---

## 🤖 GitHub Actions Automation

You can run this tool entirely in the cloud using GitHub Actions. The workflow will:

1. Spin up a runner.
2. Inject credentials from GitHub Secrets.
3. Perform the backup.
4. Commit the encrypted `.zip` file back to your repo (or you can modify it to upload to S3).

### 1. Set GitHub Secrets

Go to your **Repository Settings** > **Secrets and variables** > **Actions** and add:

- `PROD_DB_URI`: Connection string for production.
- `STAGING_DB_URI`: Connection string for staging.
- `ZIP_PASSWORD`: Password for encryption.

### 2. Add the Workflow

Copy the content of `.github/workflows/backup.yml` provided in this repo. It runs daily at 02:00 UTC. By default, the schedule block is commented out. You must un-comment this to enable the automatic trigger.

---

## 🧹 Retention Policy (`config.py`)

To prevent your disk from filling up, the tool includes a `config.py` file where you can define rules:

**Python**

```
# config.py

# Keep the last 5 backups per project
MAX_BACKUPS_PER_PROJECT = 5

# Delete backups older than 30 days
RETENTION_DAYS = 30
```

> **Note:** Any backup marked as **Permanent** (suffix `_P.zip`) is **never** deleted, regardless of these settings.

---

## ♻️ Restoration Guide

Since the backups are modular, you can choose to restore the entire database or just specific parts.

1. **Unzip the Archive** :
   **Bash**

```
   # You will need your ZIP_PASSWORD to extract this
   unzip production_backup_2024-01-01.zip -d restore_folder
```

1. **Run Restoration Commands** :
   Use the [Supabase CLI](https://supabase.com/docs/guides/cli) to restore in the correct order:
   **Bash**

```
   # 1. Restore Roles (Caution: Overwrites permissions)
   supabase db execute --db-url "$SUPABASE_DB_URI" -f restore_folder/roles.sql

   # 2. Restore Schema (Tables, Views, Functions)
   supabase db execute --db-url "$SUPABASE_DB_URI" -f restore_folder/schema.sql

   # 3. Restore Data (Rows)
   supabase db execute --db-url "$SUPABASE_DB_URI" -f restore_folder/data.sql
```

---

## 🔮 Roadmap

We are actively working on:

- [ ] **Cloud Storage Integration** : Direct upload to AWS S3, Cloudflare R2, or Google Cloud Storage.
- [ ] **Notification Webhooks** : Slack/Discord alerts on backup success or failure.
- [ ] **`restore.py` Helper** : An interactive script to automate the restoration commands above.
- [ ] **Supabase Storage** : Backup logic for actual file assets (images/avatars) using Supabase API.

## 📝 License

This project is licensed under the MIT License.
