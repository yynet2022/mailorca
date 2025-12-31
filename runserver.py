#! /usr/bin/env python
# -*- coding:utf-8 -*-
#
import click
import logging
import logging.config
from config import CONFIG, load_config

CONFIG_FILE = "config.json"


@click.command(context_settings={"auto_envvar_prefix": "MAILORCA"})
@click.option(
    "--config", type=click.Path(),
    default=CONFIG_FILE,
    help="config-file",
    show_default=True,
)
@click.option(
    "--smtp-host", type=str,
    default=CONFIG['smtp']['host'],
    help="SMTP host",
    show_default=True,
)
@click.option(
    "--smtp-port", type=int,
    default=CONFIG['smtp']['port'],
    help="SMTP port",
    show_default=True,
)
@click.option(
    "--http-host", type=str,
    default=CONFIG['http']['host'],
    help="HTTP host",
    show_default=True,
)
@click.option(
    "--http-port", type=int,
    default=CONFIG['http']['port'],
    help="HTTP port",
    show_default=True,
)
@click.option(
    "--max-history", type=int,
    default=CONFIG['max_history'],
    help="max-history",
    show_default=True,
)
@click.pass_context
def main(ctx, config, smtp_host, smtp_port, http_host, http_port, max_history):
    load_config(config)

    logging.config.dictConfig(CONFIG['logging'])
    logger = logging.getLogger(__name__)

    # check:
    #   ctx.get_parameter_source('val') vs
    #   click.core.ParameterSource.{DEFAULT, COMMANDLINE, ENVIRONMENT}
    p = click.core.ParameterSource
    if ctx.get_parameter_source('smtp_host') != p.DEFAULT:
        CONFIG['smtp']['host'] = smtp_host
    if ctx.get_parameter_source('smtp_port') != p.DEFAULT:
        CONFIG['smtp']['port'] = smtp_port
    if ctx.get_parameter_source('http_host') != p.DEFAULT:
        CONFIG['http']['host'] = http_host
    if ctx.get_parameter_source('http_port') != p.DEFAULT:
        CONFIG['http']['port'] = http_port
    if ctx.get_parameter_source('max_history') != p.DEFAULT:
        CONFIG['max_history'] = max_history

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
