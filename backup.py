import argparse
import glob
import importlib.util
import os
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime
from urllib.parse import urlparse

import inquirer
from dotenv import load_dotenv

# Import user configuration
import config


def install_dependencies():
    """Install dependencies from requirements.txt."""
    try:
        # We use standard pip here for user-friendliness on local machines,
        # but the CI uses 'uv' explicitly in the workflow file.
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        exit(1)


def run_command(command, env, log_name):
    """Helper to run subprocess commands."""
    print(f"Generating {log_name}...")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, env=env, timeout=1200)
        print(f"✔ {log_name} created.")
    except subprocess.TimeoutExpired:
        print(f"❌ Error: {log_name} process timed out.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating {log_name}:")
        print(e.stderr)
        return False
    return True


def compress_and_encrypt(source_folder, output_zip, password):
    """Zips a folder with AES-256 encryption using pyzipper."""
    import pyzipper

    print(f"\n📦 Compressing and Encrypting to {output_zip}...")

    try:
        with pyzipper.AESZipFile(output_zip, "w", compression=pyzipper.ZIP_LZMA, encryption=pyzipper.WZ_AES) as zf:
            if password:
                zf.setpassword(password.encode("utf-8"))
                zf.setencryption(pyzipper.WZ_AES, nbits=256)

            for root, _, files in os.walk(source_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(source_folder))
                    zf.write(file_path, arcname)

        print("✔ Secured Archive Created.")
        return True
    except Exception as e:
        print(f"❌ Error during compression: {e}")
        return False


def cleanup_backups(backup_dir, project_prefix):
    """Retention policy logic."""
    print("\n🧹 Running Retention Cleanup...")

    search_pattern = os.path.join(backup_dir, f"{project_prefix}_backup_*.zip")
    files = glob.glob(search_pattern)

    # Filter out Permanent backups
    deletable_files = [f for f in files if "_P.zip" not in f]

    # Sort by modification time (newest first)
    deletable_files.sort(key=os.path.getmtime, reverse=True)

    files_deleted = 0

    # Check Count Limit
    if config.MAX_BACKUPS_PER_PROJECT > 0:
        while len(deletable_files) > config.MAX_BACKUPS_PER_PROJECT:
            file_to_remove = deletable_files.pop()
            try:
                os.remove(file_to_remove)
                print(f"   🗑️ Deleted (Count Limit): {os.path.basename(file_to_remove)}")
                files_deleted += 1
            except OSError as e:
                print(f"   ⚠️ Could not delete {file_to_remove}: {e}")

    # Check Age Limit
    if config.RETENTION_DAYS > 0:
        now = time.time()
        age_limit_seconds = config.RETENTION_DAYS * 86400

        for file_path in deletable_files[:]:
            file_age = now - os.path.getmtime(file_path)
            if file_age > age_limit_seconds:
                try:
                    os.remove(file_path)
                    print(f"   🗑️ Deleted (Old Age): {os.path.basename(file_path)}")
                    files_deleted += 1
                except OSError as e:
                    print(f"   ⚠️ Could not delete {file_path}: {e}")

    if files_deleted == 0:
        print("   No cleanup required.")


