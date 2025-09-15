import schedule
import subprocess
import time
import logging
from datetime import datetime

# Configure logging
log_file = r"C:\Users\jaskew\Documents\project_repository\scripts\Data Movement\ThrearConnect-api-pull\utils\Scheduled Tasks\logs\alynforensics.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Function to run the Python script
def run_file():
    try:
        file_path = r"C:\Users\jaskew\Documents\project_repository\scripts\Data Movement\ThrearConnect-api-pull\utils\Scheduled Tasks\alynforensics.py"
        command = ["python", file_path]
        logging.info(f"Executing: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("Script executed successfully.")
            logging.info(f"Output: {result.stdout}")
        else:
            logging.error("Script execution failed.")
            logging.error(f"Error: {result.stderr}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Function to check if the current time is within the allowed time frame
def run_within_timeframe():
    logging.info("Starting script execution...")
    current_time = datetime.now().time()
    start_time = datetime.strptime("07:00", "%H:%M").time()
    end_time = datetime.strptime("15:00", "%H:%M").time()
    if start_time <= current_time <= end_time:
        run_file()
        logging.info("Script execution completed.")
    else:
        logging.info("Current time is outside the allowed time frame (7 AM to 3 PM).")

# Schedule the task every 10 minutes
schedule.every(10).minutes.do(run_within_timeframe)

try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    logging.info("Scheduler stopped.")