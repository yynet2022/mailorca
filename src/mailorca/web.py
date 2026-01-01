# -*- coding:utf-8 -*-
import html
import logging
import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from aiosmtpd.controller import Controller as SMTPController
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from .config import CONFIG
from .smtp import MailHandler
from .store import STORE

TITLE = "MailOrca"
logger = logging.getLogger(__name__)

# --- Templates ---
# Use relative path to find templates directory within the package
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


# --- Helpers ---
def urlize_text(text: str) -> str:
    """Convert URLs in text to clickable links.

    Args:
        text: The text to process.

    Returns:
        The text with URLs wrapped in anchor tags.
    """
    if not text:
        return ""
    # Escape HTML first to prevent XSS from original text
    escaped_text = html.escape(text)
    # Simple regex for URLs
    url_pattern = re.compile(r"(https?://[^\s]+)")
    # Replace URL with <a> tag
    return url_pattern.sub(
        r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped_text,
    )


templates.env.filters["urlize"] = urlize_text


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the lifecycle of the application (startup/shutdown).

    Starts the SMTP server in a background thread on startup and
    stops it on shutdown.
    """
    # Startup: Run SMTP Server
    controller = SMTPController(
        MailHandler(),
        hostname=CONFIG["smtp"]["host"],
        port=CONFIG["smtp"]["port"],
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


app = FastAPI(title=TITLE, lifespan=lifespan)


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> Response:
    """Render the main page listing received emails."""
    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "mails": STORE.mails,
            "columns": CONFIG["ui"]["list_columns"],
            "smtp_port": CONFIG["smtp"]["port"],
        },
    )


@app.get("/mail/{mail_id}", response_class=HTMLResponse)
async def detail(request: Request, mail_id: str) -> Response:
    """Render the detail page for a specific email."""
    mail = STORE.get(mail_id)
    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "mail": mail,
            "detail_headers": CONFIG["ui"]["detail_headers"],
        },
    )


@app.get("/mail/{mail_id}/download")
async def download_raw(mail_id: str) -> Response:
    """Download the raw .eml file for a specific email."""
    mail = STORE.get(mail_id)
    if not mail:
        raise HTTPException(status_code=404, detail="Mail not found")

    # Return as .eml file
    filename = f"{mail_id}.eml"
    return Response(
        content=mail["raw"],
        media_type="message/rfc822",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/mails")
async def api_list() -> Response:
    """API endpoint to get the list of emails (without raw data)."""
    # Remove raw bytes for JSON response to be lighter
    safe_mails = []
    for m in STORE.mails:
        c = m.copy()
        del c["raw"]
        safe_mails.append(c)
    return JSONResponse(safe_mails)


@app.get("/api/mails/{mail_id}")
async def api_detail(mail_id: str) -> Response:
    """API endpoint to get details of a specific email."""
    mail = STORE.get(mail_id)
    if not mail:
        return JSONResponse({"error": "Not found"}, status_code=404)
    c = mail.copy()
    c.pop("raw", None)  # Remove raw bytes
    return JSONResponse(c)
