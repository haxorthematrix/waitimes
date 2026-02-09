#!/usr/bin/env python3
"""Generate realistic ride images using DALL-E 3."""

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

# Ride prompts - detailed descriptions for DALL-E 3
RIDES = [
    ("tower_terror", "The Hollywood Tower Hotel at Disney's Hollywood Studios at dusk, an imposing 13-story art deco hotel tower with a haunted abandoned look, Spanish Colonial Revival architecture, overgrown vines, broken windows, eerie purple lightning in the background, dramatic photography style"),

    ("rock_roller", "Rock 'n' Roller Coaster entrance at Disney Hollywood Studios, a giant red electric guitar with neon lights, rock and roll themed facade, purple and blue neon signs, dramatic nighttime lighting, theme park photography"),

    ("space_mountain", "Space Mountain at Walt Disney World Magic Kingdom, the iconic white futuristic dome structure at night with dramatic blue and purple lighting, stars visible in the sky, cinematic theme park photography"),

    ("haunted_mansion", "The Haunted Mansion at Walt Disney World Magic Kingdom, a stately antebellum manor house in Liberty Square, dark and foreboding atmosphere, wrought iron gates, dead trees, full moon in background, gothic architecture, theme park photography"),

    ("millennium_falcon", "Millennium Falcon Smugglers Run at Disney's Galaxy's Edge, the iconic Star Wars spaceship docked at a spaceport, detailed weathered hull, atmospheric lighting, steam and fog, cinematic sci-fi photography"),

    ("rise_resistance", "Star Wars Rise of the Resistance at Disney's Galaxy's Edge, a massive First Order Star Destroyer hangar interior, stormtroopers in formation, red and black Imperial aesthetics, dramatic cinematic lighting"),

    ("slinky_dog", "Slinky Dog Dash roller coaster at Disney's Toy Story Land, a giant colorful Slinky Dog coaster train on bright red and yellow tracks, oversized toy blocks and building sets in background, playful daytime theme park photography"),

    ("flight_passage", "Avatar Flight of Passage at Disney's Animal Kingdom Pandora, bioluminescent alien jungle landscape, floating mountains in background, glowing plants in purple and blue colors, ethereal Na'vi atmosphere, cinematic fantasy photography"),

    ("guardians_galaxy", "Guardians of the Galaxy Cosmic Rewind at EPCOT, the sleek modern building with the Guardians ship crashed into it, dramatic sunset lighting, futuristic architecture, Marvel theme park photography"),

    ("frozen", "Frozen Ever After ride at EPCOT Norway pavilion, the Arendelle castle with snowy Norwegian fjord scenery, northern lights in the sky, winter wonderland atmosphere, magical Disney photography"),

    ("pirates_caribbean", "Pirates of the Caribbean at Walt Disney World Magic Kingdom, a Spanish colonial fortress entrance at night, torchlight, skull and crossbones, Caribbean atmosphere, adventure themed photography"),

    ("jungle_cruise", "Jungle Cruise at Walt Disney World Magic Kingdom, a vintage 1930s expedition boat house, tropical jungle vegetation, adventure signage, golden afternoon light, adventureland atmosphere"),

    ("spaceship_earth", "Spaceship Earth at EPCOT Walt Disney World, the iconic geodesic sphere at twilight, dramatic purple and blue lighting on the triangular panels, fountain in foreground, futuristic Disney photography"),

    ("test_track", "Test Track at EPCOT, a sleek modern automotive testing facility with blue neon accents, futuristic vehicle design aesthetic, dramatic nighttime lighting, technology themed photography"),

    ("everest", "Expedition Everest at Disney's Animal Kingdom, the massive snow-capped mountain with the abandoned railway winding through it, Himalayan village at the base, dramatic cloudy sky, adventure photography"),

    ("navi_river", "Na'vi River Journey at Disney's Animal Kingdom Pandora, a glowing bioluminescent river cave, ethereal alien plants in purple blue and pink, the Shaman of Songs animatronic, magical atmosphere photography"),

    ("star_tours", "Star Tours The Adventures Continue at Disney's Hollywood Studios, a retro-futuristic spaceport terminal, Star Wars droids and signage, sleek spacecraft visible, cinematic sci-fi theme park photography"),

    ("toy_story", "Toy Story Mania at Disney's Hollywood Studios, a giant colorful carnival midway entrance, oversized toys and games, bright playful colors, whimsical theme park photography"),

    ("runaway_railway", "Mickey and Minnie's Runaway Railway at Disney's Hollywood Studios, the Chinese Theatre facade with art deco Mickey Mouse poster, classic Hollywood golden age aesthetic, dramatic nighttime lighting"),

    ("tron", "TRON Lightcycle Run at Walt Disney World Magic Kingdom, the futuristic canopy structure glowing with blue and white light grid patterns, sleek motorcycle coaster vehicles, dramatic nighttime cyberpunk aesthetic"),
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

        print(f"  ✓ Saved {folder}/1.jpg")
        return True

    except Exception as e:
        print(f"  ✗ Error generating {folder}: {e}")
        return False


def main():
    print("DALL-E 3 Ride Image Generator")
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

        # Rate limiting - wait 130 seconds due to strict rate limit
        print("  Waiting 130 seconds for rate limit...")
        time.sleep(130)

    print()
    print("=" * 50)
    print(f"Complete: {success_count} succeeded, {fail_count} failed")


if __name__ == "__main__":
    main()
