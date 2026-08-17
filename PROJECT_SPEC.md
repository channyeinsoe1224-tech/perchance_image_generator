# PROJECT_SPEC.md — Perchance Image Generator Library (v2.4)

## Overview

**Perchance Image Generator** is an Object-Oriented, asynchronous Python library and high-concurrency Web Studio for generating AI images using [Perchance AI Text-to-Image Generator](https://perchance.org/ai-text-to-image-generator) with **Zero-Disk Streaming Proxy** technology.

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
├── app.py                         # FastAPI backend with multi-worker pool & Zero-Disk stream proxy
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

## Zero-Disk Streaming Proxy Architecture

- **0 MB Server Disk Usage:** No generated images are stored or accumulated on the server hard drive.
- **On-the-Fly Stream Proxy (`/api/image/{id}`):** When a user or frontend requests an image, FastAPI streams the image bytes on the fly directly to the browser with caching headers (`max-age=31536000`).
- **Direct Custom Domain Downloads (`/api/download/{id}`):** Downloads are served as attachments under your own domain name without temporary file disk writes.
