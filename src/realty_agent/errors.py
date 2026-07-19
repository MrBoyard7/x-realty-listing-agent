"""Custom exceptions for the pipeline.

Any of these being raised during a scheduled run should be caught by the
Azure Function entry point and turned into an error row in the
spreadsheet (see ``docs/ARCHITECTURE.md`` -> "Error handling").
"""


class RealtyAgentError(Exception):
    """Base class for all agent-specific errors."""


class XFetchError(RealtyAgentError):
    """Raised when posts could not be retrieved from X."""


class WorkbookAccessError(RealtyAgentError):
    """Raised when the OneDrive workbook could not be downloaded/uploaded."""


class ExtractionError(RealtyAgentError):
    """Raised when a post's structured data could not be produced at all."""
