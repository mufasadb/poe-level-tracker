# Docker Deployment Guide

## Using Docker Hub Image

The bot is automatically built and published to Docker Hub: `callmebeachy/poe-character-tracker:latest`

## Environment Variables

### Method 1: Docker Compose with .env file (Recommended)

1. **Create `.env` file**:
```bash
DISCORD_BOT_TOKEN=your_bot_token_here
CHECK_INTERVAL=300
MONITORED_LEAGUES=Standard,Hardcore,Settlers
TRACKED_ACCOUNTS=account1#1234,account2#5678
```

2. **Use docker-compose.yml**:
```yaml
version: '3.8'
services:
  poe-tracker:
    image: callmebeachy/poe-character-tracker:latest
    container_name: poe-character-tracker
    restart: unless-stopped
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - CHECK_INTERVAL=${CHECK_INTERVAL:-300}
      - MONITORED_LEAGUES=${MONITORED_LEAGUES:-Standard,Hardcore}
      - TRACKED_ACCOUNTS=${TRACKED_ACCOUNTS}
    volumes:
      - ./data:/app/data
```

3. **Start**:
```bash
docker-compose up -d
```

### Method 2: Direct Docker Run

```bash
docker run -d \
  --name poe-character-tracker \
  --restart unless-stopped \
  -e DISCORD_BOT_TOKEN="your_bot_token_here" \
  -e CHECK_INTERVAL=300 \
  -e MONITORED_LEAGUES="Standard,Hardcore,Settlers" \
  -e TRACKED_ACCOUNTS="account1#1234,account2#5678" \
  -v $(pwd)/data:/app/data \
  callmebeachy/poe-character-tracker:latest
```

### Method 3: Docker Environment File

1. **Create `docker.env` file**:
```bash
DISCORD_BOT_TOKEN=your_bot_token_here
CHECK_INTERVAL=300
MONITORED_LEAGUES=Standard,Hardcore,Settlers
TRACKED_ACCOUNTS=account1#1234,account2#5678
```

2. **Run with env file**:
```bash
docker run -d \
  --name poe-character-tracker \
  --restart unless-stopped \
  --env-file docker.env \
  -v $(pwd)/data:/app/data \
  callmebeachy/poe-character-tracker:latest
```

### Method 4: Unraid Community Applications

When the template is added to Community Applications:

1. **Container Settings**:
   - **Repository**: `callmebeachy/poe-character-tracker:latest`
   - **Network Type**: `bridge`

2. **Environment Variables**:
   - `DISCORD_BOT_TOKEN`: Your Discord bot token
   - `CHECK_INTERVAL`: `300` (5 minutes)
   - `MONITORED_LEAGUES`: `Standard,Hardcore,Settlers`
   - `TRACKED_ACCOUNTS`: `account1#1234,account2#5678` (optional)

3. **Volume Mappings**:
   - **Container Path**: `/app/data`
   - **Host Path**: `/mnt/user/appdata/poe-tracker/data`

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | ✅ Yes | - | Discord bot token |
| `CHECK_INTERVAL` | No | `300` | Check interval in seconds |
| `MONITORED_LEAGUES` | No | `Standard,Hardcore` | Comma-separated leagues |
| `TRACKED_ACCOUNTS` | No | - | Initial accounts (optional) |
| `PUID` | No | `1000` | User ID for file permissions (Unraid: use `99`) |
| `PGID` | No | `1000` | Group ID for file permissions (Unraid: use `100`) |
| `DATA_FILE` | No | `/app/data/tracked_characters_data.json` | Data file location |

## Volume Mounts

- **`/app/data`**: Persistent storage for character data and tracked accounts
- **`/app/logs`**: Log files (optional)

## Health Check

The container includes a health check that verifies the application is running:

```bash
# Check container health
docker ps
# STATUS should show "healthy"

# View health check logs
docker inspect poe-character-tracker --format='{{.State.Health.Status}}'
```

## Logging

```bash
# View logs
docker logs poe-character-tracker

# Follow logs
docker logs -f poe-character-tracker

# View with timestamps
docker logs -t poe-character-tracker
```

## Updating

```bash
# Pull latest image
docker pull callmebeachy/poe-character-tracker:latest

# Recreate container (with docker-compose)
docker-compose pull
docker-compose up -d

# Or manually
docker stop poe-character-tracker
docker rm poe-character-tracker
# Then run again with same parameters
```

## Troubleshooting

**Bot not starting?**
```bash
# Check environment variables
docker exec poe-character-tracker env | grep DISCORD

# Check logs for errors
docker logs poe-character-tracker | grep ERROR
```

**Data not persisting?**
```bash
# Verify volume mount
docker inspect poe-character-tracker | grep -A 10 Mounts

# Check data directory
ls -la ./data/
```

**Permission issues?**
```bash
# Fix data directory permissions
sudo chown -R 1000:1000 ./data/
```