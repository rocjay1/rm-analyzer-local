"""Azure Function entrypoint triggered by a blob upload."""

# Standard library imports
import json
import logging
import os
import pathlib
import sys
import tempfile
from typing import List, Optional

# Third-party imports
import azure.functions as func
from azure.communication.email import EmailClient


def _ensure_repo_root_on_path() -> None:
    """Add the project root (containing rm_analyzer_local) to sys.path."""
    module_path = pathlib.Path(__file__).resolve()
    for candidate in (module_path.parent,) + tuple(module_path.parents):
        if (candidate / "rm_analyzer_local").is_dir():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            return
    logging.warning(
        "rm_analyzer_local package directory not found adjacent to function app."
    )


_ensure_repo_root_on_path()

from rm_analyzer_local import summarize  # pylint: disable=wrong-import-position


def _load_config() -> dict:
    raw_config = os.getenv("CONFIG_JSON", "")
    if not raw_config:
        raise RuntimeError("CONFIG_JSON app setting is not set.")
    try:
        return json.loads(raw_config)
    except json.JSONDecodeError as exc:
        raise RuntimeError("CONFIG_JSON is not valid JSON.") from exc


def _get_email_client() -> EmailClient:
    connection_string = os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING")
    if not connection_string:
        raise RuntimeError("AZURE_COMMUNICATION_CONNECTION_STRING is not configured.")
    return EmailClient.from_connection_string(connection_string)


def _send_summary_email(destinations: List[str], subject: str, html: str) -> None:
    sender = os.getenv("EMAIL_SENDER_ADDRESS")
    if not sender:
        raise RuntimeError("EMAIL_SENDER_ADDRESS is not configured.")

    client = _get_email_client()

    message_payload = {
        "senderAddress": sender,
        "content": {
            "subject": subject,
            "html": html,
        },
        "recipients": {
            "to": [{"address": address.strip()} for address in destinations]
        },
    }

    poller = client.begin_send(message_payload)
    _ = poller.result()


_CONFIG_CACHE: Optional[dict] = None


def _get_config() -> dict:
    global _CONFIG_CACHE  # noqa: PLW0603
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = _load_config()
    return _CONFIG_CACHE


def main(blob: func.InputStream) -> None:
    logging.info(
        "rm-analyzer function triggered by blob: name=%s size=%d bytes",
        blob.name,
        blob.length or 0,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as handle:
        handle.write(blob.read())
        temp_path = handle.name

    try:
        config = _get_config()
        destinations, subject, html = summarize.build_summary(temp_path, config)
        _send_summary_email(destinations, subject, html)
        logging.info("Summary email sent to: %s", ", ".join(destinations))
    finally:
        os.unlink(temp_path)
