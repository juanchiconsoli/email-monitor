import json
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel, EmailStr
from rich.table import Table
from email_monitor.conifg import Config

from email_monitor.console import console


class Client(BaseModel):
    name: str
    email: EmailStr


class ClientService:
    def __init__(self, config: Config) -> None:
        self.config = config

    def get_all(self) -> List[Client]:
        clients = []

        clients_config = self.config.get_clients()

        for clien_dict in clients_config:
            clients.append(Client(**clien_dict))

        return clients

    def get_client_table(self) -> Table:
        rows = []

        clients = self.get_all()

        for client in clients:
            rows.append((client.name, client.email))

        table = console.build_table(
            title="Clients",
            header=[
                "Client",
                "Email",
            ],
            rows=rows,
        )

        return table
