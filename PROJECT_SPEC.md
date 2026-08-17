# PROJECT_SPEC.md — Perchance Image Generator Library (v2.0)

## Overview

**Perchance Image Generator** is an Object-Oriented, asynchronous Python library that generates AI images using [Perchance AI Text-to-Image Generator](https://perchance.org/ai-text-to-image-generator).

---

## Directory Layout

```
perchance_image_generator/
│
├── perchance/                     # Core OOP Python Library Package
│   ├── __init__.py                # Package exports (PerchanceGenerator, PerchanceGeneratorPool, etc.)
│   ├── client.py                  # Core client and worker pool implementation
│   ├── models.py                  # Dataclasses and enums (ImageResult, Shape)
│   ├── exceptions.py              # Custom exceptions
│   └── network.py                 # NetworkLogger for traffic capture
│
├── examples/                      # Example usage scripts
│   ├── quickstart.py              # Basic image generation example
│   ├── batch_generation.py        # Multi-image batch generation example
│   ├── multi_creator_pool.py      # Concurrent parallel worker pool example
│   ├── persistent_profile.py      # Session persistence with Chrome user profile
│   └── capture_network_log.py     # Network logging example
│
├── static/                        # Web app UI frontend (HTML/CSS/JS)
├── app.py                         # FastAPI backend server with WebSocket live streaming
├── run_webapp.py                  # Launcher for the interactive AI Web Studio
├── run_test.py                    # Root verification test script
├── setup.py                       # Setuptools packaging file
├── pyproject.toml                 # Packaging configuration
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

---

## Technical Design

### `PerchanceGenerator` Client

- Managed via `async with PerchanceGenerator() as generator:` context manager.
- `generate()`: Generates a single image with customizable prompts, shape, art styles, guidance scale, and seeds.
- `generate_batch()`: Loads the Perchance page once per session, handles iframe discovery, fills inputs, and generates multiple images without page reloads.
- `PerchanceGeneratorPool`: Manages parallel generation across multiple asynchronous workers.
