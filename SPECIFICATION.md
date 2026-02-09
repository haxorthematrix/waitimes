# Disney World Wait Times Display

## Project Overview

A dedicated display application that shows real-time wait times for Walt Disney World attractions. The display rotates through rides, showing each with a full-screen themed image, stylized typography, and current wait information in an overlay.

**Target Hardware:** Raspberry Pi + Official 7" Touchscreen Display (800x480 pixels)
**Development Language:** Python
**Development Environment:** Local (macOS), deployment to Pi at 192.168.10.25
**Mode:** Fully automated "set it and forget it" - no touch interaction required

---

## Current Status

### Completed
- [x] Phase 1: Core Infrastructure (API client, data models, caching)
- [x] Phase 2: Display Engine (pygame rendering, rotation, crossfade transitions)
- [x] Phase 3: Theming (10 custom fonts, color schemes, image management)
- [x] Phase 4: Polish & Error Handling (logging, stale data warnings, graceful degradation)
- [x] Ride mappings for 60+ attractions across all 4 parks

### In Progress
- [ ] DALL-E 3 image generation (20/51 rides complete)

### Pending
- [ ] Phase 5: Pi Deployment
- [ ] Phase 6: Park hours awareness / nighttime mode

---

## Display Specifications

### Screen Dimensions
- **Resolution:** 800 x 480 pixels
- **Aspect Ratio:** 5:3
- **Orientation:** Landscape

### Layout Design (Full-Screen with Overlay)

```
+-----------------------------------------------------------------------+
|                                                                       |
|                     [Full-Screen Ride Image]                          |
|                         (800 x 480)                                   |
|                                                                       |
|   +---------------------------------------------------------------+   |
|   |                                                               |   |
|   |   SPACE MOUNTAIN                          [Themed Font]       |   |
|   |                                                               |   |
|   |   25 min                                  [Wait Time]         |   |
|   |                                                               |   |
|   |   Magic Kingdom                           [Park Name]         |   |
|   |                                                               |   |
|   +---------------------------------------------------------------+   |
|                          [Semi-transparent overlay box]               |
|                                                                       |
|                    o o o * o o o o o o o o                            |
|                      [Ride indicator dots]                            |
+-----------------------------------------------------------------------+
```

---

## Data Source

### Queue-Times.com API
- **Base URL:** `https://queue-times.com/parks/{park_id}/queue_times.json`
- **Walt Disney World Park IDs:**
  - Magic Kingdom: `6`
  - EPCOT: `5`
  - Hollywood Studios: `7`
  - Animal Kingdom: `8`

### API Configuration
- **Refresh Interval:** Every 5 minutes (300 seconds)
- **Caching:** Store last successful response; display cached data if API fails
- **Retry Logic:** On failure, wait 30 seconds before retry; max 3 retries
- **Stale Data Warning:** Visual indicator when data is >15 minutes old

---

## Ride Rotation

### Timing
- **Display Duration:** 8 seconds per ride
- **Transition:** Smooth crossfade (0.5 seconds)
- **Image Cycling:** Images rotate only after completing a full round of all rides

### Filtering
- Only show rides that are currently operating
- Only show rides with wait time data > 0
- Configurable per-park filtering

---

## Typography

### Themed Fonts (10 fonts installed)

| Theme | Font | Used For |
|-------|------|----------|
| scifi | Orbitron | Space Mountain, TRON, Buzz Lightyear, Guardians, Test Track |
| spooky | Creepster | Haunted Mansion, Tower of Terror |
| pirate | Pirata One | Pirates of the Caribbean |
| adventure | Rye | Jungle Cruise, Everest, Safari, Indiana Jones, Big Thunder |
| whimsical | Fredoka One | Small World, Winnie the Pooh, Figment, Remy |
| playful | Luckiest Guy | Toy Story, Slinky Dog, Dumbo, Runaway Railway, Monsters Inc |
| action | Bangers | Rock 'n' Roller Coaster |
| fantasy | Cinzel | Seven Dwarfs, Peter Pan, Frozen, Little Mermaid |
| future | Exo2 | Spaceship Earth, PeopleMover, Carousel of Progress |
| starwars | Audiowide | Rise of the Resistance, Millennium Falcon, Star Tours |
| avatar | Exo2 | Flight of Passage, Na'vi River Journey |
| classic | Cinzel | Default/fallback |

### Font Sizes
- **Ride Name:** 42px
- **Wait Time:** 72px
- **Park Name:** 28px

---

## Imagery

### Image Generation
- **Method:** DALL-E 3 API (OpenAI)
- **Resolution:** 1792 x 1024 (scaled to 800 x 480 for display)
- **Quality:** Standard
- **Style:** Photorealistic theme park photography

### Image Storage
```
assets/images/
├── space_mountain/1.png
├── haunted_mansion/1.png
├── tower_terror/1.png
└── ... (one folder per ride)
```

### Covered Attractions (60+ rides)

**Magic Kingdom (25 rides):**
Space Mountain, Haunted Mansion, Pirates of the Caribbean, Jungle Cruise, Big Thunder Mountain, Seven Dwarfs Mine Train, It's a Small World, Peter Pan's Flight, TRON Lightcycle Run, Tiana's Bayou Adventure, Buzz Lightyear, Dumbo, Winnie the Pooh, Mad Tea Party, Country Bear Jamboree, Carousel of Progress, PeopleMover, Little Mermaid, Astro Orbiter, Barnstormer, Magic Carpets, Monsters Inc Laugh Floor, PhilharMagic, Enchanted Tiki Room

