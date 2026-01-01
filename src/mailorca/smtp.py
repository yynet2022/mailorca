# -*- coding:utf-8 -*-
import logging

from .store import STORE

logger = logging.getLogger(__name__)


# --- SMTP Handler ---
class MailHandler:
    async def handle_DATA(self, server, session, envelope):
        logger.debug(f"Mail received from {envelope.mail_from}")
        STORE.add(envelope.content)
        return "250 OK"
