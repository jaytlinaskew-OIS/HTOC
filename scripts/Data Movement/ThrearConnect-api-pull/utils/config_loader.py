import json
import os

def load_config(config_file):
    # Get absolute path to ensure correct file resolution
    config_path = os.path.abspath(config_file)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as file:
        config = json.load(file)

    # Safely get each field, raise if missing
    try:
        api_key = config.get('api_key')
        access_id = config.get('access_id')
        url_base = config.get('url_base')

        if not all([api_key, access_id, url_base]):
            raise KeyError("One or more required keys ('api_key', 'access_id', 'url_base') are missing or have null values in the config file.")

    except KeyError as e:
        raise KeyError(f"Missing key in config.json: {e}")

    return api_key, access_id, url_base
