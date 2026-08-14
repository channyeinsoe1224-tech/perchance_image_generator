"""Root test script for Perchance Image Generator Version 2 (Chrome-less / Direct HTTP API)."""

import asyncio
import os
import time
from perchance import PerchanceHTTPGenerator, Shape

async def main():
    print("=" * 60)
    print("  PERCHANCE IMAGE GENERATOR - VERSION 2 (CHROME-LESS TEST)")
    print("=" * 60)

    prompt = "a serene cyberpunk temple surrounded by cherry blossoms at midnight, 8k resolution"
    print(f"\n[Prompt]: '{prompt}'")
    print("[Engine]: Version 2 PerchanceHTTPGenerator (Direct API / Headless Background)")

    output_dir = "v2_test_output"
    os.makedirs(output_dir, exist_ok=True)

    start_time = time.time()
    
    async with PerchanceHTTPGenerator() as generator:
        print("\n--> Generating image via V2 direct API...")
        result = await generator.generate(
            prompt=prompt,
            shape=Shape.LANDSCAPE,
            style="Digital Painting",
            seed=42
        )

        elapsed = time.time() - start_time
        filename = f"{output_dir}/v2_cyberpunk_temple.{result.file_extension}"
        result.save(filename)

        print("\n" + "=" * 60)
        print("  GENERATION SUCCESSFUL!")
        print("=" * 60)
        print(f" Saved to        : {filename}")
        print(f" File Size       : {len(result.image_bytes)} bytes")
        print(f" Image ID        : {result.image_id}")
        print(f" Seed            : {result.seed}")
        print(f" Resolution      : {result.shape}")
        print(f" Download URL    : {result.download_url}")
        print(f" Time Taken      : {elapsed:.2f} seconds")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
