import json
import os

def load_config(config_file):
    """Read ThreatConnect API credentials from a JSON file.

    Args:
        config_file (str): path to a JSON configuration file.

    Returns:
        tuple: (api_secret_key, api_access_id, api_base_url, api_default_org)

    Raises:
        FileNotFoundError: if the config file doesn't exist.
        KeyError: if required keys are missing.
    """
    config_path = os.path.abspath(config_file)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as fh:
        config = json.load(fh)

    try:
        api_secret_key = config.get('api_secret_key')
        api_access_id = config.get('api_access_id')
        api_base_url = config.get('api_base_url')
        api_default_org = config.get('api_default_org')

        if not all([api_secret_key, api_access_id, api_base_url, api_default_org]):
            raise KeyError(
                "One or more required keys ('api_secret_key', 'api_access_id', "
                "'api_base_url', 'api_default_org') are missing or empty."
            )
    except KeyError as e:
        raise KeyError(f"Missing key in config.json: {e}")

    return api_secret_key, api_access_id, api_base_url, api_default_org
