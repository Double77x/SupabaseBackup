import asyncio
import base64
import json
import os
import sys

from nicegui import app, ui

# --- CONSTANTS & PATHS ---
# Detect if running as PyInstaller EXE or normal script
IS_FROZEN = getattr(sys, "frozen", False)
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0])) if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))

ENV_DIR = os.path.join(BASE_DIR, "envs")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

os.makedirs(ENV_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# Serve assets folder so generic paths work
app.add_static_files("/assets", ASSETS_DIR)

# --- SETTINGS MANAGEMENT ---
DEFAULT_SETTINGS = {"max_backups": 5, "retention_days": 30}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return DEFAULT_SETTINGS


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


app_settings = load_settings()


# --- HELPER: PARSE ENV FILE ---
def parse_env_file(filepath):
    """Reads an .env file and returns a dict of key-value pairs."""
    data = {"SUPABASE_DB_URI": "", "ZIP_PASSWORD": ""}
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    data[key] = value
    return data


# --- CATPPUCCIN PALETTES ---
THEME_LATTE = {
    "primary": "#40a02b",
    "secondary": "#e6e9ef",
    "accent": "#40a02b",
    "dark": "#1e1e2e",
    "positive": "#40a02b",
    "negative": "#d20f39",
    "background": "#eff1f5",
    "card": "#ffffff",
    "text": "#4c4f69",
    "border": "#ccd0da",
    "terminal_bg": "#dce0e8",
    "terminal_text": "#4c4f69",
    "btn_text": "#ffffff",
    "input_bg": "#ffffff",
}

THEME_FRAPPE = {
    "primary": "#a6e3a1",
    "secondary": "#303446",
    "accent": "#a6e3a1",
    "dark": "#1e1e2e",
    "positive": "#a6e3a1",
    "negative": "#e78284",
    "background": "#292c3c",
    "card": "#303446",
    "text": "#c6d0f5",
    "border": "#414559",
    "terminal_bg": "#232634",
    "terminal_text": "#a6e3a1",
    "btn_text": "#303446",
    "input_bg": "#303446",
}

# --- GLOBAL STYLES ---
STYLE_CSS = """
<style>
    :root {
        --radius: 0.5rem;
        --terminal-bg: #1e1e2e;
        --terminal-text: #a6e3a1;
    }
    
    body {
        font-family: 'Inter', sans-serif;
        overflow: hidden;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .nicegui-content {
        padding: 0 !important;
        margin: 0 !important;
        width: 100%;
        height: 100vh;
    }
    
    .shadcn-card {
        border-radius: var(--radius);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid; 
    }

    /* INPUTS & DROPDOWNS */
    .q-field--outlined .q-field__control {
        border-radius: var(--radius) !important;
    }
    .q-menu {
        border-radius: var(--radius) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* TERMINAL */
    .terminal-window {
        background-color: var(--terminal-bg) !important;
        color: var(--terminal-text) !important;
        border-radius: var(--radius);
        font-family: 'JetBrains Mono', monospace;
        border: 1px solid transparent;
        transition: background-color 0.3s, color 0.3s;
    }
    
    /* BUTTONS */
    .q-btn {
        text-transform: none !important;
        font-weight: 600;
        border-radius: var(--radius) !important;
        letter-spacing: 0.01em;
    }
</style>
"""


def get_env_files():
    return [f for f in os.listdir(ENV_DIR) if f.endswith(".env")]


@ui.page("/")
def main_page():
    ui.add_head_html(STYLE_CSS)

    is_dark = ui.dark_mode()
    is_dark.enable()

    # --- HELPER: REFRESH DROPDOWN ---
    def refresh_envs():
        files = get_env_files()
        env_dropdown.options = files
        # Keep selection valid or default to first
        if files:
            if not env_dropdown.value or env_dropdown.value not in files:
                env_dropdown.value = files[0]
        else:
            env_dropdown.value = None
        env_dropdown.update()

    # --- THEME ENGINE ---
    def apply_theme():
        theme = THEME_FRAPPE if is_dark.value else THEME_LATTE

        ui.colors(
            primary=theme["primary"],
            secondary=theme["secondary"],
            accent=theme["accent"],
            positive=theme["positive"],
            negative=theme["negative"],
        )

        bg_container.style(f"background-color: {theme['background']}; color: {theme['text']}")
        main_card.style(f"background-color: {theme['card']}; border-color: {theme['border']}")

        # Apply to Modals
        new_project_card.style(
            f"background-color: {theme['card']}; color: {theme['text']}; border-color: {theme['border']}"
        )
        edit_project_card.style(
            f"background-color: {theme['card']}; color: {theme['text']}; border-color: {theme['border']}"
        )
        settings_card.style(
            f"background-color: {theme['card']}; color: {theme['text']}; border-color: {theme['border']}"
        )

        ui.run_javascript(f"""
            document.documentElement.style.setProperty('--terminal-bg', '{theme["terminal_bg"]}');
            document.documentElement.style.setProperty('--terminal-text', '{theme["terminal_text"]}');
        """)

        # Update text color for buttons to ensure contrast
        for btn in [start_btn, save_config_btn, update_config_btn, save_settings_btn, create_new_btn]:
            btn.style(f"color: {theme['btn_text']} !important")

        env_dropdown.update()

    def toggle_theme():
        is_dark.toggle()
        apply_theme()

    # --- DIALOGS ---

    # 1. New Project Dialog
    with ui.dialog() as new_project_dialog:
        with ui.card().classes("shadcn-card w-96 p-6 no-shadow") as new_project_card:
            ui.label("New Project Configuration").classes("text-lg font-bold mb-4")

            name_input = ui.input("Project Name (e.g. production)").props("outlined dense").classes("w-full mb-3")
            uri_input = ui.input("Supabase DB URI").props("outlined dense").classes("w-full mb-3")
            pass_input = ui.input("Zip Password").props("outlined dense type=password").classes("w-full mb-6")

            def save_new_env():
                if not name_input.value or not uri_input.value:
                    ui.notify("Name and URI are required", type="warning")
                    return

                filename = f".{name_input.value}.env"
                filepath = os.path.join(ENV_DIR, filename)

                with open(filepath, "w") as f:
                    f.write(f"SUPABASE_DB_URI={uri_input.value}\n")
                    f.write(f"ZIP_PASSWORD={pass_input.value}\n")

                ui.notify(f"Created {filename}", type="positive")
                refresh_envs()
                env_dropdown.value = filename
                new_project_dialog.close()
                name_input.value = ""
                uri_input.value = ""
                pass_input.value = ""

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=new_project_dialog.close).props("flat color=grey")
                save_config_btn = ui.button("Create", on_click=save_new_env).props("unelevated").classes("px-4")

    # 2. Edit Project Dialog
    with ui.dialog() as edit_project_dialog:
        with ui.card().classes("shadcn-card w-96 p-6 no-shadow") as edit_project_card:
            ui.label("Edit Configuration").classes("text-lg font-bold mb-4")

            edit_uri_input = ui.input("Supabase DB URI").props("outlined dense").classes("w-full mb-3")
            edit_pass_input = ui.input("Zip Password").props("outlined dense type=password").classes("w-full mb-6")

            def open_edit_dialog():
                if not env_dropdown.value:
                    ui.notify("No project selected", type="warning")
                    return

                filepath = os.path.join(ENV_DIR, env_dropdown.value)
                data = parse_env_file(filepath)

                edit_uri_input.value = data.get("SUPABASE_DB_URI", "")
                edit_pass_input.value = data.get("ZIP_PASSWORD", "")
                edit_project_dialog.open()

            def update_env():
                if not env_dropdown.value:
                    ui.notify("No project selected", type="warning")
                    return

                filepath = os.path.join(ENV_DIR, env_dropdown.value)
                with open(filepath, "w") as f:
                    f.write(f"SUPABASE_DB_URI={edit_uri_input.value}\n")
                    f.write(f"ZIP_PASSWORD={edit_pass_input.value}\n")

                ui.notify(f"Updated {env_dropdown.value}", type="positive")
                edit_project_dialog.close()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=edit_project_dialog.close).props("flat color=grey")
                update_config_btn = ui.button("Save Changes", on_click=update_env).props("unelevated").classes("px-4")

    # 3. Settings Dialog
    with ui.dialog() as settings_dialog:
        with ui.card().classes("shadcn-card w-96 p-6 no-shadow") as settings_card:
            ui.label("Global Settings").classes("text-lg font-bold mb-4")

            max_backups_input = (
                ui.number("Max Backups per Project", value=app_settings["max_backups"])
                .props("outlined dense")
                .classes("w-full mb-3")
            )
            retention_days_input = (
                ui.number("Retention Days", value=app_settings["retention_days"])
                .props("outlined dense")
                .classes("w-full mb-4")
            )

            def save_app_settings():
                app_settings["max_backups"] = int(max_backups_input.value)
                app_settings["retention_days"] = int(retention_days_input.value)
                save_settings(app_settings)
                ui.notify("Settings Saved", type="positive")
                retention_label.set_text(
                    f"Retention: {app_settings['max_backups']} files / {app_settings['retention_days']} days"
                )
                settings_dialog.close()

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=settings_dialog.close).props("flat color=grey")
                save_settings_btn = ui.button("Save", on_click=save_app_settings).props("unelevated").classes("px-4")

    # --- MAIN LAYOUT ---

    with ui.element("div").classes("w-full h-full flex items-center justify-center p-4") as bg_container:
        with ui.column().classes("w-full max-w-2xl gap-6"):
            # HEADER
            with ui.row().classes("w-full justify-between items-center"):
                with ui.row().classes("items-center gap-4"):
                    # LOGO LOGIC
                    logo_path = os.path.join(ASSETS_DIR, "logo.svg")
                    if os.path.exists(logo_path):
                        try:
                            with open(logo_path, "rb") as f:
                                b64_data = base64.b64encode(f.read()).decode("utf-8")
                                src = f"data:image/svg+xml;base64,{b64_data}"
                                # HTML IMG for perfect control
                                ui.element("img").props(f'src="{src}" alt="Logo"').classes(
                                    "h-14 w-auto object-contain object-left max-w-[200px]"
                                )
                        except Exception:
                            ui.icon("dns", size="xl").classes("text-primary")
                    else:
                        ui.icon("dns", size="xl").classes("text-primary")

                    with ui.column().classes("gap-0"):
                        ui.label("Supabase Backup").classes("text-3xl font-bold tracking-tight leading-none")
                        ui.label("Disaster Recovery Manager").classes("text-sm opacity-60 font-medium")

                with (
                    ui.button(icon="contrast", on_click=toggle_theme)
                    .props("round flat unelevated")
                    .classes("text-primary")
                ):
                    pass

            # MAIN CARD
            with ui.card().classes("shadcn-card w-full p-8 no-shadow") as main_card:
                # CONFIG SECTION HEADER
                with ui.row().classes("w-full justify-between items-center mb-2"):
                    ui.label("Project Configuration").classes("font-bold text-lg")
                    ui.button(icon="settings", on_click=settings_dialog.open).props("round flat dense").classes(
                        "text-primary opacity-50 hover:opacity-100"
                    )

                # PROJECT SELECTION UI
                with ui.column().classes("w-full gap-2 mb-4"):
                    ui.label("Select Project Environment").classes("text-sm font-medium opacity-70")

                    env_files = get_env_files()
                    env_dropdown = (
                        ui.select(options=env_files, value=env_files[0] if env_files else None)
                        .props('outlined dense options-dense behavior="menu"')
                        .classes("w-full font-medium")
                    )

                    # ACTION BAR
                    with ui.row().classes("w-full gap-2 mt-1"):
                        create_new_btn = (
                            ui.button("Create New", icon="add", on_click=new_project_dialog.open)
                            .props("unelevated size=sm")
                            .classes("px-3 opacity-90 hover:opacity-100")
                        )
                        ui.button("Edit Config", icon="edit", on_click=open_edit_dialog).props(
                            "outline size=sm color=grey"
                        ).classes("px-3")

                # PERMANENT SWITCH
                with ui.row().classes("items-center justify-between w-full mb-6 mt-2"):
                    with ui.column().classes("gap-0"):
                        ui.label("Permanent Backup").classes("font-medium")
                        ui.label("Protect from auto-deletion").classes("text-xs opacity-60")

                    is_permanent = ui.switch("").props('color=primary keep-color size="lg"')

                ui.separator().classes("mb-6 opacity-20")

                # LOGS
                with ui.row().classes("w-full justify-between items-end mb-2"):
                    ui.label("Execution Log").classes("font-bold text-lg")
                    status_badge = ui.badge("IDLE", color="grey").props("outline rounded")

                log = ui.log().classes("w-full h-56 p-4 text-xs terminal-window terminal-scroll mb-6 shadow-inner")

                # FOOTER
                with ui.row().classes("w-full justify-between items-center"):
                    retention_label = ui.label(
                        f"Retention: {app_settings['max_backups']} files / {app_settings['retention_days']} days"
                    ).classes("text-xs opacity-60 font-medium")

                    with ui.row().classes("items-center gap-4"):
                        spinner = ui.spinner(size="md").classes("text-primary invisible")

                        start_btn = (
                            ui.button("START BACKUP").props("unelevated").classes("px-8 py-2 text-base shadow-sm")
                        )

                        async def run_process():
                            if not env_dropdown.value:
                                ui.notify("Select a project first", type="warning")
                                return

                            start_btn.disable()
                            spinner.set_visibility(True)
                            status_badge.props('color=primary label="RUNNING"')
                            log.clear()
                            log.push(f"🚀 Starting backup: {env_dropdown.value}")

                            # --- PORTABLE EXECUTION LOGIC ---
                            # If running as EXE, call the compiled engine.
                            # If running as script, call the python file.
                            if IS_FROZEN:
                                engine_exe = os.path.join(BASE_DIR, "backup_engine.exe")
                                cmd = f'"{engine_exe}" --env "{env_dropdown.value}" --non-interactive'
                            else:
                                cmd = f'"{sys.executable}" backup.py --env "{env_dropdown.value}" --non-interactive'

                            if is_permanent.value:
                                cmd += " --permanent"

                            process = await asyncio.create_subprocess_shell(
                                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=BASE_DIR
                            )

                            if process.stdout:
                                while True:
                                    line = await process.stdout.readline()
                                    if not line:
                                        break
                                    log.push(line.decode().strip())

                            await process.wait()

                            if process.returncode == 0:
                                ui.notify("Backup Successful", type="positive")
                                status_badge.props('color=positive label="SUCCESS"')
                                log.push("✅ Backup secured.")
                            else:
                                ui.notify("Backup Failed", type="negative")
                                status_badge.props('color=negative label="FAILED"')
                                log.push("❌ Error. Check logs.")

                            start_btn.enable()
                            spinner.set_visibility(False)

                        start_btn.on("click", run_process)

            # --- AUTHOR FOOTER ---
            with ui.row().classes("w-full justify-center"):
                ui.label("Made by Double77 🦁").classes("text-xs opacity-40 font-medium")

    apply_theme()


ui.run(native=True, window_size=(750, 1000), title="Supabase Backup Manager", port=8081, reload=False)
