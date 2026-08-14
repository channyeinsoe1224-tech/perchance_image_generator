# PROJECT_SPEC.md — Perchance Image Generator Library

## Overview

**Perchance Image Generator** is an Object-Oriented, asynchronous Python library that generates AI images using [Perchance AI Text-to-Image Generator](https://perchance.org/ai-text-to-image-generator). It uses Playwright browser automation with DOM session reuse, route payload interception, and optional Chrome network logging.

---

## Directory Layout

```
perchance_image_generator/
│
├── perchance/                     # Core OOP Python Library Package
│   ├── __init__.py                # Package exports (PerchanceGenerator, ImageResult, etc.)
│   ├── client.py                  # Core client class (PerchanceGenerator)
│   ├── models.py                  # Dataclasses and enums (ImageResult, Shape)
│   ├── exceptions.py              # Custom exceptions
│   └── network.py                 # NetworkLogger for Chrome traffic capture
│
├── examples/                      # Example usage scripts
│   ├── quickstart.py              # Basic image generation example
│   ├── batch_generation.py        # Multi-image batch generation example
│   └── capture_network_log.py     # Network logging example
│
├── run_test.py                    # Root test script
├── setup.py                       # Setuptools packaging file
├── pyproject.toml                 # Packaging configuration
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

---

## Technical Design

### `PerchanceGenerator` Client

- Managed via `async with PerchanceGenerator() as generator:` context manager.
- `generate()` calls `generate_batch(count=1)`.
- `generate_batch()` loads the Perchance page once per session, handles iframe discovery, fills inputs, and clicks the Generate button $N$ times with a 1.5-second cooldown between requests.
