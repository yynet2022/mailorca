"""Configuration module for MailOrca.

This module holds the global configuration dictionary and provides
a function to load settings from an external JSON file.
"""

import json
from typing import Any

CONFIG: dict[str, Any] = {
    "smtp": {"host": "127.0.0.1", "port": 1025},
    "http": {"host": "127.0.0.1", "port": 8025},
    "max_history": 100,
    "ui": {
        "list_columns": ["Date", "Subject", "To", "From"],
        "detail_headers": [
            "From",
            "To",
            "Cc",
            "Subject",
            "Date",
            "Message-ID",
        ],
    },
    "logging": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s %(name)s:%(lineno)s %(funcName)s:%(levelname)s: %(message)s"  # noqa: E501
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
        "loggers": {
            "mailorca": {
                "level": "WARNING",
                "propagate": True,
            },
        },
    },
}


def load_config(config_file: str) -> None:
    """Load configuration from a JSON file and merge with defaults.

    Args:
        config_file: The path to the configuration JSON file.
    """
    c = CONFIG
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            u = json.load(f)
        # Merge with defaults
        c["smtp"] = c["smtp"] | u.get("smtp", {})
        c["http"] = c["http"] | u.get("http", {})
        c["max_history"] = u.get("max_history", c["max_history"])
        c["ui"]["list_columns"] = u.get("ui", {}).get(
            "list_columns", c["ui"]["list_columns"]
        )
        c["ui"]["detail_headers"] = u.get("ui", {}).get(
            "detail_headers", c["ui"]["detail_headers"]
        )
        c["logging"] = u.get("logging", c["logging"])
    except FileNotFoundError:
        # It's okay if config file doesn't exist, use defaults
        pass
    except Exception as e:
        print(f"Config file error: {e}")
        print("Using defaults.")
