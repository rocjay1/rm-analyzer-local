"""Functions for sending an email using Gmail and OAuth2."""

# Standard library imports

import os
import base64
import logging
from email.message import EmailMessage
from typing import Optional, Any, Callable

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import rm_analyzer_local

# If modifying these scopes, delete the file token.json
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]



def gmail_send_message(
    destination: str,
    subject: str,
    html: str,
    service_factory: Optional[Callable[[Any], Any]] = None,
) -> Optional[Any]:
    """Create and send an email message.

    Args:
        destination: Recipient email address.
        subject: Email subject.
        html: Email body as HTML.
        service_factory: Optional function to create the Gmail API service (for testing/mocking).
    Returns:
        The sent message object, or None if sending failed.
    """
    creds = None
    token_path = os.path.join(rm_analyzer_local.CONFIG_DIR, "token.json")
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        new_app_flow = True

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                new_app_flow = False
            except RefreshError:
                # Google Cloud "Testing" apps's refresh tokens expire in 7 days
                os.remove(token_path)

        if new_app_flow:
            flow = InstalledAppFlow.from_client_config(rm_analyzer_local.get_creds(), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    try:
        if service_factory:
            service = service_factory(creds)
        else:
            service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()
        message.set_content(html, subtype="html")
        message["To"] = destination
        message["Subject"] = subject

        # Encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        send_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )

        logging.info('Message Id: %s', send_message["id"])
    except HttpError as error:
        logging.error('An error occurred: %s', error)
        send_message = None

    return send_message
