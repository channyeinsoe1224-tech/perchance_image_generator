"""Data models for Perchance Image Generator library."""

import os
import base64
import io
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

class Shape(str, Enum):
    SQUARE = "square"
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"

    @classmethod
    def get_resolution(cls, shape_str: str) -> str:
        s = shape_str.lower()
        if s == "portrait":
            return "512x768"
        elif s == "landscape":
            return "768x512"
        return "768x768"

@dataclass
class GenerationOptions:
    prompt: str
    shape: str = "square"
    negative_prompt: str = ""
    guidance_scale: float = 7.0
    seed: int = -1
    style: Optional[str] = None

@dataclass
class ImageResult:
    """Result of an image generation request."""
    image_bytes: bytes
    file_extension: str
    seed: int
    prompt: str
    shape: str = "square"
    guidance_scale: float = 7.0
    negative_prompt: str = ""
    style: Optional[str] = None
    image_id: Optional[str] = None
    download_url: Optional[str] = None

    @property
    def size_bytes(self) -> int:
        return len(self.image_bytes)

    def save(self, output_path: str) -> str:
        """Save the image bytes to a file path on disk."""
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(self.image_bytes)
        return output_path

    def to_base64(self) -> str:
        """Get the image encoded as a base64 string."""
        return base64.b64encode(self.image_bytes).decode("utf-8")

    def to_data_uri(self) -> str:
        """Get the image as a Data URI for HTML display."""
        mime_type = "image/png" if self.file_extension.lower() == "png" else "image/jpeg"
        return f"data:{mime_type};base64,{self.to_base64()}"

    def __repr__(self) -> str:
        return f"<ImageResult seed={self.seed} format={self.file_extension} size={self.size_bytes}B>"