**EPCOT (12 rides):**
Guardians of the Galaxy: Cosmic Rewind, Frozen Ever After, Test Track, Remy's Ratatouille Adventure, Spaceship Earth, Soarin' Around the World, Living with the Land, Journey Into Imagination (Figment), Mission: SPACE, Seas with Nemo & Friends, Journey of Water (Moana), Gran Fiesta Tour

**Hollywood Studios (12 rides):**
Rise of the Resistance, Millennium Falcon: Smugglers Run, Tower of Terror, Slinky Dog Dash, Rock 'n' Roller Coaster, Toy Story Mania, Alien Swirling Saucers, Star Tours, Mickey & Minnie's Runaway Railway, Indiana Jones Stunt Spectacular

**Animal Kingdom (10 rides):**
Avatar Flight of Passage, Na'vi River Journey, Expedition Everest, Kilimanjaro Safaris, DINOSAUR, Kali River Rapids, Festival of the Lion King, Finding Nemo: The Big Blue and Beyond

---

## Color Schemes

### Theme Colors (12 themes)

| Theme | Background | Accent |
|-------|------------|--------|
| scifi | #0a0a19 | #4cc9f0 (cyan) |
| spooky | #190a19 | #801336 (deep red) |
| pirate | #140f0a | #c9a227 (gold) |
| adventure | #0f2319 | #95d5b2 (soft green) |
| whimsical | #282332 | #ff9f1c (warm orange) |
| playful | #1e1e2d | #ff6b6b (coral) |
| action | #0f0f14 | #ff4136 (hot red) |
| fantasy | #191423 | #b482ff (soft purple) |
| future | #0f141e | #64c8ff (light blue) |
| starwars | #05050a | #ff4500 (orange-red) |
| avatar | #051419 | #00ffc8 (bioluminescent teal) |
| classic | #14141e | #ffd700 (gold) |

### Wait Time Colors
- **Green (0-20 min):** #2ecc71
- **Yellow (21-45 min):** #f1c40f
- **Orange (46-75 min):** #e67e22
- **Red (76+ min):** #e74c3c

---

## Technical Architecture

### Project Structure
```
waitimes/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config.yaml            # Configuration settings
├── SPECIFICATION.md       # This document
├── generate_images.py     # DALL-E image generation script
│
├── src/
│   ├── api/
│   │   └── queue_times.py  # API client with caching
│   │
│   ├── display/
│   │   └── renderer.py     # Full-screen display with overlay
│   │
│   ├── models/
│   │   └── ride.py         # Ride, Park, WaitTimesData dataclasses
│   │
│   ├── themes/
│   │   ├── fonts.py        # Font mappings (60+ ride-to-theme mappings)
│   │   ├── colors.py       # Color schemes (12 themes)
│   │   └── images.py       # Image loading with cycling
│   │
│   └── utils/
│       └── logging_config.py  # Rotating file logger
│
├── assets/
│   ├── fonts/              # 10 TTF font files
│   └── images/             # DALL-E generated ride images
│
└── venv/                   # Python virtual environment
```

### Dependencies
```
pygame>=2.5.0          # Display rendering
requests>=2.31.0       # API calls
pyyaml>=6.0            # Configuration
Pillow>=10.0.0         # Image processing
openai>=1.0.0          # DALL-E image generation
```

---

## Configuration

### config.yaml
```yaml
api:
  refresh_interval: 300  # 5 minutes
  retry_delay: 30
  max_retries: 3
  timeout: 10

display:
  width: 800
  height: 480
  fullscreen: false     # true for Pi deployment
  fps: 30

rotation:
  display_duration: 8
  transition_duration: 0.5

parks:
  - magic_kingdom
  - epcot
  - hollywood_studios
  - animal_kingdom

logging:
  level: INFO
  file: waitimes.log
```

---

## Error Handling

### Network Failures
- Display cached data with "Last updated: X minutes ago"
- Warning indicator when data is stale (>15 min)
- Automatic retry with exponential backoff

### Missing Images
- Fall back to theme-colored placeholder with decorative elements
- Log missing images for generation

### Logging
- Rotating file log (5 files, 1MB each)
- Configurable log level
- Console output optional (--no-console-log flag)

---

## Deployment (Phase 5)

### Pi Setup
1. Install Raspberry Pi OS Lite
2. Install Python 3.11+
3. Clone repository
4. Install dependencies: `pip install -r requirements.txt`
5. Configure auto-login and auto-start
6. Disable screen blanking
7. Set timezone to America/New_York

### Systemd Service
```ini
[Unit]
Description=Disney Wait Times Display
After=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/waitimes
ExecStart=/usr/bin/python3 main.py --fullscreen
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Command Line Options
```
python main.py                    # Run with GUI
python main.py --fullscreen       # Fullscreen mode (for Pi)
python main.py --text-only        # Print wait times to console
python main.py --no-console-log   # Log to file only
python main.py --log-level DEBUG  # Override log level
```

---

## Future Enhancements (Phase 6+)

- **Park hours awareness:** Show "Park Closed" when appropriate
- **Nighttime mode:** Display nighttime castle/park imagery when closed
- **Weather integration:** Show current weather at parks
- **Wait time trends:** Historical graphs
- **Multi-resort support:** Disneyland, international parks

---

*Specification Version: 2.0*
*Last Updated: 2026-02-08*
