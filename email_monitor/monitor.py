from datetime import datetime
from typing import Dict, List, Union
from pydantic import BaseModel
import imaplib
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from email.header import decode_header

from email_monitor.conifg import PASS_KEYWORDS, WARNING_KEYWORDS, InvalidConfig
from email_monitor.console import console
from email_monitor.clients import ClientService


class EmailBackup(BaseModel):
    subject: str
    sender: str
    date: Union[datetime, str]

    def get_row(self):
        return (
            self.sender,
            self.subject,
            self.date.strftime("%A, %d %B %Y %I:%M %p"),
        )

    def has_passed(self, pass_keywords: List[str] = None) -> bool:

        if pass_keywords is None:
            pass_keywords = PASS_KEYWORDS

        return any(pass_key in self.subject.lower() for pass_key in pass_keywords)

    def get_status(self):

        if any(pass_key in self.subject.lower() for pass_key in PASS_KEYWORDS):
            return "success"
        elif any(pass_key in self.subject.lower() for pass_key in WARNING_KEYWORDS):
            return "warning"
        else:
            return "failure"


class EmailClient:
    def __init__(
        self, email: str, password: str, server: str = "ssl0.ovh.net", port: int = 993
    ):
        self.server = server
        self.port = port
        self.email = email
        self.password = password
        self.mail = None

    @classmethod
    def from_config(cls, config: Dict[str, Union[str, int]]):
        try:

            return EmailClient(
                email=config["email"],
                password=config["password"],
                server=config["server"],
            )
        except KeyError as ex:
            raise InvalidConfig("La configuration du serveur de mail est incorrecte")

    def connect(self):
        self.mail = imaplib.IMAP4_SSL(self.server, self.port, timeout=15)
        self.mail.login(self.email, self.password)

    def select_mailbox(self, mailbox="INBOX"):
        if not self.mail:
            raise Exception("You need to connect first")
        self.mail.select(mailbox)

    def search_emails(self, criteria="ALL"):
        if not self.mail:
            raise Exception("You need to connect first")
        return self.mail.search(None, criteria)

    def fetch_email(self, email_id):
        if not self.mail:
            raise Exception("You need to connect first")
        _, data = self.mail.fetch(email_id, "(RFC822)")
        return data[0][1]

    def get_all_emails(
        self, imap_query="ALL", criteria: str = "sauvegarde"
    ) -> List[EmailBackup]:
        if not self.mail:
            raise Exception("You need to connect first")

        email_subjects = []

        email_ids = self.search_emails(criteria=imap_query)

        for email_id in email_ids[1][0].split():

            try:
                raw_email_data = self.fetch_email(email_id)
                msg = message_from_bytes(raw_email_data)
                subject = self.decode_part(msg.get("Subject"))
                sender = self.decode_part(msg.get("From"))

                date = parsedate_to_datetime(msg.get("Date"))

                if subject:
                    if criteria in subject.lower():
                        email_subjects.append(
                            EmailBackup(subject=subject, sender=sender, date=date)
                        )
            except ValueError as ex:
                console.log_warning(ex)
                console.log_warning(f"Skipping email {subject}")

        return email_subjects

    def decode_part(self, subject):
        decoded_subject = []
        for part, encoding in decode_header(subject):
            if isinstance(part, bytes):
                # Decode bytes to string
                if encoding:
                    part = part.decode(encoding)
                else:
                    part = part.decode()
            decoded_subject.append(part)
        return "".join(decoded_subject)

    def logout(self):
        if self.mail:
            self.mail.logout()
            self.mail = None


class Monitor:
    def __init__(
        self, client_service: ClientService, email_client: EmailClient
    ) -> None:
        self.clients = client_service.get_all()
        self.email_client = email_client

    def get_backups(self, date: datetime):

        emails = self.email_client.get_all_emails(self.get_date_imap_query(date))

        emails.sort(key=lambda obj: obj.date)

        if date:
            emails = [e for e in emails if e.date.date() == date.date()]

        result_dict = {
            key: [item for item in emails if key in item.subject]
            for key in self._client_names
        }

        return result_dict

    @property
    def _client_names(self):
        return [c.name for c in self.clients]

    @staticmethod
    def get_date_imap_query(date: datetime) -> str:
        date_str = date.strftime("%d-%b-%Y")
        return f'(SENTON "{date_str}")'
