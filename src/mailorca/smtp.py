# -*- coding:utf-8 -*-
import logging
from typing import Any

from aiosmtpd.smtp import Envelope, Session

from .store import STORE

logger = logging.getLogger(__name__)


# --- SMTP Handler ---
class MailHandler:
    """SMTP Handler to process received emails."""

    async def handle_DATA(
        self, server: Any, session: Session, envelope: Envelope
    ) -> str:
        """Handle the DATA command (end of mail transaction).

        Args:
            server: The SMTP server instance.
            session: The current SMTP session.
            envelope: The SMTP envelope containing message data.

        Returns:
            SMTP response string (e.g., "250 OK").
        """
        logger.debug(f"Mail received from {envelope.mail_from}")
        content = envelope.content
        if isinstance(content, str):
            content = content.encode("utf-8")

        if isinstance(content, bytes):
            STORE.add(content)
        else:
            logger.error(f"Received unexpected content type: {type(content)}")
            return "500 Internal Server Error"

        return "250 OK"
