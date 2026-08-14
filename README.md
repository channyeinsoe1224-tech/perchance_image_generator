# Perchance Image Generator (Python OOP Library)

An Object-Oriented, asynchronous Python library for generating AI images using the [Perchance AI Text-to-Image Generator](https://perchance.org/ai-text-to-image-generator) powered by Playwright browser automation.

---

## Features

- 🎨 **Asynchronous & Object-Oriented Design:** Modern Python API using `async/await` and context managers (`async with PerchanceGenerator() as generator:`).
- 🚀 **Session Reuse & Batch Generation:** Single-session page reuse to generate multiple images (`generate_batch`) without reloading the page, saving ~12s per image.
- 📐 **Resolution & Shape Options:** Supports `square` (768x768), `landscape` (768x512), and `portrait` (512x768).
- ⚙️ **Configurable Parameters:** Custom negative prompts, guidance scale (1.0 - 30.0), and seed control.
- 🌐 **Network Logger:** Built-in Chrome network log listener to capture and export raw HTTP traffic and console messages to JSON.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/perchance-image-generator.git
cd perchance-image-generator

# Install dependencies and Playwright Chromium
pip install -r requirements.txt
playwright install chromium

# Install the library in editable mode
pip install -e .
```

---

## Quickstart

```python
import asyncio
from perchance import PerchanceGenerator

async def main():
    # Launch generator client using context manager
    async with PerchanceGenerator() as generator:
        image = await generator.generate(
            prompt="a futuristic cyberpunk cat, neon lights, 8k",
            shape="square",
            negative_prompt="blurry, low quality"
        )
        
        print(f"Generated image seed: {image.seed}")
        image.save("cyberpunk_cat.png")

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
            image.save(f"garden_{idx}.jpg")
            idx += 1

if __name__ == "__main__":
    asyncio.run(main())
```

---

## API Reference

### `PerchanceGenerator`

```python
PerchanceGenerator(
    headless: Optional[bool] = None,
    timeout: float = 90.0,
    user_agent: Optional[str] = None,
    enable_network_logging: bool = False
)
```

- `async generate(prompt, shape="square", negative_prompt="", guidance_scale=7.0, seed=-1) -> ImageResult`
- `async generate_batch(prompt, count=1, shape="square", negative_prompt="", guidance_scale=7.0, first_seed=-1) -> AsyncGenerator[ImageResult, None]`
- `async start()`: Explicitly start browser session.
- `async close()`: Close browser context and release resources.

### `ImageResult`

- `image_bytes`: `bytes` object containing raw image binary data.
- `seed`: `int` seed used for generation.
- `file_extension`: `str` format (e.g. `'jpeg'`).
- `save(path: str)`: Save binary image to disk.
- `to_base64() -> str`: Base64 encoded string.
- `to_data_uri() -> str`: HTML data URI string.

---

## Running Examples & Tests

```bash
# Run root test
python run_test.py

# Run examples
python examples/quickstart.py
python examples/batch_generation.py
python examples/capture_network_log.py
```
