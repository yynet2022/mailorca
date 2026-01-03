#! /usr/bin/env python
# -*- coding:utf-8 -*-
"""MailOrca Server Launcher (Development).

This script is a wrapper around `mailorca.cli.main` to facilitate
running the application during development without installing the package.
"""
import os
import sys

# Add src to sys.path to allow running without installation
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
)

from mailorca.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
