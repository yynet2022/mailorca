import re
import html
# import asyncio
import json
import uuid
import time
import email
import logging
import logging.config
from email.header import decode_header, make_header
from email import policy
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from aiosmtpd.controller import Controller as SMTPController

# --- Configuration Loading ---
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "smtp": {"host": "127.0.0.1", "port": 1025},
    "http": {"host": "127.0.0.1", "port": 8025},
    "max_history": 100,
    "ui": {
        "list_columns": ["Date", "Subject", "To", "From"],
        "detail_headers": ["From", "To", "Cc", "Subject", "Date"]
    },
    "logging": {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s %(name)s:%(lineno)s %(funcName)s:%(levelname)s: %(message)s'  # noqa: E501
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'loggers': {
            'mailorca': {
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
}


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            # Merge with defaults (simplified shallow merge for top keys)
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    except FileNotFoundError:
        print("Config file not found. Using defaults.")
        return DEFAULT_CONFIG


CONFIG = load_config()
logging.config.dictConfig(CONFIG['logging'])
logger = logging.getLogger(__name__)


# --- In-Memory Data Store ---
class MailStore:
    def __init__(self, max_history: int):
        self.mails: List[Dict[str, Any]] = []
        self.max_history = max_history

    def add(self, raw_data: bytes):
        mail_id = str(uuid.uuid4())
        timestamp = time.time()

        # Parse Email
        parsed = self._parse_email(raw_data)

        entry = {
            "id": mail_id,
            "timestamp": timestamp,
            "raw": raw_data,
            "parsed": parsed
        }

        self.mails.insert(0, entry)  # Prepend (Newest first)

        # Trim history
        if len(self.mails) > self.max_history:
            self.mails = self.mails[:self.max_history]

    def get(self, mail_id: str) -> Optional[Dict]:
        for m in self.mails:
            if m["id"] == mail_id:
                return m
        return None

    def _parse_email(self, raw_data: bytes) -> Dict:
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
                charset = part.get_content_charset() or 'utf-8'
                try:
                    text = payload.decode(charset, errors='replace')
                except LookupError:
                    text = payload.decode('utf-8', errors='replace')

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
            "body_html": body_html
        }


STORE = MailStore(max_history=CONFIG["max_history"])


# --- Helpers ---
def urlize_text(text: str) -> str:
    """Convert URLs in text to clickable links."""
    if not text:
        return ""
    # Escape HTML first to prevent XSS from original text
    escaped_text = html.escape(text)
    # Simple regex for URLs
    url_pattern = re.compile(r'(https?://[^\s]+)')
    # Replace URL with <a> tag
    return url_pattern.sub(
        r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped_text)


# --- SMTP Handler ---
class MailHandler:
    async def handle_DATA(self, server, session, envelope):
        logger.info(f"Mail received from {envelope.mail_from}")
        STORE.add(envelope.content)
        return '250 OK'


# --- FastAPI App & Templates ---
# Register Templates manually since we are using strings
templates = Jinja2Templates(directory="templates")
templates.env.filters["urlize"] = urlize_text


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run SMTP Server
    controller = SMTPController(
        MailHandler(),
        hostname=CONFIG["smtp"]["host"],
        port=CONFIG["smtp"]["port"]
    )
    controller.start()
    logger.info(
        f"SMTP listening on {CONFIG['smtp']['host']}:{CONFIG['smtp']['port']}"
    )
    logger.info(
        "Web UI available at "
        f"http://{CONFIG['http']['host']}:{CONFIG['http']['port']}"
    )

    yield

    # Shutdown
    controller.stop()
    logger.info("SMTP stopped.")


app = FastAPI(title="MailOrca", lifespan=lifespan)

# --- Routes ---


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("list.html", {
        "request": request,
        "mails": STORE.mails,
        "columns": CONFIG["ui"]["list_columns"],
        "smtp_port": CONFIG["smtp"]["port"]
    })


@app.get("/mail/{mail_id}", response_class=HTMLResponse)
async def detail(request: Request, mail_id: str):
    mail = STORE.get(mail_id)
    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "mail": mail,
        "detail_headers": CONFIG["ui"]["detail_headers"]
    })


@app.get("/mail/{mail_id}/download")
async def download_raw(mail_id: str):
    mail = STORE.get(mail_id)
    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    # Return as .eml file
    filename = f"{mail_id}.eml"
    return Response(
        content=mail["raw"],
        media_type="message/rfc822",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/mails")
async def api_list():
    # Remove raw bytes for JSON response to be lighter
    safe_mails = []
    for m in STORE.mails:
        c = m.copy()
        del c["raw"]
        safe_mails.append(c)
    return JSONResponse(safe_mails)


@app.get("/api/mails/{mail_id}")
async def api_detail(mail_id: str):
    mail = STORE.get(mail_id)
    if not mail:
        return JSONResponse({"error": "Not found"}, status_code=404)
    c = mail.copy()
    c.pop("raw", None)  # Remove raw bytes
    return JSONResponse(c)


def main():
    try:
        import uvicorn
        uvicorn.run(
            "mailorca:app",
            host=CONFIG["http"]["host"],
            port=CONFIG["http"]["port"],
            reload=False
        )
    except Exception as e:
        logger.error(f'Error: {e}')


if __name__ == "__main__":
    main()
