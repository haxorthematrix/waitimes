# Disney World Wait Times Display

A pygame-based display application that shows real-time Walt Disney World wait times on a Raspberry Pi with a 7" touchscreen. Features themed fonts, color schemes, and AI-generated ride images.

![Display Example](docs/example.png)

## Features

- **Real-time wait times** from queue-times.com (10-minute refresh)
- **Full-screen ride images** with clean bottom bar overlay
- **68 AI-generated images** (64 rides + 4 parks) via DALL-E 3
- **10 themed fonts** matched to ride aesthetics (sci-fi, spooky, pirate, etc.)
- **12 color schemes** for different ride themes
- **Smooth crossfade transitions** between rides
- **60+ ride mappings** across all 4 WDW parks
- **Closed park display** with park-specific imagery when parks aren't operating
- **Weather display** with OpenWeatherMap integration and custom icons
- **Web dashboard** for historical wait time trends (Flask + SQLite)
- **Special events** - fireworks and parade video playback with Sora AI-generated videos
- **Graceful error handling** with stale data warnings
- **Fully automated** - set it and forget it

## Requirements

- Python 3.11+
- Raspberry Pi with 7" touchscreen (800x480) or any display
- Network connection

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/haxorthematrix/waitimes.git
cd waitimes
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the display

```bash
# Windowed mode (for development)
python main.py

# Fullscreen mode (for Pi deployment)
python main.py --fullscreen

# Text-only mode (no GUI, just print wait times)
python main.py --text-only
```

## Configuration

Edit `config.yaml` to customize:

```yaml
api:
  refresh_interval: 300  # seconds between API updates
  timeout: 10

display:
  width: 800
  height: 480
  fullscreen: false      # set true for Pi
  fps: 30

rotation:
  display_duration: 8    # seconds per ride
  transition_duration: 0.5

parks:                   # comment out parks to exclude
  - magic_kingdom
  - epcot
  - hollywood_studios
  - animal_kingdom
```

## Adding Custom Images

Images are stored in `assets/images/{ride_folder}/`. Each ride has its own folder.

### Image Requirements

- **Format:** PNG or JPG
- **Recommended size:** 1792x1024 (will be scaled to 800x480)
- **Naming:** `1.png`, `2.png`, `3.png`, etc.

### Adding Images to a Ride

1. Find the ride's folder name in `src/themes/images.py` under `RIDE_IMAGE_MAP`
2. Add your image(s) to `assets/images/{folder_name}/`
3. Images will automatically be included in the rotation

**Example:** To add a custom Space Mountain image:
```bash
# The folder for Space Mountain is "space_mountain"
cp my_space_mountain_photo.png assets/images/space_mountain/2.png
```

### Image Rotation Behavior

- Multiple images per ride will cycle through
- Images rotate **after a complete round** of all rides (not during)
- This means if you have 3 images for Space Mountain and 7 rides total, you'll see all 7 rides, then on the next cycle, Space Mountain shows image #2

### Ride Folder Reference

| Ride | Folder Name |
|------|-------------|
| Space Mountain | `space_mountain` |
| Haunted Mansion | `haunted_mansion` |
| Pirates of the Caribbean | `pirates_caribbean` |
| Jungle Cruise | `jungle_cruise` |
| Big Thunder Mountain | `big_thunder` |
| Seven Dwarfs Mine Train | `seven_dwarfs` |
| It's a Small World | `small_world` |
| Peter Pan's Flight | `peter_pan` |
| TRON Lightcycle Run | `tron` |
| Tiana's Bayou Adventure | `tiana` |
| Tower of Terror | `tower_terror` |
| Rock 'n' Roller Coaster | `rock_roller` |
| Slinky Dog Dash | `slinky_dog` |
| Toy Story Mania | `toy_story` |
| Rise of the Resistance | `rise_resistance` |
| Millennium Falcon | `millennium_falcon` |
| Star Tours | `star_tours` |
| Runaway Railway | `runaway_railway` |
| Guardians of the Galaxy | `guardians_galaxy` |
| Frozen Ever After | `frozen` |
| Test Track | `test_track` |
| Spaceship Earth | `spaceship_earth` |
| Remy's Ratatouille | `remy` |
| Soarin' | `soarin` |
| Mission: SPACE | `mission_space` |
| Flight of Passage | `flight_passage` |
| Na'vi River Journey | `navi_river` |
| Expedition Everest | `everest` |
| Kilimanjaro Safaris | `kilimanjaro` |
| Zootopia | `zootopia` |
| Wildlife Express | `wildlife_express` |
| Walt Disney World Railroad | `railroad` |
| Prince Charming Regal Carrousel | `carrousel` |

**Park Images (for closed display):**

