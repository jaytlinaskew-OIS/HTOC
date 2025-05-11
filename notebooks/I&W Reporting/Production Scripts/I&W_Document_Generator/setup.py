# src/setup.py

import os
import sys
import urllib3
from ThreatConnect import ThreatConnect
from RequestObject import RequestObject
from src.config import CONFIG_PATH, VERIFY_SSL
from utils.config_loader import load_config
from src.logging_config import get_logger

logger = get_logger(__name__)

# Disable SSL warnings
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def initialize_threatconnect():
    """ Initialize the ThreatConnect session. """
    try:
        api_secret_key, api_access_id, api_base_url, api_default_org = load_config(CONFIG_PATH)
        logger.info(f"Loaded configuration from {CONFIG_PATH}")
        
        # Initialize ThreatConnect instance
        tc = ThreatConnect(api_access_id, api_secret_key, api_default_org, api_base_url)
        logger.info("ThreatConnect initialized successfully.")
        return tc

    except Exception as e:
        logger.error(f"Failed to initialize ThreatConnect: {e}")
        sys.exit(1)

def create_request_object(owner):
    """ Create and configure a RequestObject for ThreatConnect requests. """
    try:
        ro = RequestObject()
        ro.set_http_method('GET')
        ro.set_owner(owner)
        ro.set_owner_allowed(True)
        logger.info("RequestObject created successfully.")
        return ro

    except Exception as e:
        logger.error(f"Failed to create RequestObject: {e}")
        sys.exit(1)
