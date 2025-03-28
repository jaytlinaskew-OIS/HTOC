import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CSVFileHandler(FileSystemEventHandler):
    def __init__(self, raw_dir, json_path):
        """
        Initialize the file handler.

        Args:
            raw_dir (str): Path to the raw data directory.
            json_path (str): Path to the JSON file to store file paths.
        """
        self.raw_dir = raw_dir
        self.json_path = json_path

    def on_created(self, event):
        """
        Triggered when a new file is created in the directory.

        Args:
            event: The file system event.
        """
        if event.is_directory:
            return

        # Check if the new file is a CSV
        if event.src_path.endswith(".csv"):
            print(f"New CSV file detected: {event.src_path}")
            self.update_json(event.src_path)

    def update_json(self, file_path):
        """
        Update the JSON file with the new file path.

        Args:
            file_path (str): Path to the new CSV file.
        """
        # Load existing data from the JSON file
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r") as json_file:
                    data = json.load(json_file)
            except json.JSONDecodeError:
                # Handle empty or corrupted JSON file
                data = []
        else:
            data = []

        # Add the new file path if it's not already in the JSON
        relative_path = os.path.relpath(file_path, start=self.raw_dir)
        if relative_path not in data:
            data.append(relative_path)

            # Save the updated data back to the JSON file
            with open(self.json_path, "w") as json_file:
                json.dump(data, json_file, indent=4)
            print(f"File path added to JSON: {relative_path}")

def monitor_directory(raw_dir, json_path):
    """
    Monitor the raw data directory for new CSV files.

    Args:
        raw_dir (str): Path to the raw data directory.
        json_path (str): Path to the JSON file to store file paths.
    """
    event_handler = CSVFileHandler(raw_dir, json_path)
    observer = Observer()
    observer.schedule(event_handler, path=raw_dir, recursive=False)
    observer.start()
    print(f"Monitoring directory: {raw_dir}")

    try:
        while True:
            pass  # Keep the script running
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    # Define paths relative to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(script_dir, "/Users/jaytlinaskew/GitRepository/TimeSeries-Analysis/data/raw")
    json_path = os.path.join(script_dir, "/Users/jaytlinaskew/GitRepository/TimeSeries-Analysis/data/data_path.json")

    # Ensure the raw directory exists
    os.makedirs(raw_dir, exist_ok=True)

    # Start monitoring the directory
    monitor_directory(raw_dir, json_path)
    
    
    # python monitor_raw_directory.py