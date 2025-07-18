import json

def get_threatconnect_config(config_path):
    """Extract ThreatConnect configuration."""
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        tc_config = config.get("threatconnect", {}).get("credentials", {})
        return {
            "secret_key": tc_config["secret_key"],
            "access_id": tc_config["access_id"],
            "base_url": tc_config["base_url"],
            "default_org": tc_config["default_org"]
        }
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file not found: {config_path}")
    except KeyError as e:
        raise RuntimeError(f"Missing key in ThreatConnect config: {e}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Error decoding JSON in ThreatConnect config: {e}")


