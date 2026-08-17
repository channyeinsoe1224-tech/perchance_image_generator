"""Perchance Image Generator Library.

A modern Object-Oriented Python library for generating AI images using Perchance.
"""

from .client import PerchanceGenerator, PerchanceGeneratorPool
from .models import ImageResult, GenerationOptions, Shape
from .exceptions import (
    PerchanceError,
    GenerationTimeoutError,
    IframeNotFoundError,
    VerificationFailedError,
    DownloadError
)
from .network import NetworkLogger

# Version 2 aliases and exports
PerchanceHTTPGenerator = PerchanceGenerator

__version__ = "2.0.0"
__all__ = [
    "PerchanceGenerator",
    "PerchanceHTTPGenerator",
    "PerchanceGeneratorPool",
    "ImageResult",
    "GenerationOptions",
    "Shape",
    "PerchanceError",
    "GenerationTimeoutError",
    "IframeNotFoundError",
    "VerificationFailedError",
    "DownloadError",
    "NetworkLogger",
]
