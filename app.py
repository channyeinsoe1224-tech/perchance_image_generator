"""Perchance AI Studio — Web Application Backend with WebSocket Live Streaming.

FastAPI-based server providing RESTful and WebSocket (ws://) endpoints for generating AI images
using the Perchance Deep Neural Diffusion Engine with real-time streaming progress,
persistent gallery management, and web interface serving.
"""

import asyncio
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from perchance import PerchanceGenerator, Shape

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUTS_DIR = os.path.join(STATIC_DIR, "outputs")
DATA_DIR = os.path.join(BASE_DIR, "data")
GALLERY_FILE = os.path.join(DATA_DIR, "gallery.json")
PROFILE_DIR = os.path.join(DATA_DIR, "browser_profile")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

# Global generator instance and lock for synchronized Perchance browser automation
_generator: Optional[PerchanceGenerator] = None
_generator_lock = asyncio.Lock()


def load_gallery() -> List[Dict[str, Any]]:
    """Load saved gallery items from JSON."""
    if os.path.exists(GALLERY_FILE):
        try:
            with open(GALLERY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_gallery(gallery: List[Dict[str, Any]]) -> None:
    """Save gallery items to JSON."""
    with open(GALLERY_FILE, "w", encoding="utf-8") as f:
        json.dump(gallery, f, indent=2, ensure_ascii=False)


# Presets database
PRESETS = {
    "styles": [
        {
            "id": "none",
            "name": "Default / Raw",
            "style_prompt": "",
            "badge": "Standard",
            "description": "Natural diffusion without style constraint",
            "category": "Basic",
        },
        {
            "id": "photorealistic",
            "name": "Photorealistic",
            "style_prompt": "Photorealistic",
            "badge": "Popular",
            "description": "Ultra-sharp photography, 8k uhd, cinematic lighting",
            "category": "Realistic",
        },
        {
            "id": "anime",
            "name": "Anime & Manga",
            "style_prompt": "Anime",
            "badge": "Popular",
            "description": "Vibrant Japanese anime art style, crisp lineart, Studio aesthetic",
            "category": "Illustration",
        },
        {
            "id": "digital_painting",
            "name": "Digital Painting",
            "style_prompt": "Digital Painting",
            "badge": "Artistic",
            "description": "Rich brush strokes, smooth lighting, ArtStation trending",
            "category": "Artistic",
        },
        {
            "id": "cyberpunk",
            "name": "Cyberpunk Neon",
            "style_prompt": "Cyberpunk",
            "badge": "Trending",
            "description": "Futuristic high-tech cityscape, holographic neon glows, rainy reflections",
            "category": "Sci-Fi",
        },
        {
            "id": "ghibli",
            "name": "Studio Ghibli",
            "style_prompt": "Studio Ghibli",
            "badge": "Artistic",
            "description": "Nostalgic anime aesthetic, lush painted backgrounds, warm atmosphere",
            "category": "Illustration",
        },
        {
            "id": "render3d",
            "name": "3D Render",
            "style_prompt": "3D Render",
            "badge": "Sharp",
            "description": "Cinema4D Octane render, raytracing, subsurface scattering shaders",
            "category": "3D",
        },
        {
            "id": "cinematic",
            "name": "Cinematic Film",
            "style_prompt": "Cinematic Film",
            "badge": "Film",
            "description": "35mm anamorphic lens, shallow depth of field, dramatic color grading",
            "category": "Realistic",
        },
        {
            "id": "concept_art",
            "name": "Concept Art",
            "style_prompt": "Concept Art",
            "badge": "Design",
            "description": "Video game visual development, matte painting, dynamic atmosphere",
            "category": "Artistic",
        },
        {
            "id": "watercolor",
            "name": "Watercolor",
            "style_prompt": "Watercolor",
            "badge": "Traditional",
            "description": "Delicate color bleeds, textured watercolor paper, soft pastel tones",
            "category": "Traditional",
        },
        {
            "id": "oil_painting",
            "name": "Oil Painting",
            "style_prompt": "Oil Painting",
            "badge": "Traditional",
            "description": "Impasto canvas texture, classical lighting, chiaroscuro masters style",
            "category": "Traditional",
        },
        {
            "id": "pixel_art",
            "name": "Retro Pixel Art",
            "style_prompt": "Pixel Art",
            "badge": "Retro",
            "description": "16-bit detailed pixel masterpiece, nostalgic arcade palette",
            "category": "Retro",
        },
        {
            "id": "synthwave",
            "name": "Synthwave 80s",
            "style_prompt": "Synthwave",
            "badge": "Retro",
            "description": "Outrun retro wave, wireframe grid, purple sunset, chrome reflections",
            "category": "Retro",
        },
        {
            "id": "dark_fantasy",
            "name": "Dark Fantasy",
            "style_prompt": "Dark Fantasy",
            "badge": "Mood",
            "description": "Eldritch gothic atmosphere, dark souls aesthetic, dramatic rim lighting",
            "category": "Artistic",
        },
        {
            "id": "isometric",
            "name": "Isometric 3D",
            "style_prompt": "Isometric 3D",
            "badge": "3D",
            "description": "Miniature diorama, clean isometric angle, tilt-shift focus, low-poly charm",
            "category": "3D",
        },
    ],
    "enhancers": {
        "Lighting": [
            "golden hour sunlight",
            "volumetric cinematic rays",
            "soft studio softbox lighting",
            "dramatic rim light",
            "bioluminescent glow",
            "moody neon lighting",
            "candlelight glow",
        ],
        "Detail & Quality": [
            "masterpiece, 8k uhd",
            "hyperdetailed textures",
            "unreal engine 5 render",
            "sharp focus",
            "intricate micro-details",
            "award winning composition",
        ],
        "Camera & Lens": [
            "35mm f/1.4 lens",
            "wide angle perspective",
            "shallow depth of field, bokeh",
            "macro photography",
            "drone aerial view",
            "anamorphic widescreen",
        ],
        "Mood & Vibe": [
            "ethereal and mystical",
            "epic atmosphere",
            "cozy and warm ambiance",
            "gloomy and mysterious",
            "vibrant and energetic",
            "minimalist serene",
        ],
    },
    "prompts": [
        "A cyberpunk street market in Neo-Tokyo with glowing food stalls, rainy pavement reflections, and flying vehicles",
        "A mystical ancient library inside a massive hollow redwood tree, floating glowing lanterns, and magical dust",
        "A serene samurai warrior meditating under falling cherry blossom petals near a misty mountain waterfall",
        "An adorable robotic kitten playing with a holographic butterfly in a sunlit botanical greenhouse",
        "An astronaut discovering an alien crystalline garden on a purple planet under two giant moons",
        "A cozy Nordic cottage covered in fresh winter snow with warm yellow light glowing from the windows at twilight",
        "An ethereal phoenix made of golden flames soaring over a volcanic mountain range at sunset",
        "A steampunk airship navigating through towering floating islands and cascading clouds",
    ],
}


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str = Field(default="")
    style: Optional[str] = Field(default=None)
    shape: str = Field(default="square")
    guidance_scale: float = Field(default=7.0, ge=1.0, le=30.0)
    seed: int = Field(default=-1)
    count: int = Field(default=1, ge=1, le=4)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _generator
    print("[AI Studio] Initializing Perchance Generator Engine...")
    headless_mode = os.environ.get("HEADLESS", "false").lower() == "true"
    _generator = PerchanceGenerator(
        user_data_dir=PROFILE_DIR,
        headless=headless_mode,
        timeout=120.0
    )
    try:
        await _generator.start()
        print("[AI Studio] Perchance Generator active and ready.")
    except Exception as e:
        print(f"[AI Studio] Engine init note: {e}")
    yield
    print("[AI Studio] Shutting down Perchance Generator...")
    if _generator:
        try:
            await _generator.close()
        except Exception:
            pass
    print("[AI Studio] Shutdown complete.")


app = FastAPI(
    title="Perchance AI Image Studio",
    description="Perchance AI Text-to-Image Studio with WebSocket Live Streaming",
    version="2.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon."""
    favicon_path = os.path.join(STATIC_DIR, "favicon.svg")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/api/presets")
async def get_presets():
    """Return style presets, prompt enhancers, and sample prompts."""
    return JSONResponse(content=PRESETS)


@app.get("/api/status")
async def get_status():
    """Get system and engine status."""
    gallery = load_gallery()
    return {
        "status": "online",
        "engine": "Perchance Deep Neural Diffusion",
        "websocket": "ws://127.0.0.1:8000/ws/generate",
        "total_images": len(gallery),
        "is_busy": _generator_lock.locked(),
    }


@app.get("/api/gallery")
async def get_gallery():
    """Get all generated images in the gallery."""
    gallery = load_gallery()
    return JSONResponse(content=list(reversed(gallery)))


@app.delete("/api/gallery/{item_id}")
async def delete_gallery_item(item_id: str):
    """Delete an item from the gallery and remove its file from disk."""
    gallery = load_gallery()
    item_to_delete = None
    new_gallery = []

    for item in gallery:
        if item.get("id") == item_id:
            item_to_delete = item
        else:
            new_gallery.append(item)

    if not item_to_delete:
        raise HTTPException(status_code=404, detail="Image not found in gallery")

    filename = item_to_delete.get("filename")
    if filename:
        filepath = os.path.join(OUTPUTS_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error removing file {filepath}: {e}")

    save_gallery(new_gallery)
    return {"status": "success", "deleted_id": item_id}


@app.post("/api/generate")
async def generate_images_http(req: GenerateRequest):
    """Generate 1 to 4 images using Perchance Engine via REST."""
    global _generator
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    shape_val = req.shape.lower()
    if shape_val not in ["square", "landscape", "portrait"]:
        shape_val = "square"

    shape_enum = (
        Shape.LANDSCAPE
        if shape_val == "landscape"
        else Shape.PORTRAIT
        if shape_val == "portrait"
        else Shape.SQUARE
    )

    style_clean = req.style if (req.style and req.style.lower() not in ["none", ""]) else None

    results = []
    start_time = time.time()

    async with _generator_lock:
        if not _generator or not _generator._context:
            headless_mode = os.environ.get("HEADLESS", "false").lower() == "true"
            _generator = PerchanceGenerator(
                user_data_dir=PROFILE_DIR,
                headless=headless_mode,
                timeout=120.0,
            )
            await _generator.start()

        try:
            gallery = load_gallery()
            async for result in _generator.generate_batch(
                prompt=prompt,
                count=req.count,
                shape=shape_enum,
                negative_prompt=req.negative_prompt,
                guidance_scale=req.guidance_scale,
                first_seed=req.seed,
                style=style_clean,
            ):
                item_id = str(uuid.uuid4())[:8]
                timestamp = int(time.time())
                ext = result.file_extension or "jpeg"
                filename = f"gen_{timestamp}_{item_id}.{ext}"
                filepath = os.path.join(OUTPUTS_DIR, filename)

                result.save(filepath)

                gallery_entry = {
                    "id": item_id,
                    "filename": filename,
                    "url": f"/outputs/{filename}",
                    "prompt": prompt,
                    "style": style_clean or "Default",
                    "shape": shape_val,
                    "resolution": Shape.get_resolution(shape_val),
                    "seed": result.seed,
                    "guidance_scale": req.guidance_scale,
                    "negative_prompt": req.negative_prompt,
                    "size_bytes": len(result.image_bytes),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "download_url": result.download_url,
                }
                gallery.append(gallery_entry)
                results.append(gallery_entry)

            save_gallery(gallery)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    elapsed = time.time() - start_time
    return {
        "status": "success",
        "count": len(results),
        "elapsed_seconds": round(elapsed, 2),
        "results": results,
    }


@app.websocket("/ws/generate")
async def websocket_generate_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming Perchance generation and progress."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt", "").strip()
            if not prompt:
                await websocket.send_json({"type": "error", "message": "Prompt cannot be empty"})
                continue

            shape_val = data.get("shape", "square").lower()
            if shape_val not in ["square", "landscape", "portrait"]:
                shape_val = "square"

            shape_enum = (
                Shape.LANDSCAPE
                if shape_val == "landscape"
                else Shape.PORTRAIT
                if shape_val == "portrait"
                else Shape.SQUARE
            )

            style_clean = data.get("style") or None
            negative_prompt = data.get("negative_prompt", "")
            guidance_scale = float(data.get("guidance_scale", 7.0))
            seed = int(data.get("seed", -1))
            count = max(1, min(4, int(data.get("count", 1))))

            start_time = time.time()
            results = []

            await websocket.send_json({
                "type": "status",
                "stage": "Initializing Perchance Session...",
                "progress": 15,
            })

            global _generator
            async with _generator_lock:
                if not _generator or not _generator._context:
                    headless_mode = os.environ.get("HEADLESS", "false").lower() == "true"
                    _generator = PerchanceGenerator(
                        user_data_dir=PROFILE_DIR,
                        headless=headless_mode,
                        timeout=120.0,
                    )
                    await _generator.start()

                await websocket.send_json({
                    "type": "status",
                    "stage": "Injecting parameters & synthesizing diffusion latents...",
                    "progress": 40,
                })

                gallery = load_gallery()
                item_idx = 0
                async for result in _generator.generate_batch(
                    prompt=prompt,
                    count=count,
                    shape=shape_enum,
                    negative_prompt=negative_prompt,
                    guidance_scale=guidance_scale,
                    first_seed=seed,
                    style=style_clean,
                ):
                    item_idx += 1
                    item_id = str(uuid.uuid4())[:8]
                    timestamp = int(time.time())
                    ext = result.file_extension or "jpeg"
                    filename = f"gen_{timestamp}_{item_id}.{ext}"
                    filepath = os.path.join(OUTPUTS_DIR, filename)

                    result.save(filepath)

                    gallery_entry = {
                        "id": item_id,
                        "filename": filename,
                        "url": f"/outputs/{filename}",
                        "prompt": prompt,
                        "style": style_clean or "Default",
                        "shape": shape_val,
                        "resolution": Shape.get_resolution(shape_val),
                        "seed": result.seed,
                        "guidance_scale": guidance_scale,
                        "negative_prompt": negative_prompt,
                        "size_bytes": len(result.image_bytes),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "download_url": result.download_url,
                    }
                    gallery.append(gallery_entry)
                    results.append(gallery_entry)

                    # Stream image over WebSocket immediately
                    progress_pct = int(40 + (item_idx / count) * 55)
                    await websocket.send_json({
                        "type": "status",
                        "stage": f"Synthesized image {item_idx}/{count}",
                        "progress": progress_pct,
                    })
                    await websocket.send_json({
                        "type": "image_ready",
                        "item": gallery_entry,
                    })

                save_gallery(gallery)

            elapsed = round(time.time() - start_time, 2)
            await websocket.send_json({
                "type": "complete",
                "count": len(results),
                "elapsed_seconds": elapsed,
                "results": results,
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# Mount static assets directory
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_index():
    """Serve main Single-Page Web Application."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Studio UI loading..."}
