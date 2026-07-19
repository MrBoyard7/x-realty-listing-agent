"""
realty_agent
============

A lightweight, low-cost agent that reads real estate listing posts from a
configured X (Twitter) account and writes structured rows into an Excel
workbook stored on Microsoft OneDrive.

The package is intentionally split into small, independently testable
pieces so that the AI-extraction step (the most expensive part of the
pipeline in terms of token usage) can be bypassed whenever a post can be
parsed with plain, deterministic rules instead.
"""

__version__ = "0.1.0"
