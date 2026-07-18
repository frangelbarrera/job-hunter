"""Send drafted cold emails via Gmail API.

Requires OAuth credentials (see README.md → Configuration).
Requests only gmail.send + gmail.readonly scopes.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from email.mime.text import MIMEText
from pathlib import Path

DEFAULT_CREDENTIALS = os.environ.get(
    "GMAIL_CREDENTIALS_PATH",
    os.path.expanduser("~/.config/jobhunt/credentials.json"),
)
DEFAULT_TOKEN = os.environ.get(
    "GMAIL_TOKEN_PATH",
    os.path.expanduser("~/.config/jobhunt/token.json"),
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

# Hard rate limit to protect the sender reputation
MAX_PER_HOUR = 10
MAX_PER_DAY = 50
MIN_DELAY_SECONDS = 30


def _get_service():
    """Build an authenticated Gmail service object."""
    creds_path = Path(DEFAULT_CREDENTIALS)
    token_path = Path(DEFAULT_TOKEN)

    if not creds_path.exists():
        raise FileNotFoundError(
            f"Gmail credentials not found at {creds_path}. See README.md → Configuration for setup."
        )

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def _build_message(to: str, subject: str, body: str, sender: str = "me") -> dict:
    message = MIMEText(body)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_one(
    to: str,
    subject: str,
    body: str,
    dry_run: bool = False,
    confirm: bool = True,
) -> bool:
    """Send a single email. Returns True on success."""
    if confirm:
        print(f"\nTo: {to}")
        print(f"Subject: {subject}")
        print(f"---\n{body[:500]}...\n---")
        answer = input("Send this email? [y/N] ").strip().lower()
        if answer != "y":
            print("Skipped.")
            return False

    if dry_run:
        print("[dry-run] would send")
        return True

    try:
        service = _get_service()
        message = _build_message(to, subject, body)
        result = service.users().messages().send(userId="me", body=message).execute()
        print(f"[sent] id={result['id']}")
        time.sleep(MIN_DELAY_SECONDS)
        return True
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return False


def main(dry_run: bool = False) -> int:
    drafts_file = Path(__file__).resolve().parent.parent / "data" / "drafts.json"
    if not drafts_file.exists():
        print(f"No drafts file: {drafts_file}", file=sys.stderr)
        print("Run `python -m scripts.generate_email --save` first.", file=sys.stderr)
        return 1

    drafts = json.loads(drafts_file.read_text(encoding="utf-8"))
    sent = 0
    for draft in drafts[:MAX_PER_DAY]:
        if sent >= MAX_PER_HOUR:
            print(f"Hit hourly cap of {MAX_PER_HOUR}. Resume later.")
            break
        ok = send_one(
            to=draft["to"],
            subject=draft["subject"],
            body=draft["body"],
            dry_run=dry_run,
        )
        if ok:
            sent += 1
    print(f"\nSent {sent} emails.")
    return 0


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    sys.exit(main(dry_run=dry))
