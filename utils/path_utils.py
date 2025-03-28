import sys
import json

def add_src_path_from_config(config_file):
    """
    Load the source path from a JSON config file and add it to sys.path.

    Args:
        config_file (str): Path to the JSON configuration file.

    Returns:
        None
    """
    with open(config_file, 'r') as file:
        config = json.load(file)
        src_path = config.get("src_path")
        if src_path and src_path not in sys.path:
            sys.path.append(src_path)