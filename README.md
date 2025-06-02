# Path of Exile Character Level Tracker

A robust, automated Discord bot that monitors Path of Exile characters for level-ups using the official PoE API. When a monitored character levels up, the system announces the event in a designated Discord channel with proper rate limiting and error handling.

## Features

- **Real-time Level Monitoring**: Continuously tracks character levels across multiple accounts
- **League-Aware Tracking**: Monitors characters in specific leagues (Standard, Hardcore, Challenge leagues, etc.)
- **Discord Notifications**: Rich Discord webhook notifications for level-ups
- **Rate Limit Compliance**: Respects PoE API rate limits with intelligent backoff strategies
- **Persistent Storage**: Character data survives container restarts
- **Docker Ready**: Easy deployment with Docker and Docker Compose
- **Unraid Compatible**: Optimized for Unraid server deployment
- **Comprehensive Logging**: Detailed logs for monitoring and troubleshooting

## Requirements

- Docker and Docker Compose
- Discord webhook URL
- Path of Exile accounts with **public character profiles**

## Quick Start

### 1. Setup Discord Webhook

1. Create a Discord webhook in your server:
   - Go to Server Settings → Integrations → Webhooks
   - Click "New Webhook"
   - Configure name and channel
   - Copy the webhook URL

### 2. Clone and Configure

```bash
git clone https://github.com/mufasadb/poe-level-tracker.git
cd poe-level-tracker

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Configure Environment Variables

Edit `.env` file:

```bash
# Discord webhook URL - REQUIRED
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Check interval in seconds (default: 300 = 5 minutes)
CHECK_INTERVAL=300

# Monitored leagues (comma-separated)
MONITORED_LEAGUES=Standard,Hardcore,Settlers

# Account names to track (comma-separated with discriminators)
TRACKED_ACCOUNTS=account1#1234,account2#5678
```

### 4. Deploy with Docker Compose

```bash
# Start the tracker
docker-compose up -d

# View logs
docker-compose logs -f poe-tracker

# Stop the tracker
docker-compose down
```

## Unraid Deployment

### Method 1: Docker Compose (Recommended)

1. **Enable Docker Compose Plugin** (if not already enabled)
   - Go to Apps → Install Docker Compose Manager

2. **Create Stack Directory**
   ```bash
   mkdir -p /mnt/user/appdata/poe-tracker
   cd /mnt/user/appdata/poe-tracker
   ```

3. **Download Files**
   ```bash
   wget https://raw.githubusercontent.com/mufasadb/poe-level-tracker/main/docker-compose.yml
   wget https://raw.githubusercontent.com/mufasadb/poe-level-tracker/main/.env.example
   mv .env.example .env
   ```

4. **Configure Environment**
   ```bash
   nano .env
   # Add your Discord webhook URL and tracked accounts
   ```

5. **Deploy Stack**
   - In Docker Compose Manager, add new stack
   - Point to `/mnt/user/appdata/poe-tracker/docker-compose.yml`
   - Deploy stack

### Method 2: Unraid Community Applications

1. **Search for "PoE Level Tracker"** in Community Applications
2. **Configure Template**:
   - **Discord Webhook URL**: Your Discord webhook URL
   - **Tracked Accounts**: Comma-separated list (e.g., `account1#1234,account2#5678`)
   - **Monitored Leagues**: Leagues to monitor (e.g., `Standard,Hardcore,Settlers`)
   - **Check Interval**: How often to check (300 seconds = 5 minutes)
   - **Data Path**: `/mnt/user/appdata/poe-tracker/data` (for persistence)
   - **Log Path**: `/mnt/user/appdata/poe-tracker/logs` (optional)

3. **Apply Template**

### Method 3: Manual Docker Command

```bash
docker run -d \
  --name poe-character-tracker \
  --restart unless-stopped \
  -e DISCORD_WEBHOOK_URL="YOUR_WEBHOOK_URL" \
  -e TRACKED_ACCOUNTS="account1#1234,account2#5678" \
  -e MONITORED_LEAGUES="Standard,Hardcore" \
  -e CHECK_INTERVAL=300 \
  -v /mnt/user/appdata/poe-tracker/data:/app/data \
  -v /mnt/user/appdata/poe-tracker/logs:/app/logs \
  ghcr.io/mufasadb/poe-level-tracker:latest
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | Yes | - | Discord webhook URL for notifications |
| `TRACKED_ACCOUNTS` | Yes | - | Comma-separated account names with discriminators |
| `MONITORED_LEAGUES` | No | `Standard,Hardcore` | Comma-separated league names to monitor |
| `CHECK_INTERVAL` | No | `300` | Check interval in seconds (minimum 60) |
| `DATA_FILE` | No | `/app/data/tracked_characters_data.json` | Path to persistent data file |

### Account Name Format

PoE now uses account names with discriminators. Format: `AccountName#1234`

To find your account name:
1. Log into pathofexile.com
2. Go to your profile
3. Look for the account name format in the URL or profile display

### Making Your Profile Public

**IMPORTANT**: Your PoE character profile must be public for the tracker to work.

1. Log into pathofexile.com
2. Go to "Privacy Settings"
3. Set "Characters" to "Public"

## Monitoring and Troubleshooting

### View Logs

```bash
# Docker Compose
docker-compose logs -f poe-tracker

# Direct Docker
docker logs -f poe-character-tracker

# Unraid
# Check container logs in Docker tab
```

### Common Issues

1. **"Account profile is private"**
   - Solution: Make your PoE character profile public in privacy settings

2. **"No tracked accounts configured"**
   - Solution: Set `TRACKED_ACCOUNTS` environment variable with account#discriminator format

3. **Rate limiting errors**
   - The bot handles this automatically with backoff strategies
   - Reduce check frequency if persistent

4. **Discord notifications not working**
   - Verify webhook URL is correct
   - Check webhook permissions in Discord
   - Test webhook manually

### Health Monitoring

The container includes a health check that verifies the application is running and generating logs.

### Data Persistence

Character data is stored in `/app/data/tracked_characters_data.json` within the container. Mount this directory to preserve data across container restarts:

```yaml
volumes:
  - ./data:/app/data
```

## API Rate Limiting

The tracker implements comprehensive rate limiting:

- Respects PoE API rate limits (15 requests per minute, 90 per 30 minutes, etc.)
- Automatic backoff on 429 errors
- Minimum 1-second delay between requests
- 2-second delay between different accounts

## Development

### Local Development

```bash
# Clone repository
git clone https://github.com/mufasadb/poe-level-tracker.git
cd poe-level-tracker

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DISCORD_WEBHOOK_URL="your_webhook_url"
export TRACKED_ACCOUNTS="account#1234"

# Run tracker
python main.py

# Or run tests
python character_tracker.py
python discord_webhook.py
```

### Building Docker Image

```bash
docker build -t poe-level-tracker .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: Report bugs and feature requests on GitHub Issues
- **Discord**: Join our Discord server for community support
- **Documentation**: Check the GitHub Wiki for additional documentation

## Changelog

### v1.0.0
- Initial release
- PoE API integration with rate limiting
- Discord webhook notifications
- League-aware character tracking
- Docker containerization
- Unraid compatibility
- Persistent data storage
- Comprehensive logging and error handling