# Reitti "This Day That Year" Collage Generator (Docker)

Generate a collage of screenshots from your self-hosted Reitti instance showing the same day across multiple years.

## Quick Start

1. Create project directory:
```bash
mkdir reitti-collage && cd reitti-collage
```

2. Create the following files:
   - `reitti_collage.py` (main script)
   - `Dockerfile`
   - `requirements.txt`
   - `docker-compose.yml`

3. Build and run:
```bash
docker-compose build
docker-compose up
```

The collage will be saved to `./output/collages/`

## Configuration

Edit `docker-compose.yml` environment variables:

- `REITTI_URL`: Your Reitti instance URL
- `START_YEAR`: First year to include (default: 2012)
- `WAIT_TIME`: Seconds to wait for page load (default: 5)
- `SCREENSHOT_WIDTH`: Screenshot width (default: 1920)
- `SCREENSHOT_HEIGHT`: Screenshot height (default: 1080)
- `COLLAGE_COLUMNS`: Number of columns in collage (default: 3)

## Run Modes

### One-time run:
```bash
docker-compose up
```

### Daily scheduled run:
Uncomment the last two lines in docker-compose.yml to run daily at the same time.

### Custom schedule with cron:
Add to your host crontab:
```bash
0 9 * * * cd /path/to/reitti-collage && docker-compose up
```

## Output Structure

```
output/
├── screenshots/     # Individual year screenshots
│   ├── reitti_2012-11-06.png
│   ├── reitti_2013-11-06.png
│   └── ...
└── collages/        # Final collage
    └── reitti_collage_11-06_2012-2025.png
```

## Troubleshooting

**Can't reach Reitti instance:**
- Use `network_mode: host` (already set) to access host network
- Verify Reitti is accessible from host

**Screenshots are blank:**
- Increase `WAIT_TIME` environment variable
- Check Reitti is responding correctly

**Permission errors:**
- Ensure `./output` directory is writable
```bash
chmod 777 output
```