| Park | Folder Name |
|------|-------------|
| Magic Kingdom | `parks/magic_kingdom` |
| EPCOT | `parks/epcot` |
| Hollywood Studios | `parks/hollywood_studios` |
| Animal Kingdom | `parks/animal_kingdom` |

See `src/themes/images.py` for the complete mapping.

## Generating Images with DALL-E

If you have an OpenAI API key, you can generate images:

```bash
export OPENAI_API_KEY='your-api-key'
python generate_images.py         # Batch 1: 20 main rides
python generate_images_batch2.py  # Batch 2: 30 additional rides
python generate_images_batch3.py  # Batch 3: 14 rides + character meets
python generate_park_images.py    # Park images for closed display
```

**Note:** Due to rate limits, image generation takes ~2 minutes per image. All 68 images are already included in the repository.

## Raspberry Pi Deployment

### 1. Install on Pi

```bash
# Clone and install
git clone https://github.com/haxorthematrix/waitimes.git
cd waitimes
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test it works
python main.py --fullscreen
```

### 2. Set up auto-start with systemd

Create `/etc/systemd/system/waitimes.service`:

```ini
[Unit]
Description=Disney Wait Times Display
After=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/waitimes
Environment=DISPLAY=:0
ExecStart=/home/pi/waitimes/venv/bin/python main.py --fullscreen --no-console-log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable waitimes
sudo systemctl start waitimes
```

### 3. Disable screen blanking

Add to `/etc/xdg/lxsession/LXDE-pi/autostart`:
```
@xset s off
@xset -dpms
@xset s noblank
```

### 4. Set timezone

```bash
sudo timedatectl set-timezone America/New_York
```

## Command Line Options

```
python main.py [options]

Options:
  --fullscreen        Run in fullscreen mode
  --text-only         Print wait times to console (no GUI)
  --config FILE       Use custom config file (default: config.yaml)
  --log-level LEVEL   Set log level: DEBUG, INFO, WARNING, ERROR
  --no-console-log    Disable console logging (file only)
  --test-event TYPE   Test event animation (fireworks, fireworks-epcot, parade)
```

## Closed Park Display

When a park is not operating (no rides reporting wait times), the display shows:
- Park-specific background image (e.g., Cinderella Castle for Magic Kingdom)
- "CLOSED" in large red text
- Park name
- Opening time (if available)

This provides a nice visual even during off-hours instead of a blank screen.

## Logs

- **Log file:** `waitimes.log` (rotating, 5 files, 1MB each)
- **View logs:** `tail -f waitimes.log`

## Troubleshooting

### Display won't start
- Check pygame is installed: `python -c "import pygame; print(pygame.ver)"`
- Ensure DISPLAY is set: `echo $DISPLAY`
- Try running with `--log-level DEBUG`

### No wait times showing
- Check network connection
- Verify queue-times.com is accessible
- Check logs for API errors

### Images not loading
- Verify images are in correct folder: `ls assets/images/`
- Check image format (PNG/JPG only)
- Check logs for loading errors

## Web Dashboard

Access the web dashboard at `http://<pi-ip>/` to view:

- Current wait times for all parks
- Historical trend graphs
- Individual ride statistics
- JSON API endpoints (`/api/waits`, `/api/history`)

### Weather Setup

1. Get a free API key from [OpenWeatherMap](https://openweathermap.org/api)
2. Add to `config.yaml`:
   ```yaml
   weather:
     enabled: true
     api_key: "your-api-key"
   ```

### Special Events

Fireworks and parade videos play automatically at scheduled times. Test with:

```bash
python main.py --test-event fireworks        # Magic Kingdom fireworks
python main.py --test-event fireworks-epcot  # EPCOT fireworks
python main.py --test-event parade           # Magic Kingdom parade
```

## Roadmap (Phase 9+)

Future enhancements under consideration:

- [ ] **Multi-resort support** - Disneyland, Tokyo Disney, international parks
- [ ] **Lightning Lane integration** - Show LL return times alongside standby
- [ ] **Mobile companion app** - Remote monitoring from your phone
- [ ] **Voice announcements** - Audio alerts when favorite rides have short waits
- [ ] **Predictive wait times** - ML-based predictions for optimal visit planning
- [ ] **Additional event videos** - Hollywood Studios, Animal Kingdom events
- [ ] **Enhanced web dashboard** - More visualizations, park comparisons, data export

## License

MIT License - see LICENSE file.

## Credits

- Wait time data: [queue-times.com](https://queue-times.com)
- Weather data: [OpenWeatherMap](https://openweathermap.org)
- Fonts: Google Fonts
- Ride images: Generated with DALL-E 3
- Event videos: Generated with OpenAI Sora
