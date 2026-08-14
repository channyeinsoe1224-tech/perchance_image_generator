"""Custom exceptions for Perchance Image Generator library."""

class PerchanceError(Exception):
    """Base exception for all Perchance errors."""
    pass

class GenerationTimeoutError(PerchanceError):
    """Raised when image generation times out."""
    pass

class IframeNotFoundError(PerchanceError):
    """Raised when the generator iframe is not found on the page."""
    pass

class VerificationFailedError(PerchanceError):
    """Raised when user verification or Turnstile challenge fails."""
    pass

class DownloadError(PerchanceError):
    """Raised when fetching or downloading the generated image fails."""
    pass
