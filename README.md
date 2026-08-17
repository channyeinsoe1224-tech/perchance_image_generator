# Perchance Image Generator (Python Library v2.0)

A modern Object-Oriented, asynchronous Python library for generating AI images using the [Perchance AI Text-to-Image Generator](https://perchance.org/ai-text-to-image-generator).

---

## Features

- 🎨 **Asynchronous & Object-Oriented:** Modern Python API using `async/await` and context managers (`async with PerchanceGenerator() as generator:`).
- ⚡ **High Performance Session Reuse:** Single-session reuse to generate batches of images (`generate_batch`) without reloading the page.
- 👥 **Multi-Worker Concurrency:** `PerchanceGeneratorPool` for generating multiple prompts in parallel across independent workers.
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

## Parallel Worker Pool

```python
import asyncio
from perchance import PerchanceGeneratorPool

async def main():
    pool = PerchanceGeneratorPool(workers=2)
    prompts = [
        "a cybernetic wolf in a neon snowstorm, 8k",
        "a cute baby dragon sleeping on gold coins, 8k"
    ]
    results = await pool.generate_parallel(prompts=prompts, shape="square")
    for i, result in enumerate(results):
        result.save(f"pool_output_{i}.jpeg")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🌐 Interactive Web Studio

To launch the web interface locally or on a server:

```bash
python run_webapp.py
```

Then open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (or your VPS IP) in your browser.

---

## 🚀 VPS Server Deployment (Ubuntu / Debian)

### 1. Automated Setup Script

```bash
# Make deploy script executable and run
chmod +x deploy.sh
./deploy.sh
```

### 2. Launch Web Studio

```bash
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
