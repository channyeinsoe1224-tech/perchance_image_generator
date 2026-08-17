"""Perchance AI Studio — Zero-Disk Streaming Proxy Web Application Backend.

FastAPI server providing scalable RESTful and WebSocket (ws://) endpoints with an asynchronous
worker pool for concurrent AI image generation, real-time queue management, live streaming progress,
and Zero-Disk on-demand streaming proxy (0 MB disk storage used for image files).
"""

import asyncio
import base64
import io
import json
import os
import platform
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from perchance import PerchanceGenerator, Shape

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
GALLERY_FILE = os.path.join(DATA_DIR, "gallery.json")
PROFILE_DIR = os.path.join(DATA_DIR, "browser_profile")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)

# Concurrency configuration
MAX_WORKERS = max(1, int(os.environ.get("MAX_WORKERS", "3")))
_gallery_lock = asyncio.Lock()


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
            "name": "Photorealistic 8K",
            "style_prompt": "photorealistic, 8k resolution, raw photo, highly detailed, sharp focus, professional photography, studio lighting",
            "badge": "Popular",
            "description": "Crisp, lifelike details with studio photography realism",
            "category": "Realism",
        },
        {
            "id": "anime",
            "name": "Anime & Manga",
            "style_prompt": "anime aesthetic, Makoto Shinkai style, vibrant colors, detailed line art, masterpiece, high quality illustration",
            "badge": "Anime",
            "description": "Vibrant Japanese anime illustration with expressive lines",
            "category": "Artistic",
        },
        {
            "id": "cyberpunk",
            "name": "Cyberpunk Neon",
            "style_prompt": "cyberpunk style, neon glow, futuristic city, volumetric lighting, reflections on wet asphalt, octane render, 8k",
            "badge": "Sci-Fi",
            "description": "High-tech dystopian atmosphere drenched in neon illumination",
            "category": "Sci-Fi",
        },
        {
            "id": "ghibli",
            "name": "Studio Ghibli",
            "style_prompt": "Studio Ghibli style, Hayao Miyazaki, hand-painted aesthetic, lush green landscapes, whimsical, nostalgic warm lighting",
            "badge": "Artistic",
            "description": "Dreamy, nostalgic hand-painted fantasy animation aesthetic",
            "category": "Artistic",
        },
        {
            "id": "3d_render",
            "name": "3D Pixar / Disney",
            "style_prompt": "3D character render, Pixar style, Disney animation, ray tracing, cute, subsurface scattering, smooth lighting",
            "badge": "3D",
            "description": "Charming 3D stylized CGI character animation look",
            "category": "3D",
        },
        {
            "id": "cinematic",
            "name": "Cinematic Film",
            "style_prompt": "cinematic still, 35mm film grain, dramatic lighting, anamorphic lens flare, movie scene, color graded, ultra detailed",
            "badge": "Cinema",
            "description": "Dramatic Hollywood movie still with anamorphic lighting",
            "category": "Realism",
        },
        {
            "id": "watercolor",
            "name": "Watercolor Painting",
            "style_prompt": "delicate watercolor painting, soft paper texture, artistic color bleeds, vibrant ink splatter, loose brushstrokes",
            "badge": "Traditional",
            "description": "Fluid watercolors with artistic paper texture bleeds",
            "category": "Artistic",
        },
        {
            "id": "oil_painting",
            "name": "Classic Oil Painting",
            "style_prompt": "oil painting on canvas, visible impasto brushstrokes, rich classical colors, Rembrandt lighting, fine art masterpiece",
            "badge": "Traditional",
            "description": "Textured oil on canvas with deep Renaissance lighting",
            "category": "Traditional",
        },
        {
            "id": "pixel_art",
            "name": "Retro Pixel Art",
            "style_prompt": "16-bit pixel art, retro gaming aesthetic, vibrant limited palette, clean pixel clusters, nostalgic arcade look",
            "badge": "Retro",
            "description": "Nostalgic 16-bit vintage video game pixel artwork",
            "category": "Retro",
        },
        {
            "id": "dark_fantasy",
            "name": "Dark Fantasy / Elden",
            "style_prompt": "dark fantasy, gothic, ominous foggy atmosphere, Elden Ring aesthetic, intricate armor, dramatic chiaroscuro, 8k",
            "badge": "Fantasy",
            "description": "Grim, moody gothic fantasy with epic scale and lore",
            "category": "Fantasy",
        },
        {
            "id": "steampunk",
            "name": "Steampunk Victorian",
            "style_prompt": "steampunk aesthetic, polished brass gears, copper pipes, Victorian fashion, steam haze, intricate mechanical parts",
            "badge": "Sci-Fi",
            "description": "Retro-futuristic steam-powered machinery and brass elegance",
            "category": "Sci-Fi",
        },
        {
            "id": "synthwave",
            "name": "Synthwave / Retro 80s",
            "style_prompt": "synthwave 80s retro aesthetic, purple and magenta grid, wireframe neon sun, chrome typography, outrun style",
            "badge": "Retro",
            "description": "80s outrun vaporwave grids with glowing wireframe sunsets",
            "category": "Retro",
        },
        {
            "id": "concept_art",
            "name": "Epic Concept Art",
            "style_prompt": "epic concept art, matte painting, trending on ArtStation, colossal scale, atmospheric depth, highly detailed environment",
            "badge": "Concept",
            "description": "Grand panoramic game and cinema concept art",
            "category": "Concept",
        },
        {
            "id": "isometric",
            "name": "Isometric 3D Diorama",
            "style_prompt": "isometric 3D diorama, low poly cute miniature world, tilt-shift, bright clean lighting, Blender render, detailed",
            "badge": "3D",
            "description": "Charming miniature tilt-shift isometric voxel diorama",
            "category": "3D",
        },
    ],
    "enhancers": {
        "lighting": [
            {"name": "Volumetric Rays", "tag": "volumetric god rays lighting"},
            {"name": "Golden Hour", "tag": "warm golden hour sunset light"},
            {"name": "Moody Neon", "tag": "atmospheric neon rim lighting"},
            {"name": "Studio Softbox", "tag": "diffused studio softbox light"},
            {"name": "Bioluminescence", "tag": "glowing bioluminescent ambient"},
        ],
        "detail": [
            {"name": "8K Hyperdetail", "tag": "8k resolution, ultra-detailed textures"},
            {"name": "Masterpiece", "tag": "award-winning masterpiece, trending on artstation"},
            {"name": "Photorealistic", "tag": "photorealistic, hyperrealistic, octane render"},
            {"name": "Sharp Focus", "tag": "tack sharp focus, highly intricate"},
        ],
        "camera": [
            {"name": "Macro Close-up", "tag": "macro shot, shallow depth of field"},
            {"name": "Wide Angle", "tag": "wide angle cinematic view, 24mm lens"},
            {"name": "Drone Overhead", "tag": "dramatic top-down bird eye view"},
            {"name": "Portrait 85mm", "tag": "85mm f/1.4 portrait lens, creamy bokeh"},
        ],
        "mood": [
            {"name": "Ethereal & Dreamy", "tag": "ethereal, dreamy mystical atmosphere"},
            {"name": "Epic & Majestic", "tag": "epic scale, breathtaking, majestic"},
            {"name": "Dark & Ominous", "tag": "dark, moody, ominous atmospheric tension"},
            {"name": "Whimsical Joy", "tag": "cheerful, vibrant, whimsical, joyful"},
        ],
    },
    "sample_prompts": [
        "A majestic mechanical dragon with translucent crystal wings soaring over neon-lit futuristic Tokyo at midnight",
        "Cozy hidden library inside a giant ancient hollow redwood tree with warm fireflies and floating lanterns",
        "Serene Japanese garden in autumn with vibrant red maple leaves floating on a crystal koi pond, 8k",
        "A cute astronaut red panda discovering glowing alien flora on an unexplored purple moon",
        "Cyberpunk street noodle vendor in rainy Neo-Seoul with neon reflections on wet cobblestones",
        "An intricate steampunk mechanical pocket watch revealing a tiny floating miniature universe inside",
        "Ethereal ice palace on top of aurora borealis mountains under a starry cosmic sky, cinematic still",
        "A magical apothecary shop filled with glowing potions, herb bundles, and sleeping feline familiars",
    ],
}


