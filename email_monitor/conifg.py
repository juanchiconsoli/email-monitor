import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List

from email_monitor.console import console


PASS_KEYWORDS = ["success", "succès", "reusit"]


class InvalidConfig(Exception): ...


class Config:

    def __init__(self) -> None:
        self._config_file = Path(
            os.environ.get("EMAIL_MONITOR_CONFIG", "./clients.json")
        ).resolve()

        self.validate()

    def set_config_file(self, config_file: Path) -> None:
        self._config_file = config_file

    def get_config_file(self):
        if self._config_file.exists():
            return self._config_file
        else:
            raise FileNotFoundError

    def get_clients(self) -> List[Dict[str, Any]]:

        config_json = self._read_config()

        return config_json["clients"]

    def get_email_config(self) -> Dict[str, Any]:

        config_json = self._read_config()

        return config_json["email"]

    def _read_config(self) -> Dict[str, Any]:
        with open(self._config_file, mode="r", encoding="utf-8") as config:
            return json.load(config)

    def get_pass_keywords(self) -> List[str]:
        return PASS_KEYWORDS

    def validate(self):
        try:

            email = self.get_email_config()

            if ["server", "email", "password"] != list(email.keys()):
                raise InvalidConfig

            clients = self.get_clients()

            for client in clients:
                if ["name", "email"] != list(client.keys()):
                    raise InvalidConfig

        except InvalidConfig:
            console.log_warning("Invalid configuration")
            sys.exit(42)
        except FileNotFoundError:
            console.log_error(f"Configuration {self._config_file} missing")
            sys.exit(42)
