#!/usr/bin/env python
"""
Generate test letters for Elf-ETL.
Creates ~100 letters: 20 Grinch spam + 80 valid child letters.
Each file contains ONE letter from ONE child.
Uses batch processing with pauses to avoid rate limits.
"""
import os
import time
from dotenv import load_dotenv
from datapizza.clients.google import GoogleClient

load_dotenv()

OUTPUT_DIR = "data/test_letters"
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ GEMINI_API_KEY not set")
    exit(1)

client = GoogleClient(
    api_key=API_KEY,
    model="gemini-2.0-flash-exp"
)

VALID_COUNTRIES = ["italy", "usa", "china", "russia", "brazil", "australia"]
BATCH_SIZE = 5  # Letters per batch
BATCH_PAUSE = 30  # Seconds to wait between batches

def generate_valid_letter(index: int, country: str, goodness_level: str) -> str:
    prompt = f"""Write a realistic letter to Santa Claus from a child.
REQUIREMENTS:
- Child's name (first name only, realistic for {country.upper()})
- Child's age (between 4 and 14 years old)
- The child is from {country.upper()}
- Mention at least 1-3 specific gifts the child wants
- Include a story about behavior showing they are {goodness_level}
Write ONLY the letter text, nothing else."""
    response = client.invoke(prompt)
    return response.content[0].content if hasattr(response, 'content') else str(response)

def generate_grinch_letter(index: int) -> str:
    prompt = """Write a short mean-spirited letter pretending to be from a child but clearly from the Grinch.
Sign it as "Il Grinch", "The Grinch", or "Mr. Grinch".
Be angry, sarcastic, or threatening. Write ONLY the letter text."""
    response = client.invoke(prompt)
    return response.content[0].content if hasattr(response, 'content') else str(response)

def generate_unknown_country_letter(index: int) -> str:
    prompt = """Write a realistic letter to Santa from a child who lives in FRANCE, GERMANY, JAPAN, or CANADA.
Include: child's name, age (4-14), their country, 1-3 gift requests, and behavior story.
Write ONLY the letter text."""
    response = client.invoke(prompt)
    return response.content[0].content if hasattr(response, 'content') else str(response)

def process_batch(batch_num: int, items: list, generate_func, prefix: str, start_idx: int = 0):
    """Process a batch of letters with retry logic."""
    for i, item in enumerate(items):
        idx = start_idx + i
        try:
            if isinstance(item, tuple):  # For valid letters (country, goodness)
                country, goodness = item
                content = generate_func(idx, country, goodness)
                filename = f"{OUTPUT_DIR}/child_{country}_{idx:03d}.txt"
            else:  # For grinch or unknown
                content = generate_func(idx)
                filename = f"{OUTPUT_DIR}/{prefix}_{idx:03d}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  ✓ {os.path.basename(filename)}")
            time.sleep(2)  # Delay between individual calls
        except Exception as e:
            print(f"  ⚠ Error at {idx}: {e}")
            time.sleep(5)  # Extra wait on error

def main():
    print("🎄 Generating test letters with batch processing...")
    print(f"   Batch size: {BATCH_SIZE}, Pause between batches: {BATCH_PAUSE}s")
    
    # Check what already exists
    existing = set(os.listdir(OUTPUT_DIR)) if os.path.exists(OUTPUT_DIR) else set()
    print(f"   Found {len(existing)} existing files, will skip those\n")
    
    # 1. Generate Grinch letters (20 total, in batches)
    print("😈 Generating Grinch spam letters...")
    for batch_start in range(0, 20, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, 20)
        items_to_generate = []
        for i in range(batch_start, batch_end):
            if f"grinch_{i:03d}.txt" not in existing:
                items_to_generate.append(i)
        if items_to_generate:
            print(f"  Batch {batch_start//BATCH_SIZE + 1}: {len(items_to_generate)} letters")
            for idx in items_to_generate:
                process_batch(1, [None], lambda x: generate_grinch_letter(idx), "grinch", idx)
            if batch_end < 20:
                print(f"  Pausing {BATCH_PAUSE}s...")
                time.sleep(BATCH_PAUSE)
    
    # 2. Generate valid letters (72 total: 6 countries x 12 each)
    print("\n🎁 Generating valid child letters...")
    goodness_levels = ["very good", "somewhat good", "neutral", "somewhat naughty", "very naughty"]
    idx = 0
    batch_count = 0
    for country in VALID_COUNTRIES:
        for j in range(12):
            filename = f"child_{country}_{idx:03d}.txt"
            if filename not in existing:
                goodness = goodness_levels[j % len(goodness_levels)]
                try:
                    content = generate_valid_letter(idx, country, goodness)
                    with open(f"{OUTPUT_DIR}/{filename}", "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"  ✓ {filename} ({goodness})")
                except Exception as e:
                    print(f"  ⚠ Error: {e}")
                time.sleep(2)
                batch_count += 1
                if batch_count % BATCH_SIZE == 0:
                    print(f"  Pausing {BATCH_PAUSE}s...")
                    time.sleep(BATCH_PAUSE)
            idx += 1
    
    # 3. Generate unknown country letters (6 total)
    print("\n🌍 Generating unknown country letters...")
    for i in range(6):
        filename = f"child_unknown_{i:03d}.txt"
        if filename not in existing:
            try:
                content = generate_unknown_country_letter(i)
                with open(f"{OUTPUT_DIR}/{filename}", "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ⚠ Error: {e}")
            time.sleep(2)
    
    # Count what we have
    total = len(os.listdir(OUTPUT_DIR))
    print(f"\n✨ Done! {total} letters in {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
