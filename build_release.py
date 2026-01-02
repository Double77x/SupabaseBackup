import os
import shutil
import zipfile

import PyInstaller.__main__

# --- CONFIGURATION ---
APP_NAME = "SupabaseManager"
ENGINE_NAME = "backup_engine"
ICON_PATH = os.path.join("assets", "logo.ico")  # Must be .ico for Windows
DIST_FOLDER = "SupabaseBackupTool"
ASSETS_DIR = "assets"


def clean():
    """Wipes previous build artifacts to ensure a fresh start."""
    for folder in ["build", "dist", DIST_FOLDER]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    print("✨ Cleaned previous build artifacts.")


def build_exe(script_name, exe_name, windowed=False):
    """Runs PyInstaller with your specific settings."""
    print(f"🔨 Building {exe_name}...")

    args = [
        script_name,
        f"--name={exe_name}",
        "--onefile",
        "--clean",
        f"--icon={ICON_PATH}" if os.path.exists(ICON_PATH) else None,
    ]

    if windowed:
        args.append("--windowed")  # Hide console for GUI

    # Remove None values
    args = [arg for arg in args if arg]

    PyInstaller.__main__.run(args)


def create_distribution():
    """Assembles the final portable folder."""
    print("📦 Assembling portable package...")

    os.makedirs(DIST_FOLDER, exist_ok=True)

    # 1. Copy EXEs
    shutil.copy(os.path.join("dist", f"{APP_NAME}.exe"), DIST_FOLDER)
    shutil.copy(os.path.join("dist", f"{ENGINE_NAME}.exe"), DIST_FOLDER)

    # 2. Copy Assets Folder
    dest_assets = os.path.join(DIST_FOLDER, "assets")
    if os.path.exists(ASSETS_DIR):
        if os.path.exists(dest_assets):
            shutil.rmtree(dest_assets)
        shutil.copytree(ASSETS_DIR, dest_assets)

    # 3. Create Empty Data Folders
    os.makedirs(os.path.join(DIST_FOLDER, "envs"), exist_ok=True)
    os.makedirs(os.path.join(DIST_FOLDER, "backups"), exist_ok=True)

    print(f"✅ Folder '{DIST_FOLDER}' created successfully.")


def zip_package():
    """Zips the folder for easy distribution."""
    zip_filename = f"{DIST_FOLDER}.zip"
    print(f"🤐 Zipping to {zip_filename}...")

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(DIST_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                # Archive name should be relative to the DIST_FOLDER
                arcname = os.path.relpath(file_path, os.path.dirname(DIST_FOLDER))
                zipf.write(file_path, arcname)

    print(f"🚀 Ready for release: {zip_filename}")


if __name__ == "__main__":
    clean()
    # Build Engine (Console mode, so users can see errors if they run it manually)
    build_exe("backup.py", ENGINE_NAME, windowed=False)

    # Build GUI (Windowed mode, no black box)
    build_exe("gui.py", APP_NAME, windowed=True)

    create_distribution()
    zip_package()
