#!/usr/bin/env python3
"""
PoE Character Level Tracker - Discord Bot
Discord bot with commands to manage character tracking
"""

import os
import signal
import sys
import logging
import asyncio
from typing import List
from character_tracker import PoECharacterTracker
from discord_bot import PoETrackerBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('poe_tracker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PoETrackerApp:
    """Main application class for the PoE character tracker Discord bot"""
    
    def __init__(self):
        self.running = True
        self.tracker = None
        self.bot = None
        
        # Load configuration from environment variables
        self.discord_token = os.getenv('DISCORD_BOT_TOKEN')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))  # Default 5 minutes
        self.monitored_leagues = self._parse_list(os.getenv('MONITORED_LEAGUES', 'Standard,Hardcore'))
        
        # Initial accounts (optional - can be added via Discord commands)
        self.initial_tracked_accounts = self._parse_list(os.getenv('TRACKED_ACCOUNTS', ''))
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list"""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def validate_configuration(self) -> bool:
        """Validate that required configuration is present"""
        if not self.discord_token:
            logger.error("DISCORD_BOT_TOKEN is required.")
            logger.error("Please set your Discord bot token in the environment variables.")
            return False
        
        logger.info(f"Configuration loaded:")
        logger.info(f"  Discord bot token: {'✓ Configured' if self.discord_token else '✗ Missing'}")
        logger.info(f"  Check interval: {self.check_interval} seconds")
        logger.info(f"  Monitored leagues: {self.monitored_leagues}")
        if self.initial_tracked_accounts:
            logger.info(f"  Initial tracked accounts: {len(self.initial_tracked_accounts)}")
        
        return True
    
    async def setup_initial_accounts(self):
        """Setup initial tracked accounts if provided via environment variable"""
        if self.initial_tracked_accounts and self.bot:
            logger.info(f"Adding {len(self.initial_tracked_accounts)} initial accounts from environment")
            for account in self.initial_tracked_accounts:
                self.bot.tracked_accounts.add(account)
            self.bot.save_tracked_accounts()
    
    async def run_bot(self):
        """Run the Discord bot"""
        logger.info("Starting PoE Character Level Tracker Discord Bot")
        
        # Initialize tracker
        self.tracker = PoECharacterTracker()
        
        # Initialize bot
        self.bot = PoETrackerBot(
            tracker=self.tracker,
            monitored_leagues=self.monitored_leagues,
            check_interval=self.check_interval
        )
        
        # Setup initial accounts if provided
        await self.setup_initial_accounts()
        
        try:
            # Start the bot
            await self.bot.start(self.discord_token)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down bot...")
        finally:
            await self.bot.close()
    
    def run(self):
        """Main application entry point"""
        if not self.validate_configuration():
            return 1
        
        try:
            asyncio.run(self.run_bot())
        except Exception as e:
            logger.error(f"Bot error: {e}")
            return 1
        
        logger.info("PoE Character Level Tracker stopped")
        return 0


def main():
    """Entry point for the application"""
    app = PoETrackerApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())