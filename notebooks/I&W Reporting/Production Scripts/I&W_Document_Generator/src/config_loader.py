# utils/config_loader.py

import json
import os

def load_config(config_path):
    """ Load the configuration file. """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as file:
        config = json.load(file)
    
    api_secret_key = config.get("api_secret_key")
    api_access_id = config.get("api_access_id")
    api_base_url = config.get("api_base_url")
    api_default_org = config.get("api_default_org")
    
    if not all([api_secret_key, api_access_id, api_base_url, api_default_org]):
        raise ValueError("One or more configuration parameters are missing.")
    
    return api_secret_key, api_access_id, api_base_url, api_default_org
