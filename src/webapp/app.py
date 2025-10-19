"""Minimal Flask uploader that saves transaction exports to Blob Storage."""

from __future__ import annotations

# Standard library imports
import base64
import datetime as dt
import json
import os
import uuid

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

# Third-party imports
from azure.core.exceptions import AzureError
from azure.identity import (
    DefaultAzureCredential,
)
from azure.storage.blob import (
    BlobServiceClient,
    ContentSettings,
)


def _allowed_emails() -> set[str]:
    """Return the configured set of authorized uploader email addresses."""
    raw = os.getenv("AUTHORIZED_USER_EMAILS", "")
    return {email.strip().lower() for email in raw.split(",") if email.strip()}


def _get_blob_service() -> BlobServiceClient:
    """Create a BlobServiceClient using either a connection string or managed identity."""
    connection_string = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
    if connection_string:
        return BlobServiceClient.from_connection_string(connection_string)

    account_name = os.getenv("STORAGE_ACCOUNT_NAME")
    if not account_name:
        raise RuntimeError(
            "STORAGE_ACCOUNT_NAME or STORAGE_ACCOUNT_CONNECTION_STRING must be configured."
        )

    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    account_url = f"https://{account_name}.blob.core.windows.net"
    return BlobServiceClient(account_url=account_url, credential=credential)


def _extract_email_from_principal() -> str | None:
    """Extract the authenticated user's email address from platform headers, if present."""
    header = request.headers.get("X-MS-CLIENT-PRINCIPAL")
    if not header:
        return None

    try:
        decoded = base64.b64decode(header)
        principal = json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return None

    claims = principal.get("claims", [])
    for claim in claims:
        claim_type = claim.get("typ", "")
        if claim_type.endswith("/emailaddress") or claim_type.endswith("/upn"):
            return claim.get("val")
    return principal.get("userDetails")


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit
app.secret_key = os.getenv("FLASK_SECRET_KEY", uuid.uuid4().hex)

ALLOWED_EMAILS = _allowed_emails()
UPLOAD_CONTAINER = os.getenv("UPLOAD_CONTAINER_NAME", "uploads")
DEBUG_ALLOW_ANON = os.getenv("DEBUG_ALLOW_ANON", "").lower() == "true"

_BLOB_SERVICE = _get_blob_service()


@app.before_request
def require_login() -> None:
    """Ensure the caller is authenticated and in the approved list."""
    if DEBUG_ALLOW_ANON:
        g.user_email = "debug@example.com"
        return

    user_email = _extract_email_from_principal()
    if not user_email:
        abort(401)

    user_email_lower = user_email.lower()
    if ALLOWED_EMAILS and user_email_lower not in ALLOWED_EMAILS:
        abort(403)

    g.user_email = user_email


@app.route("/", methods=["GET", "POST"])
def index():
    """Render the upload form and handle CSV upload POSTs."""
    if request.method == "POST":
        upload = request.files.get("file")
        if not upload or upload.filename == "":
            flash("Please choose a CSV file to upload.", "error")
            return redirect(url_for("index"))

        filename = secure_filename(upload.filename)
        if not filename.lower().endswith(".csv"):
            flash("Only CSV files exported from Rocket Money are supported.", "error")
            return redirect(url_for("index"))

        blob_name = (
            f"{dt.datetime.now(dt.timezone.utc):%Y%m%d-%H%M%S}-"
            f"{uuid.uuid4().hex[:8]}-{filename or 'transactions.csv'}"
        )

        blob_client = _BLOB_SERVICE.get_blob_client(
            container=UPLOAD_CONTAINER, blob=blob_name
        )

        try:
            upload.stream.seek(0)
            blob_client.upload_blob(
                upload.stream.read(),
                overwrite=False,
                content_settings=ContentSettings(content_type="text/csv"),
            )
        except AzureError as exc:
            flash(f"Upload failed: {exc}", "error")
            return redirect(url_for("index"))

        flash("Upload received. Analysis will arrive via email shortly.", "success")
        return redirect(url_for("index"))

    return render_template("index.html", user_email=g.get("user_email", ""))


@app.get("/healthz")
def healthcheck():
    """Expose a simple health probe endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
