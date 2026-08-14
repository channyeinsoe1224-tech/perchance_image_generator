# PROJECT_SPEC.md — Perchance Image Generator Library (v2.0)

## Overview

**Perchance Image Generator** is an Object-Oriented, asynchronous Python library that generates AI images using [Perchance AI Text-to-Image Generator](https://perchance.org/ai-text-to-image-generator).

- **Version 2 (`PerchanceHTTPGenerator`):** Chromeless direct API execution running headlessly in background without opening Chrome windows.
- **Version 1 (`PerchanceGenerator`):** Playwright browser context engine with DOM session reuse.
- **Backup:** Preserved in `v1_backup/`.

---

## Directory Layout

```
perchance_image_generator/
│
├── perchance/                     # Core OOP Python Library Package
│   ├── __init__.py                # Package exports (PerchanceGenerator, PerchanceHTTPGenerator, etc.)
│   ├── client.py                  # V1 Playwright client class (PerchanceGenerator)
│   ├── http_client.py             # V2 Chromeless HTTP client (PerchanceHTTPGenerator)
│   ├── models.py                  # Dataclasses and enums (ImageResult, Shape)
│   ├── exceptions.py              # Custom exceptions
│   └── network.py                 # NetworkLogger for traffic capture
│
├── v1_backup/                     # Complete physical copy backup of Version 1
│
├── examples/                      # Example usage scripts
│   ├── v2_http_quickstart.py      # V2 Chromeless quickstart example
│   ├── quickstart.py              # V1 basic image generation example
│   ├── batch_generation.py        # Multi-image batch generation example
│   └── capture_network_log.py     # Network logging example
│
├── run_v2_test.py                 # Root test script for Version 2
├── run_test.py                    # Root test script for Version 1
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
