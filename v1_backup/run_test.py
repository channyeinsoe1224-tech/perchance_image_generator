"""Root test launcher for perchance image generator library."""

import asyncio
import os
from perchance import PerchanceGenerator

async def run_test():
    prompt = "a vibrant neon hummingbird in flight, hyperrealistic, 8k"
    print(f"[*] Running library test generation with prompt: '{prompt}'...")

    async with PerchanceGenerator() as generator:
        result = await generator.generate(
            prompt=prompt,
            shape="square",
            negative_prompt="blurry, watermark"
        )
        print(f"[+] Success! Generated image:")
        print(f"    - Seed: {result.seed}")
        print(f"    - Extension: {result.file_extension}")
        print(f"    - Size: {result.size_bytes} bytes")
        
        output_path = os.path.join("scratch", f"test_hummingbird_{result.seed}.{result.file_extension}")
        result.save(output_path)
        print(f"[+] Saved test image to {output_path}")

if __name__ == "__main__":
    asyncio.run(run_test())
