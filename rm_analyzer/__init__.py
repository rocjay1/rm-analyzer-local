"""Initialize rm_analyzer."""

# Standard library imports
from importlib import resources
import os
import json

# Load the OAuth2 credentials.json file
CREDS = json.loads(
    resources.files("rm_analyzer")
    .joinpath("credentials.json")
    .read_text(encoding="UTF-8")
)

# Make sure the config file has been created
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".rma")
_config_file = os.path.join(CONFIG_DIR, "config.json")
if not os.path.exists(_config_file):
    raise FileExistsError(f"Config file does not exist: {_config_file}")
with open(_config_file, encoding="UTF-8") as f:
    CONFIG = json.load(f)
