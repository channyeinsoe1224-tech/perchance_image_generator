# Perchance Image Generator (Python Library v2.4)

A modern Object-Oriented, asynchronous Python library and high-concurrency Web Studio for generating AI images using the [Perchance AI Text-to-Image Generator](https://perchance.org/ai-text-to-image-generator) featuring **Zero-Disk Storage Streaming Proxy**.

---

## Features

- 🎨 **Asynchronous & Object-Oriented:** Modern Python API using `async/await` and context managers (`async with PerchanceGenerator() as generator:`).
- 💾 **Zero-Disk Storage Mode:** The server uses **0 MB disk storage for images**. Images are proxied and streamed on-the-fly directly to the browser under your custom domain links (`/api/image/{id}` and `/api/download/{id}`).
- 👥 **High-Concurrency Multi-Worker Pool:** Built-in `AsyncGeneratorPoolManager` in the Web Studio with $N$ concurrent workers for simultaneous multi-user generations.
- ⏳ **Smart Asynchronous FIFO Queue:** Real-time queue positioning and live wait countdowns over WebSockets when server capacity is full.
- ⚡ **High Performance Session Reuse:** Single-session reuse to generate batches of images (`generate_batch`) without reloading the page.
- 📐 **Resolution & Shape Options:** Supports `square` (768x768), `landscape` (768x512), and `portrait` (512x768).
- ⚙️ **Fine-Tuning Controls:** Negative prompts, guidance scale (1.0 - 30.0), seed control, and art styles.
- 🌐 **Interactive AI Web Studio:** Built-in FastAPI web application with real-time WebSocket progress streaming and persistent local gallery.
- 🚀 **VPS & Cloud Ready:** Native support for Ubuntu/Debian deployment, systemd background daemon, and Nginx reverse proxy.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/channyeinsoe1224-tech/perchance_image_generator.git
cd perchance_image_generator

# Install dependencies and Playwright Chromium
pip install -r requirements.txt
playwright install --with-deps chromium

# Install the library in editable mode
pip install -e .
```

---

## Quickstart

```python
import asyncio
from perchance import PerchanceGenerator

async def main():
    async with PerchanceGenerator() as generator:
        image = await generator.generate(
            prompt="a futuristic cyberpunk cat, neon lights, 8k",
            shape="square",
            negative_prompt="blurry, low quality"
        )
        
        print(f"Generated image seed: {image.seed}")
        image.save("cyberpunk_cat.jpeg")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Batch Generation (Multiple Images in 1 Session)

```python
import asyncio
from perchance import PerchanceGenerator

async def main():
    async with PerchanceGenerator() as generator:
        idx = 1
        async for image in generator.generate_batch(
            prompt="serene Japanese garden with cherry blossoms, landscape",
            count=3,
            shape="landscape"
        ):
            print(f"Image {idx} ready (Seed: {image.seed})")
            image.save(f"garden_{idx}.jpeg")
            idx += 1

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🌐 Interactive Multi-User Web Studio (Zero-Disk Mode)

To launch the web interface:

```bash
# Default: 3 concurrent workers (configurable via MAX_WORKERS)
python run_webapp.py
```

Then open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (or your VPS IP) in your browser.

- **Viewing Images:** `http://<your-host>:8000/api/image/<image-id>` (Streams directly from source on demand, 0 MB disk used).
- **Downloading Images:** `http://<your-host>:8000/api/download/<image-id>` (Downloads as named attachment).

---

## 🚀 VPS Server Deployment (Ubuntu / Debian)

### 1. Automated Setup Script

```bash
chmod +x deploy.sh
./deploy.sh
```

### 2. Launch Web Studio

```bash
# Optional: Set MAX_WORKERS for higher capacity (e.g. 4-6 on 4GB+ VPS)
export MAX_WORKERS=3
source venv/bin/activate
python run_webapp.py
```

### 3. Run as 24/7 Background Systemd Service

```bash
sudo cp perchance-studio.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now perchance-studio
sudo systemctl status perchance-studio
```

---

## Running Tests

```bash
python run_test.py
```