def main():
    # --- ARGUMENT PARSING FOR HEADLESS / CI MODE ---
    parser = argparse.ArgumentParser(description="Supabase Backup Tool")
    parser.add_argument("--env", help="Name of the .env file to use (e.g., .production.env)")
    parser.add_argument("--permanent", action="store_true", help="Flag backup as permanent")
    parser.add_argument("--non-interactive", action="store_true", help="Skip interactive prompts")
    args = parser.parse_args()

    if not args.non_interactive:
        # Clear the console for a cleaner interface.
        os.system("cls" if os.name == "nt" else "clear")

        # ASCII Art
        print("""

███████╗██╗   ██╗██████╗  █████╗ ██████╗  █████╗ ███████╗███████╗    ██████╗  █████╗  ██████╗██╗  ██╗██╗   ██╗██████╗ 
██╔════╝██║   ██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝    ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║   ██║██╔══██╗
███████╗██║   ██║██████╔╝███████║██████╔╝███████║███████╗█████╗      ██████╔╝███████║██║     █████╔╝ ██║   ██║██████╔╝
╚════██║██║   ██║██╔═══╝ ██╔══██║██╔══██╗██╔══██║╚════██║██╔══╝      ██╔══██╗██╔══██║██║     ██╔═██╗ ██║   ██║██╔═══╝ 
███████║╚██████╔╝██║     ██║  ██║██████╔╝██║  ██║███████║███████╗    ██████╔╝██║  ██║╚██████╗██║  ██╗╚██████╔╝██║     
╚══════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     
                                                                                                                        """)
        print("Welcome to the Supabase Backup Tool!")

    # 1. Dependency Check
    if importlib.util.find_spec("pyzipper") is None:
        if args.non_interactive:
            print("Installing dependencies for headless run...")
            install_dependencies()
        else:
            questions = [
                inquirer.Confirm("install", message="pyzipper is missing. Install dependencies?", default=True)
            ]
            ans = inquirer.prompt(questions)
            if ans and ans.get("install"):
                install_dependencies()
            else:
                print("pyzipper is required for encryption.")
                exit(1)

    # 2. Select .env file from 'envs/' folder
    env_dir = "envs"
    if not os.path.exists(env_dir):
        if args.non_interactive:
            os.makedirs(env_dir)
        else:
            print(f"Error: The '{env_dir}' folder is missing.")
            print(f"Please create an '{env_dir}' folder and move your .env files there.")
            exit(1)

    selected_env_filename = None

    if args.env:
        # Headless mode
        selected_env_filename = args.env
        if not os.path.exists(os.path.join(env_dir, selected_env_filename)):
            print(f"Error: Env file {selected_env_filename} not found in {env_dir}.")
            exit(1)
    else:
        # Interactive mode
        env_files = [f for f in os.listdir(env_dir) if f.endswith(".env")]
        if not env_files:
            print(f"Error: No .env files found in '{env_dir}/'.")
            exit(1)
        questions = [inquirer.List("env_file", message="Select project config", choices=env_files)]
        answers = inquirer.prompt(questions)
        if not answers:
            exit(1)
        selected_env_filename = answers["env_file"]

    selected_env_path = os.path.join(env_dir, selected_env_filename)

    # --- PREFIX LOGIC ---
    project_prefix = selected_env_filename.replace(".env", "")
    if project_prefix.startswith("."):
        project_prefix = project_prefix[1:]

    # --- PERMANENT TOGGLE ---
    is_permanent = False
    if args.permanent:
        is_permanent = True
    elif not args.non_interactive and config.ALLOW_PERMANENT_TAGGING:
        q_perm = [
            inquirer.Confirm(
                "permanent", message="Mark this backup as PERMANENT (protect from cleanup)?", default=False
            )
        ]
        ans_perm = inquirer.prompt(q_perm)
        is_permanent = ans_perm["permanent"] if ans_perm else False

    # 3. Folder Setup
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    suffix = "_P" if is_permanent else ""

    folder_name = f"{project_prefix}_backup_{timestamp}{suffix}" if project_prefix else f"backup_{timestamp}{suffix}"

    base_dir = "backups"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    target_folder = os.path.join(base_dir, folder_name)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # 4. Load Credentials
    load_dotenv(dotenv_path=selected_env_path)

    supabase_db_uri = os.getenv("SUPABASE_DB_URI")
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("DB_PASSWORD")
    zip_password = os.getenv("ZIP_PASSWORD")

    env = os.environ.copy()
    common_args = []

    # Connection Logic
    if supabase_db_uri:
        if not args.non_interactive:
            print(f"Connecting using URI from {selected_env_filename}...")
        common_args = ["--dbname", supabase_db_uri, "--no-password"]
    else:
        if not args.non_interactive:
            print(f"Connecting using URL/Pass from {selected_env_filename}...")
        if not supabase_url or not db_password:
            print("Error: Credentials missing in .env")
            exit(1)
        try:
            parsed = urlparse(supabase_url)
            if parsed.hostname is None:
                raise ValueError("Invalid URL: Hostname not found.")

            host = f"db.{parsed.hostname.split('.')[0]}.supabase.co"
            try:
                socket.gethostbyname(host)
            except socket.gaierror:
                pass  # Proceed anyway in CI/Headless
            common_args = ["-h", host, "-p", "5432", "-U", "postgres", "--no-password"]
            env["PGPASSWORD"] = db_password
        except Exception as e:
            print(f"Connection Error: {e}")
            exit(1)

    # 5. Execute Dumps
    is_win = platform.system() == "Windows"
    pg_dump = "pg_dump.exe" if is_win else "pg_dump"
    pg_dumpall = "pg_dumpall.exe" if is_win else "pg_dumpall"

    roles_file = os.path.join(target_folder, "roles.sql")
    schema_file = os.path.join(target_folder, "schema.sql")
    data_file = os.path.join(target_folder, "data.sql")

    print("\n--- Starting Backup ---")

    # Roles
    run_command(
        [pg_dumpall] + common_args + ["--clean", "--if-exists", "--roles-only", "-f", roles_file], env, "roles.sql"
    )

    # Schema
    s_args = common_args if supabase_db_uri else common_args + ["-d", "postgres"]
    run_command([pg_dump] + s_args + ["--schema-only", "-f", schema_file], env, "schema.sql")

    # Data
    d_args = common_args if supabase_db_uri else common_args + ["-d", "postgres"]
    run_command(
        [pg_dump] + d_args + ["--data-only", "--schema=public", "--schema=cron", "--schema=auth", "-f", data_file],
        env,
        "data.sql",
    )

    # 6. Compression & Encryption
    zip_filename = os.path.join(base_dir, f"{folder_name}.zip")

    if not zip_password:
        print("\n⚠️  WARNING: ZIP_PASSWORD not found. Archive will NOT be encrypted.")

    success = compress_and_encrypt(target_folder, zip_filename, zip_password)

    # 7. Cleanup Raw Folder
    if success:
        try:
            shutil.rmtree(target_folder)
            print(f"✔ Raw files removed. Backup secured at: {zip_filename}")
        except OSError as e:
            print(f"⚠️ Error removing raw folder: {e}")
    else:
        print("❌ Encryption failed. Keeping raw folder for safety.")

    # 8. Run Retention Policy
    cleanup_backups(base_dir, project_prefix)

    print("\n---------------------------------")
    print("Process Finished.")


if __name__ == "__main__":
    main()
