"""Example: Quickstart for Perchance Image Generator Version 2 (Chrome-less / Direct HTTP API)."""

import asyncio
from perchance import PerchanceHTTPGenerator, Shape

async def main():
    print("Initializing Version 2 Chromeless Perchance Client...")
    
    async with PerchanceHTTPGenerator() as generator:
        print("Generating image...")
        image = await generator.generate(
            prompt="an ultra detailed majestic owl in a mystical enchanted forest, 8k",
            shape=Shape.SQUARE,
            style="Cinematic"
        )
        
        output_file = "v2_mystical_owl.jpeg"
        image.save(output_file)
        print(f"Done! Image saved to {output_file}")
        print(f"Seed: {image.seed}, Image ID: {image.image_id}")

if __name__ == "__main__":
    asyncio.run(main())
