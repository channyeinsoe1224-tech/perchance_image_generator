import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from perchance import PerchanceGeneratorPool

async def main():
    prompts = [
        "a cybernetic wolf in a neon snowstorm, 8k",
        "a cute baby dragon sleeping on gold coins, 8k"
    ]
    print(f"[*] Starting Multi-Creator Pool with {len(prompts)} parallel workers...")

    # Create worker pool with 2 parallel workers
    pool = PerchanceGeneratorPool(workers=2)
    results = await pool.generate_parallel(
        prompts=prompts,
        shape="square",
        style="Digital Painting"
    )

    for idx, (prompt, result) in enumerate(zip(prompts, results), 1):
        print(f"[+] Worker {idx} done! Prompt: '{prompt[:30]}...' -> Seed: {result.seed}")
        out_path = os.path.join("scratch", f"multi_creator_{idx}_{result.seed}.{result.file_extension}")
        result.save(out_path)
        print(f"    Saved image to: {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
