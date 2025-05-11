#RAW_DATA_DIR = os.path.join(os.getcwd(), "notebooks","I&W Reporting", "Production Scripts", "I&W_Document_Generator","data","raw")

# src/config.py

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directory Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UTILS_DIR = os.path.join(BASE_DIR, "utils")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MODEL_DIR = os.path.join(BASE_DIR, "models")

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuration File Path
CONFIG_PATH = os.path.join(UTILS_DIR, "config.json")

# SSL Verification (set to False for development, True for production)
VERIFY_SSL = False
