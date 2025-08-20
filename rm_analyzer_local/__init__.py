"""Initialize rm_analyzer_local."""

# Standard library imports
from importlib import resources
import os
import json


def get_creds():
    """Load the OAuth2 credentials.json file."""
    return json.loads(
        resources.files("rm_analyzer_local")
        .joinpath("credentials.json")
        .read_text(encoding="UTF-8")
    )

def get_config():
    """Load the config.json file from the user's config directory."""
    config_dir = os.path.join(os.path.expanduser("~"), ".rma")
    config_file = os.path.join(config_dir, "config.json")
    if not os.path.exists(config_file):
        raise FileExistsError(f"Config file does not exist: {config_file}")
    with open(config_file, encoding="UTF-8") as f:
        return json.load(f)

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".rma")
