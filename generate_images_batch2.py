#!/usr/bin/env python3
"""Generate realistic ride images using DALL-E 3 - Batch 2 (additional rides)."""

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

# Additional ride prompts
RIDES = [
    # Magic Kingdom additions
    ("buzz_lightyear", "Buzz Lightyear's Space Ranger Spin at Walt Disney World Magic Kingdom, a colorful sci-fi themed entrance with Buzz Lightyear statue, neon space blasters, retro-futuristic Tomorrowland aesthetic, theme park photography"),

    ("dumbo", "Dumbo the Flying Elephant ride at Walt Disney World Magic Kingdom, the iconic circus-themed spinning ride with colorful Dumbo elephants, big top tent theming, whimsical carnival atmosphere, daytime theme park photography"),

    ("winnie_pooh", "The Many Adventures of Winnie the Pooh at Walt Disney World Magic Kingdom, a charming honey pot themed entrance in Hundred Acre Wood style, storybook aesthetic with Pooh characters, warm golden tones, whimsical photography"),

    ("mad_tea_party", "Mad Tea Party teacups ride at Walt Disney World Magic Kingdom, colorful oversized teacups under a festive canopy, Alice in Wonderland theming with playing card decorations, whimsical fantasy atmosphere"),

    ("country_bear", "Country Bear Musical Jamboree at Walt Disney World Magic Kingdom, a rustic frontier saloon entrance with wooden facade, country western theming, warm lantern lighting, Frontierland atmosphere"),

    ("carousel_progress", "Walt Disney's Carousel of Progress at Magic Kingdom Tomorrowland, the iconic rotating theater building with mid-century modern design, classic Tomorrowland architecture, retro-futuristic aesthetic"),

    ("peoplemover", "Tomorrowland Transit Authority PeopleMover at Walt Disney World Magic Kingdom, sleek elevated track with blue tram cars gliding through Tomorrowland, futuristic city transportation aesthetic, dramatic lighting"),

    ("astro_orbiter", "Astro Orbiter at Walt Disney World Magic Kingdom Tomorrowland, a towering rocket ship ride atop the elevated platform, retro space age design with orbiting rockets, dramatic nighttime lighting with stars"),

    ("barnstormer", "The Barnstormer at Walt Disney World Magic Kingdom, a colorful vintage airplane themed coaster, Goofy's circus pilot aesthetic, whimsical cartoon biplane theming, family fun atmosphere"),

    ("magic_carpets", "The Magic Carpets of Aladdin at Walt Disney World Magic Kingdom Adventureland, flying carpet ride with Arabian Nights theming, golden domes and minarets, jewel-toned decorations, exotic marketplace atmosphere"),

    ("monsters_inc", "Monsters Inc. Laugh Floor at Walt Disney World Magic Kingdom Tomorrowland, a colorful monster-themed comedy club entrance, Monsters Inc doors and characters, fun and playful Pixar theming"),

    ("philharmagic", "Mickey's PhilharMagic at Walt Disney World Magic Kingdom Fantasyland, an ornate concert hall entrance with golden musical motifs, classic Disney animation style, magical orchestra theming"),

    ("tiki_room", "Walt Disney's Enchanted Tiki Room at Magic Kingdom Adventureland, a tropical Polynesian hut with tiki torches and carved tikis, lush jungle entrance, exotic Hawaiian theming, warm tropical atmosphere"),

    # EPCOT additions
    ("soarin", "Soarin' Around the World at EPCOT, the majestic hangar-style building in The Land pavilion, aircraft wing themed entrance, inspirational world travel aesthetic, dramatic EPCOT architecture"),

    ("living_land", "Living with the Land boat ride at EPCOT The Land pavilion, a greenhouse and agricultural themed attraction, lush greenery and hydroponic gardens visible, educational nature aesthetic"),

    ("figment", "Journey Into Imagination With Figment at EPCOT, the iconic glass pyramid Imagination Pavilion with rainbow design elements, playful purple dragon Figment character theming, creative and whimsical architecture"),

    ("mission_space", "Mission: SPACE at EPCOT, a massive rotating space station themed building, orange and white NASA-inspired exterior, dramatic space exploration theming, futuristic astronaut aesthetic"),

    ("seas_nemo", "The Seas with Nemo & Friends at EPCOT, the massive aquarium pavilion with wave-shaped roof, Finding Nemo underwater theming, blue ocean colors, marine life discovery atmosphere"),

    ("journey_water", "Journey of Water Inspired by Moana at EPCOT, a beautiful tropical water exploration trail, Polynesian aesthetic with volcanic rock and lush plants, magical glowing water features, Moana theming"),

    ("gran_fiesta", "Gran Fiesta Tour Starring The Three Caballeros at EPCOT Mexico Pavilion, a Mayan pyramid interior with festive Mexican marketplace, colorful papel picado decorations, warm golden lighting"),

    # Hollywood Studios additions
    ("alien_saucers", "Alien Swirling Saucers at Disney's Hollywood Studios Toy Story Land, colorful spinning flying saucer ride, oversized toy aesthetic with Pizza Planet aliens, playful neon lighting, Pixar theming"),

    ("indiana_jones", "Indiana Jones Epic Stunt Spectacular at Disney's Hollywood Studios, a massive desert archaeological dig set, adventure movie theming with ancient ruins and props, dramatic action movie atmosphere"),

    # Animal Kingdom additions
    ("kali_river", "Kali River Rapids at Disney's Animal Kingdom Asia, a whitewater rafting adventure entrance, lush Asian rainforest theming, bamboo and temple architecture, rushing river atmosphere"),

    ("lion_king", "Festival of the Lion King at Disney's Animal Kingdom Africa, a vibrant African celebration theater entrance, colorful tribal decorations, Pride Rock inspired architecture, celebratory atmosphere"),

    ("finding_nemo_show", "Finding Nemo: The Big Blue and Beyond at Disney's Animal Kingdom, a colorful underwater theater entrance, deep blue ocean theming, Finding Nemo puppetry show aesthetic"),

    # Additional iconic rides from batch 1 that might have been missed
    ("big_thunder", "Big Thunder Mountain Railroad at Walt Disney World Magic Kingdom, a rugged red rock desert mountain with abandoned mining town, wild west gold rush theming, dramatic sunset lighting"),

    ("seven_dwarfs", "Seven Dwarfs Mine Train at Walt Disney World Magic Kingdom, a charming mine entrance with glowing gems and dwarf cottage, Snow White fairy tale theming, enchanted forest atmosphere"),

    ("small_world", "it's a small world at Walt Disney World Magic Kingdom, the iconic white and gold facade with clock tower, whimsical international children theming, pastel colors and festive decorations"),

    ("peter_pan", "Peter Pan's Flight at Walt Disney World Magic Kingdom Fantasyland, an enchanting London cityscape entrance, Neverland pirate ship theming, magical starlit sky atmosphere"),

    ("kilimanjaro", "Kilimanjaro Safaris at Disney's Animal Kingdom Africa, a rugged safari vehicle loading area, authentic African savanna theming, Harambe village architecture, wildlife expedition atmosphere"),
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
    print("DALL-E 3 Ride Image Generator - Batch 2")
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
