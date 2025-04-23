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
        api_secret_key = config.get('api_secret_key')
        api_access_id = config.get('api_access_id')
        api_base_url = config.get('api_base_url')
        api_default_org = config.get('api_default_org')


        if not all([api_secret_key, api_access_id, api_base_url, api_default_org]):
            raise KeyError("One or more required keys ('api_secret_key', 'api_access_id', 'api_base_url', 'api_default_org') are missing or have null values in the config file.")

    except KeyError as e:
        raise KeyError(f"Missing key in config.json: {e}")

    return api_secret_key, api_access_id, api_base_url, api_default_org
