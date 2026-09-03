import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "configs" / "configs.json"

# Loads the configuration from the configs.json file.
def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

# Retrieves the alert data path from the configuration.
def get_alert_data(config) -> dict:
    return config["alert"]

# Retrieves the data paths for logs, github and metrics for a specific scenario from the configuration.
def get_data(config, scenario_name: str) -> Path:
    for scenario in config["scenarios"]:
        if scenario["name"] == scenario_name:
            return scenario

    raise ValueError(f"Scenario not found: {scenario_name}")

# Retrieves the model name from the configuration.
def get_model(config) -> dict:
    return config["model"]["name"] 