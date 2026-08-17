# PROJECT_SPEC.md — Perchance Image Generator Library (v2.3)

## Overview

**Perchance Image Generator** is an Object-Oriented, asynchronous Python library and high-concurrency web application for generating AI images using [Perchance AI Text-to-Image Generator](https://perchance.org/ai-text-to-image-generator).

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
│   ├── css/style.css              # Custom responsive stylesheet
│   ├── js/app.js                  # Frontend WebSocket streaming & queue client
│   ├── favicon.svg                # Vector SVG branding favicon
│   └── index.html                 # Single-page web studio interface
│
├── app.py                         # FastAPI backend with multi-worker pool & async FIFO queue
├── run_webapp.py                  # Web Studio launcher with host/port binding
├── deploy.sh                      # Ubuntu / Debian automated deployment script
├── perchance-studio.service       # Systemd unit file for 24/7 background operation
├── nginx.conf                     # Reverse proxy configuration with WebSocket support
├── run_test.py                    # Root verification test script
├── setup.py                       # Setuptools packaging file
├── pyproject.toml                 # Packaging configuration
├── requirements.txt               # Dependencies
└── README.md                      # Documentation
```

---

## High-Concurrency Multi-Worker Architecture

- **`AsyncGeneratorPoolManager`:** Manages $N$ concurrent Chromium sessions (`MAX_WORKERS` env var, default: 3).
- **Asynchronous FIFO Queue:** Queues incoming requests with real-time queue position and estimated wait time calculation.
- **Session Auto-Recycling:** Automatically recycles browser contexts every 35 generations to ensure constant memory stability on VPS servers.
