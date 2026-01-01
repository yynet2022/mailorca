#! /usr/bin/env python
# -*- coding:utf-8 -*-
import asyncio
import logging
import logging.config
import os
import sys

import click

# Add src to sys.path to allow running without installation
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
)

from mailorca.config import CONFIG, load_config  # noqa: E402

CONFIG_FILE = "config.json"


@click.command(context_settings={"auto_envvar_prefix": "MAILORCA"})
@click.option(
    "--config",
    type=click.Path(),
    default=CONFIG_FILE,
    help="Path to the JSON configuration file.",
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
    help="Enable auto-reload.",
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
    ctx,
    config,
    smtp_host,
    smtp_port,
    http_host,
    http_port,
    max_history,
    reload,
    verbose,
):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    load_config(config)

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

    try:
        import uvicorn

        # Note: reload=True works best when the package is installed
        # in editable mode (pip install -e .). If not installed,
        # uvicorn might not detect changes in src/mailorca correctly
        # unless pythonpath is set explicitly.
        uvicorn.run(
            "mailorca.web:app",
            host=CONFIG["http"]["host"],
            port=CONFIG["http"]["port"],
            reload=reload,
        )
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
