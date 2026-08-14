import asyncio
import os
from perchance import PerchanceGenerator

async def main():
    prompt = "a majestic dragon flying over mountains, fantasy art"
    print(f"[*] Generating image with Network Logging enabled...")

    async with PerchanceGenerator(enable_network_logging=True) as generator:
        result = await generator.generate(prompt=prompt, shape="square")
        print(f"[+] Image generated! Seed: {result.seed}")
        
        output_image = os.path.join("examples", "output", f"dragon_{result.seed}.{result.file_extension}")
        result.save(output_image)

        # Export full Chrome network log
        output_log = os.path.join("examples", "output", "chrome_network_log.json")
        generator.network_logger.export_json(output_log)
        print(f"[+] Chrome Network Log exported to: {output_log}")

if __name__ == "__main__":
    asyncio.run(main())
