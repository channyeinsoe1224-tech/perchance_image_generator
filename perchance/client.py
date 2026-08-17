"""Core OOP client for Perchance Image Generator."""

import os
import json
import base64
import asyncio
import platform
import random
from typing import AsyncGenerator, List, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .models import ImageResult, Shape
from .exceptions import (
    PerchanceError,
    GenerationTimeoutError,
    IframeNotFoundError,
    VerificationFailedError,
    DownloadError
)
from .network import NetworkLogger

GENERATOR_PAGE_URL = "https://perchance.org/ai-text-to-image-generator"
BROWSERS = ["148.0.0.0", "147.0.0.0", "146.0.0.0", "145.0.0.0"]

class PerchanceGenerator:
    """Object-Oriented Async Client for Perchance AI Image Generation.
    
    Example:
        ```python
        async with PerchanceGenerator() as generator:
            image = await generator.generate("a futuristic cybernetic cat")
            image.save("cat.png")
        ```
    """

    def __init__(
        self,
        generator_url: str = GENERATOR_PAGE_URL,
        headless: Optional[bool] = None,
        timeout: float = 90.0,
        user_agent: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        enable_network_logging: bool = False
    ):
        """Initialize the PerchanceGenerator instance.
        
        Args:
            generator_url: The URL of the Perchance generator page.
            headless: Whether to launch Chromium in headless mode. 
                      Defaults to env var HEADLESS or False (headful recommended for Turnstile).
            timeout: Timeout in seconds for image generation.
            user_agent: Optional custom browser User-Agent string.
            user_data_dir: Optional path to persistent Chrome user profile directory.
                           Preserves cookies, Cloudflare tokens, and localStorage to bypass bot detection.
            enable_network_logging: Set True to record Chrome network activity.
        """
        self.generator_url = generator_url
        if headless is None:
            if os.environ.get("HEADLESS") is not None:
                self.headless = os.environ.get("HEADLESS", "false").lower() == "true"
            elif platform.system() == "Linux" and not os.environ.get("DISPLAY"):
                self.headless = True
            else:
                self.headless = False
        else:
            self.headless = headless

        self.timeout = timeout
        self.user_agent = user_agent
        self.user_data_dir = user_data_dir
        self.enable_network_logging = enable_network_logging
        self.network_logger: Optional[NetworkLogger] = NetworkLogger() if enable_network_logging else None

        self._pw = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _generate_user_agent(self, browser_version: str) -> str:
        if self.user_agent:
            return self.user_agent
        sys_name = platform.system()
        if sys_name == "Windows":
            platform_str = "Windows NT 10.0; Win64; x64"
        elif sys_name == "Darwin":
            platform_str = "Macintosh; Intel Mac OS X 10_15_7"
        else:
            platform_str = "X11; Linux x86_64"
        return (
            f"Mozilla/5.0 ({platform_str}) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{browser_version} Safari/537.36"
        )

    async def start(self):
        """Start Playwright browser context if not already active."""
        if self._context:
            return

        self._pw = await async_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-first-run",
        ]

        if self.user_data_dir:
            os.makedirs(self.user_data_dir, exist_ok=True)
            try:
                self._context = await self._pw.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                    args=launch_args,
                    viewport={"width": 1280, "height": 800},
                    user_agent=self.user_agent or self._generate_user_agent("148.0.0.0")
                )
                self._browser = None
            except Exception as e:
                # If profile directory is locked by another process, fallback to standard session
                self._browser = await self._pw.chromium.launch(
                    headless=self.headless,
                    args=launch_args
                )
                context_kwargs = {"viewport": {"width": 1280, "height": 800}}
                if self.headless or self.user_agent:
                    context_kwargs["user_agent"] = self._generate_user_agent(self._browser.version)
                self._context = await self._browser.new_context(**context_kwargs)
        else:
            self._browser = await self._pw.chromium.launch(
                headless=self.headless,
                args=launch_args
            )

            context_kwargs = {"viewport": {"width": 1280, "height": 800}}
            if self.headless or self.user_agent:
                context_kwargs["user_agent"] = self._generate_user_agent(self._browser.version)

            self._context = await self._browser.new_context(**context_kwargs)

        if self.network_logger:
            self.network_logger.attach_to_context(self._context)

    async def close(self):
        """Close browser context and release resources."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._pw:
            await self._pw.stop()
            self._pw = None

    async def generate(
        self,
        prompt: str,
        shape: Union[str, Shape] = "square",
        negative_prompt: str = "",
        guidance_scale: float = 7.0,
        seed: int = -1,
        style: Optional[str] = None
    ) -> ImageResult:
        """Generate a single image.

        Args:
            prompt: Text description of the image to generate.
            shape: Image shape ('square', 'landscape', 'portrait').
            negative_prompt: Elements to avoid in the image.
            guidance_scale: Prompt accuracy scale (1.0 to 30.0).
            seed: Generation seed (-1 for random).
            style: Art style choice (e.g. 'Cinematic', 'Digital Painting', 'Studio Ghibli', 'Casual Photo', 'Anime', 'Watercolor').

        Returns:
            ImageResult object containing image bytes and metadata.
        """
        async for result in self.generate_batch(
            prompt=prompt,
            count=1,
            shape=shape,
            negative_prompt=negative_prompt,
            guidance_scale=guidance_scale,
            first_seed=seed,
            style=style
        ):
            return result
        raise PerchanceError("Failed to generate image")

    async def generate_batch(
        self,
        prompt: str,
        count: int = 1,
        shape: Union[str, Shape] = "square",
        negative_prompt: str = "",
        guidance_scale: float = 7.0,
        first_seed: int = -1,
        style: Optional[str] = None
    ) -> AsyncGenerator[ImageResult, None]:
        """Generate `count` images in a single browser session (reusing DOM session).

        Yields:
            ImageResult objects as they are generated.
        """
        shape_str = shape.value if isinstance(shape, Shape) else str(shape).lower()
        resolution = Shape.get_resolution(shape_str)

        must_close_context = False
        if not self._context:
            await self.start()
            must_close_context = True

        page = await self._context.new_page()
        if self.network_logger:
            self.network_logger.attach_to_page(page)

        generation_result = None

        # Intercept response to capture generate API result
        async def on_response(response):
            nonlocal generation_result
            if "/api/generate" not in response.url:
                return
            try:
                data = await response.json()
                status = data.get("status")
                if status == "success" and data.get("imageDownloadUrl"):
                    generation_result = data
                elif status == "failed_verification":
                    raise VerificationFailedError(f"Verification failed: {data.get('reason')}")
            except Exception:
                pass

        page.on("response", on_response)

        # Route payload interception
        _current_seed = [first_seed]

        async def intercept_generate(route, request):
            if request.method == "POST":
                try:
                    body = json.loads(request.post_data) if request.post_data else {}
                    body["negativePrompt"] = negative_prompt
                    body["resolution"] = resolution
                    body["guidanceScale"] = guidance_scale
                    if _current_seed[0] >= 0:
                        body["seed"] = _current_seed[0]
                    await route.continue_(post_data=json.dumps(body))
                    return
                except Exception:
                    pass
            await route.continue_()

        await page.route("**/api/generate*", intercept_generate)

        try:
            await page.goto(self.generator_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(12000)

            generator_frame = None
            for frame in page.frames:
                furl = frame.url.lower()
                if frame != page.main_frame and "perchance.org" in furl:
                    try:
                        if await frame.query_selector("#generateButtonEl"):
                            generator_frame = frame
                            break
                    except Exception:
                        pass
            
            # Fallback if query_selector search didn't match immediately
            if not generator_frame:
                for frame in page.frames:
                    furl = frame.url.lower()
                    if frame != page.main_frame and "perchance.org" in furl:
                        generator_frame = frame
                        break

            if not generator_frame:
                raise IframeNotFoundError("Generator iframe not found on Perchance page")

            # Locate generate button (supports #generateButtonEl or button with "Generate" text)
            gen_btn_selector = None
            for sel in ["#generateButtonEl", 'button:has-text("Generate")', 'button:has-text("generate")', 'button']:
                try:
                    if await generator_frame.locator(sel).first.is_visible(timeout=2000):
                        gen_btn_selector = sel
                        break
                except Exception:
                    pass

            if not gen_btn_selector:
                raise IframeNotFoundError("Generate button not found in generator iframe")

            # Fill prompt into textarea / input
            for sel in ['textarea[data-name="description"]', '#promptInput', 'textarea', 'input[type="text"]']:
                try:
                    loc = generator_frame.locator(sel).first
                    if await loc.is_visible(timeout=1000):
                        await loc.fill(prompt)
                        break
                except Exception:
                    pass

            await page.wait_for_timeout(500)

            if style:
                try:
                    style_select = generator_frame.locator('select[data-name="artStyle"]').first
                    if await style_select.is_visible(timeout=1000):
                        options = await style_select.locator("option").all()
                        selected = False
                        for opt in options:
                            txt = await opt.text_content()
                            val = await opt.get_attribute("value")
                            if txt and style.lower() in txt.lower():
                                await style_select.select_option(value=val)
                                selected = True
                                break
                        if not selected:
                            await style_select.select_option(label=style)
                except Exception:
                    pass

            for img_index in range(count):
                _current_seed[0] = first_seed if img_index == 0 else -1
                generation_result = None

                # Capture existing image sources before clicking
                initial_img_srcs = set()
                try:
                    for img_el in await generator_frame.locator("img").all():
                        src = await img_el.get_attribute("src")
                        if src:
                            initial_img_srcs.add(src)
                except Exception:
                    pass

                await generator_frame.locator(gen_btn_selector).first.click()

                timed_out = True
                poll_count = int(self.timeout)
                detected_img_url = None

                for _ in range(poll_count):
                    await page.wait_for_timeout(1000)
                    if generation_result:
                        timed_out = False
                        break

                    # Check for updated <img> element src in generator frame
                    try:
                        for img_el in await generator_frame.locator("img").all():
                            src = await img_el.get_attribute("src")
                            if src and src not in initial_img_srcs and ("pollinations" in src or "blob:" in src or "data:image" in src or "http" in src):
                                detected_img_url = src
                                timed_out = False
                                break
                    except Exception:
                        pass

                    if not timed_out:
                        break

                if timed_out:
                    raise GenerationTimeoutError(
                        f"Image generation timed out ({self.timeout}s) for image {img_index + 1}/{count}"
                    )

                if generation_result:
                    raw_dl = generation_result.get("imageDownloadUrl", "")
                    if raw_dl.startswith("http://") or raw_dl.startswith("https://"):
                        dl_url = raw_dl
                    elif raw_dl.startswith("data:image"):
                        dl_url = raw_dl
                    elif raw_dl:
                        dl_url = "https://image-generation.perchance.org" + (raw_dl if raw_dl.startswith("/") else f"/{raw_dl}")
                    else:
                        dl_url = detected_img_url or ""
                    file_ext = generation_result.get("fileExtension", "jpeg")
                    actual_seed = generation_result.get("seed")
                    image_id = generation_result.get("imageId")
                else:
                    dl_url = detected_img_url or ""
                    file_ext = "jpeg"
                    actual_seed = random.randint(1000000, 999999999)
                    image_id = None

                if dl_url.startswith("data:image"):
                    header, b64_str = dl_url.split(",", 1)
                    img_bytes = base64.b64decode(b64_str)
                else:
                    img_data = await generator_frame.evaluate("""
                        async (url) => {
                            // 1. Try direct fetch of URL if valid
                            if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
                                try {
                                    const r = await fetch(url);
                                    if (r.ok) {
                                        const blob = await r.blob();
                                        const b64 = await new Promise(resolve => {
                                            const reader = new FileReader();
                                            reader.onloadend = () => resolve(reader.result.split(",")[1]);
                                            reader.readAsDataURL(blob);
                                        });
                                        return { ok: true, data: b64 };
                                    }
                                } catch (e) {
                                    console.warn('Direct fetch failed, falling back to DOM extraction:', e);
                                }
                            }

                            // 2. Fallback: extract directly from rendered <img> or <canvas> in DOM
                            try {
                                const imgs = Array.from(document.querySelectorAll('img'))
                                    .filter(img => img.src && (img.src.startsWith('data:') || img.src.startsWith('blob:') || img.src.startsWith('http')));
                                
                                for (const img of imgs.reverse()) {
                                    if (img.src.startsWith('data:image')) {
                                        return { ok: true, data: img.src.split(',')[1] };
                                    }
                                    try {
                                        const canvas = document.createElement('canvas');
                                        canvas.width = img.naturalWidth || img.width || 768;
                                        canvas.height = img.naturalHeight || img.height || 768;
                                        const ctx = canvas.getContext('2d');
                                        ctx.drawImage(img, 0, 0);
                                        const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
                                        if (dataUrl && dataUrl.includes(',')) {
                                            return { ok: true, data: dataUrl.split(',')[1] };
                                        }
                                    } catch (err) {}
                                }
                            } catch (e) {}

                            return { ok: false, status: 0, error: 'Extraction failed' };
                        }
                    """, dl_url)

                    if not img_data.get("ok"):
                        raise DownloadError(f"Image download failed: HTTP {img_data.get('status', 'ERR')} ({img_data.get('error', 'DNS/Network issue')})")

                    img_bytes = base64.b64decode(img_data["data"])
                result_obj = ImageResult(
                    image_bytes=img_bytes,
                    file_extension=file_ext,
                    seed=actual_seed,
                    prompt=prompt,
                    shape=shape_str,
                    guidance_scale=guidance_scale,
                    negative_prompt=negative_prompt,
                    style=style,
                    image_id=image_id,
                    download_url=dl_url
                )

                yield result_obj

                if img_index < count - 1:
                    await page.wait_for_timeout(1500)

        finally:
            await page.close()
            if must_close_context:
                await self.close()

class PerchanceGeneratorPool:
    """Manages a pool of parallel PerchanceGenerator workers for concurrent multi-image creation."""

    def __init__(self, workers: int = 2, **generator_kwargs):
        """Initialize worker pool.

        Args:
            workers: Maximum number of concurrent workers.
            **generator_kwargs: Keyword arguments passed to each PerchanceGenerator instance.
        """
        self.workers = workers
        self.generator_kwargs = generator_kwargs

    async def generate_parallel(
        self,
        prompts: List[str],
        shape: Union[str, Shape] = "square",
        negative_prompt: str = "",
        guidance_scale: float = 7.0,
        style: Optional[str] = None
    ) -> List[ImageResult]:
        """Generate images for multiple prompts concurrently across parallel workers.

        Args:
            prompts: List of prompt strings to generate.
            shape: Image shape ('square', 'landscape', 'portrait').
            negative_prompt: Elements to avoid.
            guidance_scale: Prompt guidance accuracy.
            style: Art style choice.

        Returns:
            List of ImageResult objects corresponding to the input prompts.
        """
        semaphore = asyncio.Semaphore(self.workers)

        async def _generate_task(prompt: str) -> ImageResult:
            async with semaphore:
                async with PerchanceGenerator(**self.generator_kwargs) as generator:
                    return await generator.generate(
                        prompt=prompt,
                        shape=shape,
                        negative_prompt=negative_prompt,
                        guidance_scale=guidance_scale,
                        style=style
                    )

        tasks = [_generate_task(p) for p in prompts]
        return await asyncio.gather(*tasks)
