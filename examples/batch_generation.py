import asyncio
import os
from perchance import PerchanceGenerator

async def main():
    prompt = "a serene cyberpunk temple surrounded by cherry blossoms, 8k"
    count = 2
    print(f"[*] Generating {count} images in 1 session for prompt: '{prompt}'...")

    async with PerchanceGenerator() as generator:
        idx = 1
        async for result in generator.generate_batch(
            prompt=prompt,
            count=count,
            shape="landscape"
        ):
            print(f"[+] Image {idx}/{count} generated! Seed: {result.seed}")
            out_file = os.path.join("examples", "output", f"cyberpunk_temple_{idx}_{result.seed}.{result.file_extension}")
            result.save(out_file)
            print(f"    Saved to: {out_file}")
            idx += 1

if __name__ == "__main__":
    asyncio.run(main())
