import os
import json
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    def __init__(self):
        self.JSONCONFIG_PATH = self._load_json_config()

    def _load_json_config(self):
        """Load JSON configuration from file path"""
        json_path = os.getenv("JSONPATH", "rat/databases.json")

        # Handle relative paths
        if not os.path.isabs(json_path):
            # Get the directory where this config.py file is located
            base_dir = Path(__file__).parent.parent
            json_path = base_dir / json_path

        try:
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    return json.load(f)
            else:
                print(f"⚠️ JSON config file not found: {json_path}")
                return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON config: {e}")
            return []
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return []

config = Config()