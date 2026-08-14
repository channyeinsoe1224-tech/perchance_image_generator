import asyncio
import os
from perchance import PerchanceGenerator

async def main():
    prompt = "a cute astronaut cat in space, digital art, high quality"
    print(f"[*] Generating image for prompt: '{prompt}'...")

    async with PerchanceGenerator() as generator:
        result = await generator.generate(
            prompt=prompt,
            shape="square",
            negative_prompt="blurry, low quality"
        )
        print(f"[+] Success! Generated image:")
        print(f"    - Seed: {result.seed}")
        print(f"    - Format: {result.file_extension}")
        print(f"    - Size: {result.size_bytes} bytes")

        output_path = os.path.join("examples", "output", f"cat_astronaut_{result.seed}.{result.file_extension}")
        result.save(output_path)
        print(f"[+] Saved image to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
