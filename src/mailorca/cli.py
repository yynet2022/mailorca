#! /usr/bin/env python
# -*- coding:utf-8 -*-
"""MailOrca Command Line Interface.

This module provides the main entry point for the MailOrca application.
"""
import asyncio
import json
import logging
import logging.config
import os
import sys
import tempfile

import click
import uvicorn

from mailorca.config import CONFIG, load_config

# Default config file name to look for in the current directory
DEFAULT_CONFIG_FILE = "config.json"


@click.command(context_settings={"auto_envvar_prefix": "MAILORCA"})
@click.option(
    "--config",
    type=click.Path(),
    default=DEFAULT_CONFIG_FILE,
    help="Path to the JSON configuration file.",
    show_default=True,
)
@click.option(
    "--gen-config",
    is_flag=True,
    default=False,
    help="Output JSON configuration file and exit.",
    show_default=True,
)
@click.option(
    "--smtp-host",
    type=str,
    default=CONFIG["smtp"]["host"],
    help="The hostname or IP address to bind the SMTP server to.",
    show_default=True,
)
@click.option(
    "--smtp-port",
    type=int,
    default=CONFIG["smtp"]["port"],
    help="The port number to listen on for SMTP connections.",
    show_default=True,
)
@click.option(
    "--http-host",
    type=str,
    default=CONFIG["http"]["host"],
    help="The hostname or IP address to bind the Web UI server to.",
    show_default=True,
)
@click.option(
    "--http-port",
    type=int,
    default=CONFIG["http"]["port"],
    help="The port number to listen on for HTTP requests.",
    show_default=True,
)
@click.option(
    "--max-history",
    type=int,
    default=CONFIG["max_history"],
    help="The maximum number of emails to keep in memory.",
    show_default=True,
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="Enable auto-reload (for development).",
    show_default=True,
)
@click.option(
    "--verbose",
    "-v",
    type=int,
    default=0,
    help="Set the verbosity level (0: warning, 1: info, 2: debug).",
    show_default=True,
)
@click.pass_context
def main(
    ctx: click.Context,
    config: str,
    gen_config: bool,
    smtp_host: str,
    smtp_port: int,
    http_host: str,
    http_port: int,
    max_history: int,
    reload: bool,
    verbose: int,
) -> None:
    """Run the MailOrca server with the specified configuration."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Load config if file exists
    load_config(config)

    # Verbosity handling
    if verbose > 1:
        CONFIG["logging"]["loggers"]["mailorca"]["level"] = "DEBUG"
    elif verbose > 0:
        CONFIG["logging"]["loggers"]["mailorca"]["level"] = "INFO"
    if verbose > 11:
        CONFIG["logging"]["root"]["level"] = "DEBUG"
    elif verbose > 10:
        CONFIG["logging"]["root"]["level"] = "INFO"

    logging.config.dictConfig(CONFIG["logging"])
    logger = logging.getLogger("mailorca")

    p = click.core.ParameterSource
    if ctx.get_parameter_source("smtp_host") != p.DEFAULT:
        CONFIG["smtp"]["host"] = smtp_host
    if ctx.get_parameter_source("smtp_port") != p.DEFAULT:
        CONFIG["smtp"]["port"] = smtp_port
    if ctx.get_parameter_source("http_host") != p.DEFAULT:
        CONFIG["http"]["host"] = http_host
    if ctx.get_parameter_source("http_port") != p.DEFAULT:
        CONFIG["http"]["port"] = http_port
    if ctx.get_parameter_source("max_history") != p.DEFAULT:
        CONFIG["max_history"] = max_history

    if gen_config:
        file_handle, file_path = tempfile.mkstemp(
            suffix=".json", prefix="config_", dir=".", text=True
        )
        try:
            with os.fdopen(file_handle, "w", encoding="utf-8") as f:
                json.dump(CONFIG, f, ensure_ascii=False, indent=2)
                f.write("\n")
            click.echo(f"Generate config file: {file_path}")
        except Exception as e:
            click.echo(e)
        sys.exit(0)

    try:
        uvicorn.run(
            "mailorca.web:app",
            host=CONFIG["http"]["host"],
            port=CONFIG["http"]["port"],
            log_config=CONFIG["logging"],
            reload=reload,
        )
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
