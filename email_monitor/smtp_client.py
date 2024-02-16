import os
from email.header import Header
from email.utils import formataddr
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from email_monitor.console import console


class SMTPClient:
    def __init__(
        self, smtp_server: str, smtp_port: int, username: str, password: str = None
    ):
        """Generate an SMTP Client

        Args:
            smtp_server (str): Smtp Server to connect to
            smtp_port (int): Server port
            username (str): Authentication username
            password (str): Authentication password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_html_email(
        self, to_address: str, subject: str, html_text: str, csv_text: str
    ):
        """Sends an embedded HTML email using the SMTP Client

        Args:
            to_address (str): Address to write to
            subject   (str): Email's Subject
            html_text (str): Email's message in html
            csv_text  (str): Email's backup plaintext
        """
        try:
            msg = MIMEMultipart(
                "alternative", None, [MIMEText(csv_text), MIMEText(html_text, "html")]
            )

            msg["From"] = formataddr(
                (str(Header("Compfarm Monitor", "utf-8")), f"{self.username}")
            )
            msg["To"] = to_address
            msg["Subject"] = subject

            # Establish a connection to the SMTP server
            server = smtplib.SMTP(
                host=self.smtp_server, port=self.smtp_port, timeout=10
            )
            server.starttls()  # Upgrade the connection to a secure SSL connection

            if self.password:
                server.login(self.username, self.password)  # Login to the SMTP server

            # Send the email
            server.sendmail(self.username, to_address, msg.as_string())

            # Close the connection
            server.quit()

            console.print(f"Email sent to {to_address} successfully!")
        except Exception:
            console.log_error("Failed to send email")
            console.print_exception()

    def send_email(self, to_address: str, subject: str, message: str):
        """Sends an email using the SMTP Client

        Args:
            to_address (str): Address to write to
            subject (str): Email's Subject
            message (str): Email's message
        """
        try:
            # Create a MIMEText object to represent the email
            msg = MIMEMultipart()
            msg["From"] = formataddr(
                (str(Header("Compfarm Monitor", "utf-8")), f"{self.username}")
            )
            msg["To"] = to_address
            msg["Subject"] = subject

            # Attach the message to the email
            msg.attach(MIMEText(message, "plain"))

            # Establish a connection to the SMTP server
            server = smtplib.SMTP(
                host=self.smtp_server, port=self.smtp_port, timeout=10
            )
            server.starttls()  # Upgrade the connection to a secure SSL connection

            if self.password:
                server.login(self.username, self.password)  # Login to the SMTP server

            # Send the email
            server.sendmail(self.username, to_address, msg.as_string())

            # Close the connection
            server.quit()

            console.print("Email sent successfully!")
        except Exception:
            console.log_error("Failed to send email")
            console.print_exception()
