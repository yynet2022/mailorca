# -*- coding:utf-8 -*-
import email
import time
import uuid
from email import policy
from email.header import decode_header, make_header
from typing import Any, Optional

from .config import CONFIG


# --- In-Memory Data Store ---
class MailStore:
    """In-memory store for received emails."""

    def __init__(self, max_history: int):
        """Initialize the mail store.

        Args:
            max_history: The maximum number of emails to retain.
        """
        self.mails: list[dict[str, Any]] = []
        self.max_history = max_history

    def add(self, raw_data: bytes) -> None:
        """Add a new email to the store.

        Parses the raw email data, creates a record with a unique ID and
        timestamp, and prepends it to the list. Trims the list if it
        exceeds max_history.

        Args:
            raw_data: The raw bytes of the email message.
        """
        mail_id = str(uuid.uuid4())
        timestamp = time.time()

        # Parse Email
        parsed = self._parse_email(raw_data)

        entry = {
            "id": mail_id,
            "timestamp": timestamp,
            "raw": raw_data,
            "parsed": parsed,
        }

        self.mails.insert(0, entry)  # Prepend (Newest first)

        # Trim history
        if len(self.mails) > self.max_history:
            self.mails = self.mails[: self.max_history]

    def get(self, mail_id: str) -> Optional[dict[str, Any]]:
        """Retrieve an email by its ID.

        Args:
            mail_id: The unique identifier of the email.

        Returns:
            The email dictionary if found, otherwise None.
        """
        for m in self.mails:
            if m["id"] == mail_id:
                return m
        return None

    def _parse_email(self, raw_data: bytes) -> dict[str, Any]:
        """Parse raw email bytes into a structured dictionary.

        Args:
            raw_data: The raw bytes of the email message.

        Returns:
            A dictionary containing headers, body_text, and body_html.
        """
        # Parse bytes to Email Message Object
        msg = email.message_from_bytes(raw_data, policy=policy.default)

        # 1. Parse Headers
        headers = {}
        # Get all header keys to handle duplicates
        for key in set(msg.keys()):
            values = msg.get_all(key)
            decoded_values = []
            for v in values:
                # Helper to decode MIME headers (Subject, Name, etc.)
                # policy.default handles most,
                # but explicit decoding ensures safety
                try:
                    # make_header + decode_header handles =?utf-8?b?...?=
                    h = make_header(decode_header(v))
                    decoded_values.append(str(h))
                except Exception:
                    decoded_values.append(str(v))

            if len(decoded_values) == 1:
                headers[key] = decoded_values[0]
            else:
                # List for multiples like Received
                headers[key] = decoded_values

        # 2. Parse Body (Text & HTML)
        body_text = None
        body_html = None

        def extract_part(part):
            nonlocal body_text, body_html
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                try:
                    text = payload.decode(charset, errors="replace")
                except LookupError:
                    text = payload.decode("utf-8", errors="replace")

                if content_type == "text/plain" and body_text is None:
                    body_text = text
                elif content_type == "text/html" and body_html is None:
                    body_html = text

        if msg.is_multipart():
            for part in msg.walk():
                extract_part(part)
        else:
            extract_part(msg)

        return {
            "headers": headers,
            "body_text": body_text,
            "body_html": body_html,
        }


# Global instance
STORE = MailStore(max_history=CONFIG["max_history"])
