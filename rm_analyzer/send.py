"""Functions for sending an email using Gmail and OAuth2."""

# Standard library imports
import os
import base64
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import rm_analyzer

# If modifying these scopes, delete the file token.json
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def gmail_send_message(destination, subject, html):
    """Create and send an email message."""
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    #   created automatically when the authorization flow completes for the first
    #   time
    token_path = os.path.join(rm_analyzer.CONFIG_DIR, "token.json")
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
            flow = InstalledAppFlow.from_client_config(rm_analyzer.CREDS, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        # pylint: disable=unspecified-encoding
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()
        message.set_content(html, subtype="html")
        message["To"] = destination
        message["Subject"] = subject

        # Encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        # pylint: disable=E1101
        send_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )

        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None

    return send_message
