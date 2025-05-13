def load_config(config_path):
    """Load API configuration from a JSON file."""
    import json

    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
            api_secret_key = config.get('api_secret_key')
            api_access_id = config.get('api_access_id')
            api_base_url = config.get('api_base_url')
            api_default_org = config.get('api_default_org')
            return api_secret_key, api_access_id, api_base_url, api_default_org
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")