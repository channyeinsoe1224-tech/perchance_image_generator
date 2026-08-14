import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from perchance import PerchanceGenerator

async def main():
    profile_dir = os.path.abspath(os.path.join("scratch", "chrome_user_profile"))
    print(f"[*] Launching generator with persistent Chrome profile at: {profile_dir}")

    # Using user_data_dir preserves cookies, Cloudflare tokens, and localStorage across sessions
    async with PerchanceGenerator(user_data_dir=profile_dir) as generator:
        result = await generator.generate(
            prompt="a serene futuristic greenhouse with glowing plants, 8k",
            shape="square"
        )
        print(f"[+] Success! Generated image with persistent profile (Seed: {result.seed})")
        
        output_path = os.path.join("scratch", f"persistent_profile_{result.seed}.{result.file_extension}")
        result.save(output_path)
        print(f"[+] Saved image to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
