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

__version__ = "1.0.0"
__all__ = [
    "PerchanceGenerator",
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
