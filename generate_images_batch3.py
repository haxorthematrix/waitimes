#!/usr/bin/env python3
"""Generate remaining ride images using DALL-E 3 - Batch 3."""

import os
import time
from pathlib import Path
import requests
from openai import OpenAI

# API key from environment variable
API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("Error: OPENAI_API_KEY environment variable not set")
    print("Set it with: export OPENAI_API_KEY='your-key-here'")
    exit(1)

# Image output directory
IMAGES_DIR = Path(__file__).parent / "assets" / "images"

# Remaining ride prompts
RIDES = [
    # Missing mapped rides
    ("remy", "Remy's Ratatouille Adventure at EPCOT France Pavilion, a whimsical oversized Parisian kitchen entrance with giant food props, Ratatouille theming, charming French bistro atmosphere, Disney photography"),

    ("little_mermaid", "Under the Sea Journey of The Little Mermaid at Magic Kingdom Fantasyland, a colorful seashell-shaped building with waterfalls, Ariel's grotto entrance, magical underwater theming, Disney photography"),

    ("tiana", "Tiana's Bayou Adventure at Magic Kingdom, a Louisiana bayou themed log flume entrance with Southern charm, Princess and the Frog theming, New Orleans jazz atmosphere, lush swamp scenery"),

    # New attractions
    ("zootopia", "Zootopia Better Zoogether at Disney's Animal Kingdom, a colorful modern city entrance with animal citizens, Zootopia movie theming, vibrant metropolis atmosphere, Disney photography"),

    ("gorilla_falls", "Gorilla Falls Exploration Trail at Disney's Animal Kingdom Africa, a lush African jungle path entrance, wildlife sanctuary theming, naturalistic safari atmosphere"),

    ("wildlife_express", "Wildlife Express Train at Disney's Animal Kingdom, a vintage African railway station with steam train, safari expedition theming, Harambe village atmosphere"),

    ("railroad", "Walt Disney World Railroad at Magic Kingdom, a beautiful Victorian-era train station on Main Street USA, classic steam locomotive, nostalgic Americana theming, golden hour lighting"),

    ("hall_presidents", "The Hall of Presidents at Magic Kingdom Liberty Square, a stately colonial brick building with white columns, American patriotic theming, historic atmosphere"),

    ("speedway", "Tomorrowland Speedway at Magic Kingdom, a colorful race track entrance with go-karts, retro-futuristic racing theming, family fun atmosphere"),

    ("carrousel", "Prince Charming Regal Carrousel at Magic Kingdom Fantasyland, a beautiful ornate golden carousel with white horses, classic Disney fairy tale theming, magical lighting"),

    # Character meet locations
    ("meet_mickey", "Meet Mickey at Town Square Theater Magic Kingdom, a charming Victorian theater entrance with Mickey Mouse marquee, classic Disney theming, Main Street USA atmosphere"),

    ("meet_princesses", "Princess Fairytale Hall at Magic Kingdom Fantasyland, an elegant castle interior with ornate decorations, royal princess theming, magical fairy tale atmosphere"),

    ("meet_anna_elsa", "Royal Sommerhus at EPCOT Norway Pavilion, a cozy Norwegian cabin with Frozen theming, Anna and Elsa meet location, warm Scandinavian atmosphere"),

    ("meet_characters", "Disney Character Meet and Greet location, a colorful themed photo spot with Disney decorations, magical meet location, whimsical Disney atmosphere"),
]


def generate_image(client, folder: str, prompt: str) -> bool:
    """Generate an image using DALL-E 3 and save it."""
    folder_path = IMAGES_DIR / folder
    folder_path.mkdir(parents=True, exist_ok=True)

    output_path = folder_path / "1.png"

    # Skip if image already exists
    if output_path.exists():
        print(f"  Skipping {folder} - image already exists")
        return True

    try:
        print(f"  Generating image for {folder}...")

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url

        # Download the image
        img_response = requests.get(image_url)
        img_response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(img_response.content)

        print(f"  ✓ Saved {folder}/1.png")
        return True

    except Exception as e:
        print(f"  ✗ Error generating {folder}: {e}")
        return False


def main():
    print("DALL-E 3 Ride Image Generator - Batch 3")
    print("=" * 50)

    client = OpenAI(api_key=API_KEY)

    success_count = 0
    fail_count = 0

    for folder, prompt in RIDES:
        success = generate_image(client, folder, prompt)
        if success:
            success_count += 1
        else:
            fail_count += 1

        # Rate limiting
        print("  Waiting 130 seconds for rate limit...")
        time.sleep(130)

    print()
    print("=" * 50)
    print(f"Complete: {success_count} succeeded, {fail_count} failed")


if __name__ == "__main__":
    main()
