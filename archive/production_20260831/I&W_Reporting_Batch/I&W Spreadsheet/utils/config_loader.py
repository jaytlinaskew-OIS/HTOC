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

def get_virustotal_config(config_path):
    """Extract VirusTotal configuration."""
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        vt_config = config.get("virustotal", {})
        return {
            "api_key": vt_config["api_key"],
            "endpoints": vt_config["endpoints"]
        }
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file not found: {config_path}")
    except KeyError as e:
        raise RuntimeError(f"Missing key in VirusTotal config: {e}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Error decoding JSON in VirusTotal config: {e}")

def get_AlienVaultOtx_config(config_path):
    """Extract OTX configuration."""
    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        otx_config = config.get("otx", {})
        return {
            "api_key": otx_config["api_key"],
            "endpoints": otx_config["endpoints"]
        }
    except FileNotFoundError:
        raise RuntimeError(f"Configuration file not found: {config_path}")
    except KeyError as e:
        raise RuntimeError(f"Missing key in OTX config: {e}")
    except json.JSONDecodeError:
        raise RuntimeError(f"Error decoding JSON in OTX config: {e}")

