import schedule
import time
import subprocess
from datetime import datetime

def run_batch_script():
    batch_file = r"Z:\HTOC\Data_Analytics\Data\OpDiv_Predictions\automation scripts\NextObserved - Copy.bat"
    try:
        subprocess.run(batch_file, check=True)
        print(f"{datetime.now()}: Batch script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"{datetime.now()}: Error executing batch script: {e}")

# Schedule the job every day at 8:00 AM
schedule.every().day.at("08:00").do(run_batch_script)

if __name__ == "__main__":
    print("Scheduler started. Waiting for 8:00 AM daily execution...")
    while True:
        schedule.run_pending()
        time.sleep(60)