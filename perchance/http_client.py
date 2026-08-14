"""Version 2: Chrome-headless Perchance client using iframe interaction (no visible window)."""

import os
import json
import base64
import asyncio
import random
from typing import AsyncGenerator, List, Optional, Union

from playwright.async_api import async_playwright, BrowserContext, Page, Frame

from .models import ImageResult, Shape
from .exceptions import (
    PerchanceError,
    GenerationTimeoutError,
    IframeNotFoundError,
    VerificationFailedError,
    DownloadError
)

GENERATOR_PAGE_URL = "https://perchance.org/ai-text-to-image-generator"


class PerchanceHTTPGenerator:
    """Version 2 Async Client for Perchance AI Image Generation.

    Operates in fully headless mode using the user's installed Chrome
    (channel='chrome') which has a legitimate TLS fingerprint that passes
    Cloudflare bot detection. No visible Chrome window is opened.

    Uses the same iframe-interaction approach as V1 but without any UI.

    Example:
        ```python
        async with PerchanceHTTPGenerator() as generator:
            image = await generator.generate("a glowing neon cybernetic tiger")
            image.save("tiger.jpeg")
        ```
    """

    def __init__(
        self,
        generator_url: str = GENERATOR_PAGE_URL,
        timeout: float = 90.0,
        user_agent: Optional[str] = None,
        channel: str = "chrome",
    ):
        """Initialize the PerchanceHTTPGenerator client.

        Args:
            generator_url: URL of the Perchance generator page.
            timeout: Maximum timeout in seconds for image generation.
            user_agent: Optional custom User-Agent string.
            channel: Browser channel to use. 'chrome' uses your installed Chrome
                     (recommended for Cloudflare bypass). 'chromium' uses the
                     Playwright-bundled Chromium (may fail bot detection).
        """
        self.generator_url = generator_url
        self.timeout = timeout
        self.user_agent = user_agent
        self.channel = channel
        self._pw = None
        self._browser = None
        self._context: Optional[BrowserContext] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Initialize headless Chrome context."""
        if self._context:
            return

        self._pw = await async_playwright().start()

        launch_kwargs = dict(
            headless=True,
            args=[
                "--headless=new",
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-infobars",
            ],
        )
        if self.channel != "chromium":
            launch_kwargs["channel"] = self.channel

        self._browser = await self._pw.chromium.launch(**launch_kwargs)

        ua = self.user_agent or (
            f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{self._browser.version} Safari/537.36"
        )

        self._context = await self._browser.new_context(
            user_agent=ua,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )

        # Stealth patches applied to every page/frame
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

    async def close(self):
        """Close browser context and release resources."""
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._pw:
            try:
                await self._pw.stop()
            except Exception:
                pass
            self._pw = None

    async def _find_generator_frame(self, page: Page) -> Frame:
        """Find the perchance subdomain iframe that hosts the generator UI."""
        # Wait up to 15s for the iframe to appear
        for _ in range(15):
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                furl = frame.url.lower()
                if "perchance.org" in furl and frame.url != "about:blank":
                    # Confirm it has the generate button
                    try:
                        if await frame.query_selector("#generateButtonEl"):
                            return frame
                    except Exception:
                        pass
            await asyncio.sleep(1)

        # Fallback: return any non-main perchance frame
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            if "perchance.org" in frame.url.lower() and frame.url != "about:blank":
                return frame

        raise IframeNotFoundError(
            "Generator iframe not found on Perchance page. "
            "The page structure may have changed."
        )

    async def generate(
        self,
        prompt: str,
        shape: Union[str, Shape] = "square",
        negative_prompt: str = "",
        guidance_scale: float = 7.0,
        seed: int = -1,
        style: Optional[str] = None,
    ) -> ImageResult:
        """Generate a single image using Version 2 headless Chrome client.

        Args:
            prompt: Image description.
            shape: Image shape ('square', 'landscape', 'portrait').
            negative_prompt: Elements to avoid.
            guidance_scale: Prompt accuracy scale (1.0 to 30.0).
            seed: Generation seed (-1 for random).
            style: Art style.

        Returns:
            ImageResult object.
        """
        async for result in self.generate_batch(
            prompt=prompt,
            count=1,
            shape=shape,
            negative_prompt=negative_prompt,
            guidance_scale=guidance_scale,
            first_seed=seed,
            style=style,
        ):
            return result
        raise PerchanceError("V2 generation failed")

    async def generate_batch(
        self,
        prompt: str,
        count: int = 1,
        shape: Union[str, Shape] = "square",
        negative_prompt: str = "",
        guidance_scale: float = 7.0,
        first_seed: int = -1,
        style: Optional[str] = None,
    ) -> AsyncGenerator[ImageResult, None]:
        """Generate multiple images in a single headless Chrome session.

        Yields:
            ImageResult objects as generated.
        """
        if not self._context:
            await self.start()

        shape_str = shape.value if isinstance(shape, Shape) else str(shape).lower()
        resolution = Shape.get_resolution(shape_str)

        page = await self._context.new_page()

        generation_result = None

        # Intercept /api/generate response to capture image data
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
                    raise VerificationFailedError(
                        f"Verification failed: {data.get('reason')}"
                    )
            except VerificationFailedError:
                raise
            except Exception:
                pass

        page.on("response", on_response)

        # Intercept /api/generate POST to inject our parameters
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
            # Load the generator page
            await page.goto(
                self.generator_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Wait for the page JS to fully initialize (same as V1's 12s wait)
            await page.wait_for_timeout(12000)

            # Find the generator iframe
            generator_frame = await self._find_generator_frame(page)

            # Fill in the prompt
            full_prompt = f"{prompt}, {style} style" if style else prompt
            for sel in [
                'textarea[data-name="description"]',
                "#promptInput",
                "textarea",
                'input[type="text"]',
            ]:
                try:
                    loc = generator_frame.locator(sel).first
                    if await loc.is_visible(timeout=1000):
                        await loc.fill(full_prompt)
                        break
                except Exception:
                    pass

            # Set art style if specified
            if style:
                try:
                    style_select = generator_frame.locator(
                        'select[data-name="artStyle"]'
                    ).first
                    if await style_select.is_visible(timeout=1000):
                        options = await style_select.locator("option").all()
                        for opt in options:
                            txt = await opt.text_content()
                            val = await opt.get_attribute("value")
                            if txt and style.lower() in txt.lower():
                                await style_select.select_option(value=val)
                                break
                except Exception:
                    pass

            # Generate images one by one
            for img_index in range(count):
                _current_seed[0] = first_seed if img_index == 0 else -1
                generation_result = None

                # Capture current image sources to detect new ones
                initial_img_srcs = set()
                try:
                    imgs = await generator_frame.query_selector_all("img")
                    for img in imgs:
                        src = await img.get_attribute("src")
                        if src:
                            initial_img_srcs.add(src)
                except Exception:
                    pass

                # Click the generate button
                gen_btn_selector = None
                for sel in [
                    "#generateButtonEl",
                    'button:has-text("Generate")',
                    "button",
                ]:
                    try:
                        if await generator_frame.locator(sel).first.is_visible(
                            timeout=2000
                        ):
                            gen_btn_selector = sel
                            break
                    except Exception:
                        pass

                if not gen_btn_selector:
                    raise IframeNotFoundError(
                        "Generate button not found in generator iframe"
                    )

                await generator_frame.locator(gen_btn_selector).first.click()

                # Wait for generation result (up to timeout seconds)
                deadline = asyncio.get_event_loop().time() + self.timeout
                while asyncio.get_event_loop().time() < deadline:
                    if generation_result:
                        break
                    await asyncio.sleep(0.5)

                if not generation_result:
                    raise GenerationTimeoutError(
                        f"Image generation timed out after {self.timeout}s"
                    )

                data = generation_result
                dl_path = data["imageDownloadUrl"]
                dl_url = "https://image-generation.perchance.org" + dl_path
                file_ext = data.get("fileExtension", "jpeg")
                actual_seed = data.get("seed", _current_seed[0])
                image_id = data.get("imageId")

                # Download the image via fetch in-page (avoids CORS)
                dl_script = """
                    async (url) => {
                        const r = await fetch(url);
                        if (!r.ok) return { ok: false, status: r.status };
                        const blob = await r.blob();
                        const b64 = await new Promise(resolve => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result.split(',')[1]);
                            reader.readAsDataURL(blob);
                        });
                        return { ok: true, data: b64 };
                    }
                """
                dl_res = await page.evaluate(dl_script, dl_url)

                if not dl_res.get("ok"):
                    raise DownloadError(
                        f"Failed to download image: HTTP {dl_res.get('status')}"
                    )

                img_bytes = base64.b64decode(dl_res["data"])

                yield ImageResult(
                    image_bytes=img_bytes,
                    file_extension=file_ext,
                    seed=actual_seed,
                    prompt=prompt,
                    shape=shape_str,
                    guidance_scale=guidance_scale,
                    negative_prompt=negative_prompt,
                    style=style,
                    image_id=image_id,
                    download_url=dl_url,
                )

                if img_index < count - 1:
                    await asyncio.sleep(1.0)

        finally:
            try:
                await page.close()
            except Exception:
                pass
