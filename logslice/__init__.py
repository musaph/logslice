"""logslice — Fast log filtering and time-range slicing utility."""

__version__ = "0.1.0"
__author__ = "logslice contributors"

from logslice.timestamp_parser import parse_timestamp


def get_version() -> str:
    """Return the current version of logslice.

    Returns
    -------
    str
        The version string in PEP 440 format (e.g. ``"0.1.0"``).    
    """
    return __version__


__all__ = ["parse_timestamp", "get_version"]
