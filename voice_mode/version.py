"""Enhanced version detection."""
from .__version__ import __version__ as base_version

def get_version():
    return base_version

__version__ = get_version()
