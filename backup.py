
import os
import platform
import subprocess
import inquirer
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse

def install_dependencies():
    """Install dependencies from requirements.txt."""
    try:
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        exit(1)

def main():
    # Display ASCII art and welcome message.
    # Clear the console for a cleaner interface.
    os.system('cls' if os.name == 'nt' else 'clear')

    """Main function to run the backup CLI."""
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

    # Check if dependencies are installed
    questions = [
        inquirer.Confirm('installed',
                          message="Have you installed the required dependencies (listed in requirements.txt)?",
                          default=True)
    ]
    answers = inquirer.prompt(questions) # type: ignore

    if answers: # Check if answers is not None
        if not answers.get('installed'): # Use .get() for safer access
            print("Installing dependencies...")
            install_dependencies()

    # Find all .env files in the current directory
    env_files = [f for f in os.listdir('.') if f.endswith('.env')]
    if not env_files:
        print("Error: No .env files found in the current directory.")
        exit(1)

    # Let the user choose which .env file to use
    questions = [
        inquirer.List('env_file',
                      message="Please select the .env file for the project you want to back up",
                      choices=env_files,
                      )
    ]
    answers = inquirer.prompt(questions)
    if answers: # Check if answers is not None
        selected_env_file = answers['env_file']
    else:
        exit(1)  # Exit if no .env file is selected or prompt is cancelled

    # Ask for the backup file name
    default_backup_name = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.sql"
    questions = [
        inquirer.Text('backup_file', 
                      message="Enter the name for the backup file",
                      default=default_backup_name)
    ]
    answers = inquirer.prompt(questions)
    if answers:
        backup_file_name = answers['backup_file']
    else:
        backup_file_name = default_backup_name

    # Create backups directory if it doesn't exist
    if not os.path.exists('backups'):
        os.makedirs('backups')
    
    backup_file = os.path.join('backups', backup_file_name)
 
    # Load environment variables from the selected .env file
    load_dotenv(dotenv_path=selected_env_file)

    # Get Supabase credentials from environment variables
    supabase_db_uri = os.getenv("SUPABASE_DB_URI")
    supabase_url = os.getenv("SUPABASE_URL")
    db_password = os.getenv("DB_PASSWORD")

    # Backup file name
    backup_file = "backup.sql"

    # Determine the command based on the OS
    pg_dump_command = "pg_dump.exe" if platform.system() == "Windows" else "pg_dump"

    command = []
    # Set the PGPASSWORD environment variable for the subprocess
    env = os.environ.copy()

    # Prioritize SUPABASE_DB_URI if it exists
    if supabase_db_uri:
        print("Using SUPABASE_DB_URI for connection.")
        command = [
            pg_dump_command,
            "--dbname", supabase_db_uri,
            "-f", backup_file,
            "--no-password"
        ]
    else:
        print("SUPABASE_DB_URI not found, falling back to SUPABASE_URL and DB_PASSWORD.")
        if not supabase_url or not db_password:
            print("Error: When SUPABASE_DB_URI is not set, both SUPABASE_URL and DB_PASSWORD must be set in the .env file.")
            print("Please add the following to your .env file:")
            print("SUPABASE_URL=https://your-project-ref.supabase.co")
            print("DB_PASSWORD=your-database-password")
            print("Alternatively, provide the full SUPABASE_DB_URI.")
            exit(1)

        # Extract project reference from Supabase URL
        try:
            parsed_url = urlparse(supabase_url)
            if not parsed_url.hostname:
                raise ValueError("Invalid Supabase URL: Hostname not found.")
            project_ref = parsed_url.hostname.split('.')[0]
            db_host = f"db.{project_ref}.supabase.co"
        except (AttributeError, IndexError, ValueError) as e:
            print(f"Error: Could not parse SUPABASE_URL: {supabase_url}")
            print(f"Details: {e}")
            print("Please make sure it is in the format: https://your-project-ref.supabase.co")
            exit(1)

        print(f"Attempting to connect to host: {db_host}")

        # Check DNS resolution
        try:
            import socket
            ip_address = socket.gethostbyname(db_host)
            print(f"Successfully resolved {db_host} to {ip_address}")
        except socket.gaierror:
            print(f"Error: Could not resolve hostname: {db_host}")
            print("This might be due to a few reasons:")
            print("1. The project reference ID in your SUPABASE_URL might be incorrect. Please double-check it in your .env file.")
            print("2. You might have a network issue preventing DNS resolution.")
            print(f"Your current SUPABASE_URL is: {supabase_url}")
            exit(1)

        # Database connection details
        db_user = "postgres"
        db_name = "postgres"
        db_port = 5432

        # Construct the pg_dump command
        # The password will be passed via the PGPASSWORD environment variable
        command = [
            pg_dump_command,
            "-h", db_host,
            "-p", str(db_port),
            "-U", db_user,
            "-d", db_name,
            "-f", backup_file,
            "--no-password" # To prevent password prompt
        ]
        env["PGPASSWORD"] = db_password

    print(f"Starting database backup to {backup_file}...")

    try:
        # Execute the pg_dump command
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
        print("Backup completed successfully.")
        print(f"Backup file created at: {os.path.abspath(backup_file)}")

    except FileNotFoundError:
        print(f"Error: {pg_dump_command} command not found.")
        print("Please make sure PostgreSQL client tools are installed and in your system's PATH.")
        exit(1)
    except subprocess.CalledProcessError as e:
        print("Error during backup:")
        print(e.stderr)
        exit(1)

if __name__ == "__main__":
    main()
