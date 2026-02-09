#!/usr/bin/env python3
"""Generate park images using DALL-E 3 for closed park displays."""

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
IMAGES_DIR = Path(__file__).parent / "assets" / "images" / "parks"

# Park image prompts
PARKS = [
    ("magic_kingdom", "Cinderella Castle at Walt Disney World Magic Kingdom at night, the iconic castle lit up with purple and blue lights, fireworks in the sky, Main Street USA in foreground, magical Disney atmosphere, cinematic photography"),

    ("epcot", "Spaceship Earth geodesic sphere at EPCOT Walt Disney World at night, the iconic silver ball structure illuminated with colorful lights, fountain in foreground, futuristic atmosphere, dramatic photography"),

    ("hollywood_studios", "The Hollywood Tower Hotel at Disney's Hollywood Studios at dusk, the imposing art deco tower lit dramatically against a purple sky, palm trees silhouetted, classic Hollywood golden age atmosphere"),

    ("animal_kingdom", "Tree of Life at Disney's Animal Kingdom at twilight, the massive iconic tree with intricate animal carvings illuminated from within, glowing warmly against a darkening sky, magical nature atmosphere"),
]


def generate_image(client, name: str, prompt: str) -> bool:
    """Generate an image using DALL-E 3 and save it."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = IMAGES_DIR / f"{name}.png"

    # Skip if image already exists
    if output_path.exists():
        print(f"  Skipping {name} - image already exists")
        return True

    try:
        print(f"  Generating image for {name}...")

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

        print(f"  ✓ Saved parks/{name}.png")
        return True

    except Exception as e:
        print(f"  ✗ Error generating {name}: {e}")
        return False


def main():
    print("DALL-E 3 Park Image Generator")
    print("=" * 50)

    client = OpenAI(api_key=API_KEY)

    success_count = 0
    fail_count = 0

    for name, prompt in PARKS:
        success = generate_image(client, name, prompt)
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