# ==============================================================================
# Multi-Worker Pool & Queue Architecture
# ==============================================================================
class PerchanceWorker:
    """Individual worker encapsulating an independent Perchance generation session."""

    def __init__(self, worker_id: int):
        self.worker_id = worker_id
        self.profile_dir = os.path.join(PROFILE_DIR, f"worker_{worker_id}")
        os.makedirs(self.profile_dir, exist_ok=True)
        self.generator = PerchanceGenerator(
            user_data_dir=self.profile_dir,
            timeout=120.0,
        )
        self.busy = False
        self.jobs_count = 0

    async def start(self):
        await self.generator.start()

    async def close(self):
        await self.generator.close()


class AsyncGeneratorPoolManager:
    """Manages a pool of concurrent Perchance workers with an asynchronous FIFO queue."""

    def __init__(self, size: int = MAX_WORKERS):
        self.size = size
        self.workers: List[PerchanceWorker] = []
        self.queue: asyncio.Queue[PerchanceWorker] = asyncio.Queue()
        self.waiting_requests = 0
        self._lock = asyncio.Lock()

    async def start(self):
        print(f"[AI Studio Pool] Initializing pool with {self.size} concurrent workers...")
        for i in range(1, self.size + 1):
            worker = PerchanceWorker(worker_id=i)
            try:
                await worker.start()
                print(f"[AI Studio Pool] Worker #{i} ready.")
            except Exception as e:
                print(f"[AI Studio Pool] Worker #{i} startup note: {e}")
            self.workers.append(worker)
            await self.queue.put(worker)
        print(f"[AI Studio Pool] All {len(self.workers)} workers online.")

    @asynccontextmanager
    async def acquire(self, on_queue_update=None):
        async with self._lock:
            self.waiting_requests += 1
            pos = self.waiting_requests

        if on_queue_update and self.queue.empty():
            await on_queue_update(position=pos, estimated_wait=pos * 14)

        worker = await self.queue.get()

        async with self._lock:
            self.waiting_requests = max(0, self.waiting_requests - 1)

        worker.busy = True
        try:
            yield worker
        finally:
            worker.busy = False
            worker.jobs_count += 1
            # Auto-recycle context after 35 jobs for memory maintenance
            if worker.jobs_count >= 35:
                print(f"[AI Studio Pool] Recycling Worker #{worker.worker_id} for memory maintenance...")
                try:
                    await worker.close()
                    await worker.start()
                    worker.jobs_count = 0
                except Exception as err:
                    print(f"[AI Studio Pool] Worker #{worker.worker_id} recycle error: {err}")
            await self.queue.put(worker)

    async def close(self):
        print("[AI Studio Pool] Shutting down all workers...")
        for worker in self.workers:
            try:
                await worker.close()
            except Exception:
                pass
        print("[AI Studio Pool] Shutdown complete.")

    def get_stats(self) -> Dict[str, Any]:
        busy = sum(1 for w in self.workers if w.busy)
        return {
            "total_workers": len(self.workers),
            "busy_workers": busy,
            "available_workers": max(0, len(self.workers) - busy),
            "waiting_in_queue": self.waiting_requests,
        }


