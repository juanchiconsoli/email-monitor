from typing import Dict, List
from datetime import datetime
from pathlib import Path
import typer
from email_monitor.clients import ClientService
from email_monitor.console import console
from email_monitor.conifg import Config, InvalidConfig
from email_monitor.monitor import EmailBackup, EmailClient, Monitor

app = typer.Typer(rich_markup_mode="rich")

app_config = Config()


@app.command("clients")
def receive(
    config: Path = typer.Option(
        None, help="Racine du fichier de configuration alternatif"
    )
):
    """Afficher la list de client dans le fichier de configuration"""
    try:
        if config:
            app_config.set_config_file(config)

        client_service = ClientService(app_config)

        table = client_service.get_client_table()

        console.print(table)

    except FileNotFoundError as ex:
        console.log_warning(ex)

    except ValueError:
        console.log_warning("The configuration file was wrongly formatted")


@app.command("emails")
def get_emails(
    config: Path = typer.Option(
        None, help="Racine du fichier de configuration alternatif"
    )
):
    """Afficher tous les emails de sauvegarde"""

    try:
        if config:
            app_config.set_config_file(config)

        client = EmailClient.from_config(app_config.get_email_config())
        client.connect()
        client.select_mailbox()

        emails = client.get_all_emails()

        client.logout()

        table = console.build_table(
            title="Emails",
            header=["Sender", "Subject", "Date"],
            rows=[e.get_row() for e in emails],
        )

        console.print(table)
    except Exception as ex:
        console.log_warning(ex)


@app.command("backups")
def sauvegardes(
    config: Path = typer.Option(
        None, help="Racine du fichier de configuration alternatif"
    ),
    date: str = typer.Argument(None, help="Date des sauvegardes: dd-mm-yyyy"),
):
    """Afficher la table des clients et sauvegardes"""
    try:

        client = EmailClient.from_config(app_config.get_email_config())
        client.connect()
        client.select_mailbox()

        if config:
            app_config.set_config_file(config)

        if not date:
            date = datetime.now()
        else:
            date = datetime.strptime(date, "%d-%m-%Y")

        client_service = ClientService(app_config)

        monitor = Monitor(client_service, email_client=client)

        results = monitor.get_backups(date)

        table = build_results_table(results)

        console.print(table)

    except FileNotFoundError as ex:
        console.log_warning(ex)

    except ValueError as ex:
        console.log_warning("Invalid date format")

    except InvalidConfig:
        console.log_warning("The configuration file was wrongly formatted")


def build_results_table(results: Dict[str, List[EmailBackup]]):

    rows = []

    for client in results.keys():

        try:
            last_email: EmailBackup = results[client][-1]

            if last_email.has_passed():
                last_email.subject = (
                    "[bold green]" + last_email.subject + "[/bold green]"
                )
                status = ":thumbs_up:"
            else:
                last_email.subject = "[bold red]" + last_email.subject + "[/bold red]"
                status = ":warning:"

            rows.append(
                (
                    client,
                    last_email.subject,
                    last_email.date.strftime("%A, %d %B %Y %I:%M %p"),
                    status,
                )
            )
        except IndexError:
            rows.append(
                (
                    client,
                    "",
                    "[bold red]Missing[/bold red]",
                    ":warning:",
                )
            )

    return console.build_table(
        title="Sauvegardes", header=["Client", "Email", "Date", "Status"], rows=rows
    )


if __name__ == "__main__":
    get_emails()
