import sys
from typing import Dict, List
from datetime import datetime
from pathlib import Path
import typer
from email_monitor.clients import ClientService
from email_monitor.console import console
from email_monitor.conifg import Config, InvalidConfig
from email_monitor.monitor import EmailBackup, EmailClient, Monitor
from email_monitor.smtp_client import SMTPClient

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

        results = _get_backup_results(config, date)

        table = _build_results_table(results)

        console.print(table)

    except FileNotFoundError as ex:
        console.log_warning(ex)

    except ValueError as ex:
        console.log_warning("Invalid date format")

    except InvalidConfig:
        console.log_warning("The configuration file was wrongly formatted")


@app.command("send-report")
def report(
    config: Path = typer.Option(
        None, help="Racine du fichier de configuration alternatif"
    ),
    to_address: str = typer.Option(
        ..., "--to_address", "-t", help="Address to write to"
    ),
    subject: str = typer.Option(..., "--subject", "-s", help="Email's subject"),
    date: str = typer.Argument(None, help="Date des sauvegardes: dd-mm-yyyy"),
):
    console.print(f"Sending email to {to_address}...")

    try:

        results = _get_backup_results(config, date)

        html_table = _build_html_results_table(results)

        if config:
            app_config.set_config_file(config)

        client_config = app_config.get_email_config()

        console.print(client_config)

        smtp_client = SMTPClient(
            username=client_config["email"],
            password=client_config["password"],
            smtp_server=client_config["server"],
            smtp_port=465,
        )

        smtp_client.send_html_email(
            to_address=to_address, subject=subject, html_text=html_table, csv_text=""
        )

    except FileNotFoundError as ex:
        console.log_warning(ex)
    except ValueError as ex:
        console.log_warning("Invalid date format")
    except InvalidConfig:
        console.log_warning("The configuration file was wrongly formatted")
    except Exception as ex:
        console.log_error("Couldn't send message")
        console.log_error(ex)
        sys.exit(42)


def _get_backup_results(config: Path, date: str) -> Dict[str, List[EmailBackup]]:
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

    return results


def _build_results_table(results: Dict[str, List[EmailBackup]]):

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


def _build_html_results_table(results: Dict[str, List[EmailBackup]]) -> str:

    head = """<head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Rapport des Sauvegardes</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                    }
                    h1 {
                        text-align: center;
                        margin-top: 20px;
                    }
                    table {
                        width: 80%;
                        border-collapse: collapse;
                        margin: 20px auto;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }
                    th {
                        background-color: #f2f2f2;
                    }
                    tr:nth-child(even) {
                        background-color: #f2f2f2;
                    }
                    tr:hover {
                        background-color: #ddd;
                    }
                </style>
            </head>"""

    report_html = f"<html>{head}<body><h1>Rapport des Sauvegardes</h1><br><br>"

    report_html = (
        report_html
        + "<table><thead><tr><th>Client</th><th>Email</th><th>Date</th><th>Status</th></tr></thead><tbody>"
    )

    for client in results.keys():

        try:
            last_email: EmailBackup = results[client][-1]

            if last_email.has_passed():
                status = "Success"
            else:
                status = "Failure"

            report_html += f'<tr><td>{client}</td><td>{last_email.subject}</td><td>{last_email.date.strftime("%A, %d %B %Y %I:%M %p")}</td><td>{status}</td>'

        except IndexError:

            report_html += (
                f"<tr><td>{client}</td><td>-</td><td>Missing</td><td>Failure</td>"
            )

    report_html = report_html + "</tbody></table></body></html>"

    return report_html


if __name__ == "__main__":
    get_emails()