# Global pool manager instance
_pool_manager = AsyncGeneratorPoolManager(size=MAX_WORKERS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[AI Studio] Starting Perchance Multi-Worker Service (Zero-Disk Proxy Mode)...")
    await _pool_manager.start()
    yield
    print("[AI Studio] Shutting down Perchance Service...")
    await _pool_manager.close()
    print("[AI Studio] Shutdown complete.")


app = FastAPI(
    title="Perchance AI Image Studio",
    description="Perchance AI Multi-Worker Studio with Streaming Proxy and Zero Disk Usage",
    version="2.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request schemas
class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt description for the image")
    shape: str = Field("square", description="Image aspect ratio: square, landscape, portrait")
    style: Optional[str] = Field(None, description="Visual art style preset")
    negative_prompt: str = Field("", description="Elements to avoid")
    guidance_scale: float = Field(7.0, ge=1.0, le=30.0, description="Guidance scale")
    seed: int = Field(-1, description="Generation seed (-1 for random)")
    count: int = Field(1, ge=1, le=4, description="Number of images to generate (1-4)")


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
    """Get system, pool, and engine status."""
    gallery = load_gallery()
    stats = _pool_manager.get_stats()
    return {
        "status": "online",
        "engine": "Perchance Multi-Worker Neural Diffusion Engine",
        "storage_mode": "Zero-Disk Stream Proxy",
        "websocket": "/ws/generate",
        "total_images": len(gallery),
        **stats,
    }


@app.get("/api/gallery")
async def get_gallery():
    """Get all generated images in the gallery."""
    gallery = load_gallery()
    return JSONResponse(content=list(reversed(gallery)))


@app.get("/api/image/{item_id}")
async def stream_image(item_id: str):
    """Stream image on-the-fly directly to the browser without saving to VPS disk."""
    gallery = load_gallery()
    item = next((img for img in gallery if img.get("id") == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")

    dl_url = item.get("download_url", "")
    if not dl_url:
        raise HTTPException(status_code=404, detail="Image source unavailable")

    # If base64 data URL
    if dl_url.startswith("data:image"):
        try:
            header, b64_str = dl_url.split(",", 1)
            img_bytes = base64.b64decode(b64_str)
            return StreamingResponse(
                io.BytesIO(img_bytes),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=31536000"}
            )
        except Exception:
            raise HTTPException(status_code=500, detail="Invalid image payload")

    # Stream from external CDN URL on-the-fly
    async def image_stream():
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", dl_url) as response:
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Remote stream error")
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(
        image_stream(),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=31536000",
            "Content-Disposition": "inline"
        }
    )


@app.get("/api/download/{item_id}")
async def download_image(item_id: str):
    """Download image under your custom domain link as a saved attachment."""
    gallery = load_gallery()
    item = next((img for img in gallery if img.get("id") == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")

    dl_url = item.get("download_url", "")
    if not dl_url:
        raise HTTPException(status_code=404, detail="Image source unavailable")

    filename = f"perchance_{item_id}.jpeg"

    # If base64 data URL
    if dl_url.startswith("data:image"):
        header, b64_str = dl_url.split(",", 1)
        img_bytes = base64.b64decode(b64_str)
        return StreamingResponse(
            io.BytesIO(img_bytes),
            media_type="image/jpeg",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    # Stream from external CDN
    async def download_stream():
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            async with client.stream("GET", dl_url) as response:
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Remote download error")
                async for chunk in response.aiter_bytes():
                    yield chunk

    return StreamingResponse(
        download_stream(),
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.delete("/api/gallery/{item_id}")
async def delete_gallery_item(item_id: str):
    """Delete an item from the gallery metadata (Zero-disk cleanup)."""
    async with _gallery_lock:
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

        save_gallery(new_gallery)
    return {"status": "success", "deleted_id": item_id}


@app.post("/api/generate")
async def generate_images_http(req: GenerateRequest):
    """Generate 1 to 4 images using Perchance Engine via REST (Zero-disk mode)."""
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

    async with _pool_manager.acquire() as worker:
        try:
            async for result in worker.generator.generate_batch(
                prompt=prompt,
                count=req.count,
                shape=shape_enum,
                negative_prompt=req.negative_prompt,
                guidance_scale=req.guidance_scale,
                first_seed=req.seed,
                style=style_clean,
            ):
                item_id = str(uuid.uuid4())[:8]

                # Determine effective image download URL without writing to disk
                effective_url = result.download_url
                if not effective_url or not effective_url.startswith("http"):
                    effective_url = f"data:image/jpeg;base64,{base64.b64encode(result.image_bytes).decode('ascii')}"

                gallery_entry = {
                    "id": item_id,
                    "url": f"/api/image/{item_id}",
                    "download_link": f"/api/download/{item_id}",
                    "prompt": prompt,
                    "style": style_clean or "Default",
                    "shape": shape_val,
                    "resolution": Shape.get_resolution(shape_val),
                    "seed": result.seed,
                    "guidance_scale": req.guidance_scale,
                    "negative_prompt": req.negative_prompt,
                    "size_bytes": len(result.image_bytes),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "download_url": effective_url,
                    "worker_id": worker.worker_id,
                }

                async with _gallery_lock:
                    gallery = load_gallery()
                    gallery.append(gallery_entry)
                    save_gallery(gallery)

                results.append(gallery_entry)

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
    """WebSocket endpoint with live queue streaming and Zero-Disk proxy execution."""
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

            # Queue update callback
            async def send_queue_notice(position: int, estimated_wait: int):
                try:
                    await websocket.send_json({
                        "type": "status",
                        "stage": f"⏳ Queued: Position #{position} (Est. wait ~{estimated_wait}s)",
                        "progress": 8,
                        "queue_position": position,
                        "estimated_wait": estimated_wait,
                    })
                except Exception:
                    pass

            await websocket.send_json({
                "type": "status",
                "stage": "Assigning worker session...",
                "progress": 15,
            })

            async with _pool_manager.acquire(on_queue_update=send_queue_notice) as worker:
                await websocket.send_json({
                    "type": "status",
                    "stage": f"Worker #{worker.worker_id} active — Synthesizing diffusion latents...",
                    "progress": 35,
                    "worker_id": worker.worker_id,
                })

                item_idx = 0
                async for result in worker.generator.generate_batch(
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

                    effective_url = result.download_url
                    if not effective_url or not effective_url.startswith("http"):
                        effective_url = f"data:image/jpeg;base64,{base64.b64encode(result.image_bytes).decode('ascii')}"

                    gallery_entry = {
                        "id": item_id,
                        "url": f"/api/image/{item_id}",
                        "download_link": f"/api/download/{item_id}",
                        "prompt": prompt,
                        "style": style_clean or "Default",
                        "shape": shape_val,
                        "resolution": Shape.get_resolution(shape_val),
                        "seed": result.seed,
                        "guidance_scale": guidance_scale,
                        "negative_prompt": negative_prompt,
                        "size_bytes": len(result.image_bytes),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "download_url": effective_url,
                        "worker_id": worker.worker_id,
                    }

                    async with _gallery_lock:
                        gallery = load_gallery()
                        gallery.append(gallery_entry)
                        save_gallery(gallery)

                    results.append(gallery_entry)

                    # Stream image over WebSocket immediately
                    progress_pct = int(35 + (item_idx / count) * 60)
                    await websocket.send_json({
                        "type": "status",
                        "stage": f"Worker #{worker.worker_id}: Image {item_idx}/{count} generated",
                        "progress": progress_pct,
                    })
                    await websocket.send_json({
                        "type": "image_ready",
                        "item": gallery_entry,
                    })

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
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_index():
    """Serve main Single-Page Web Application with cache-busting."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    return {"message": "AI Studio UI loading..."}
