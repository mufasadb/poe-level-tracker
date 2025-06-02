#!/usr/bin/env python3
"""
PoE Character Level Tracker - Main Application
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
    """Main application class for the PoE character tracker with Discord bot"""
    
    def __init__(self):
        self.running = True
        self.tracker = None
        self.bot = None
        
        # Load configuration from environment variables
        self.discord_token = os.getenv('DISCORD_BOT_TOKEN')
        self.discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')  # Fallback for webhook mode
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '300'))  # Default 5 minutes
        self.monitored_leagues = self._parse_list(os.getenv('MONITORED_LEAGUES', 'Standard,Hardcore'))
        
        # Legacy support: if TRACKED_ACCOUNTS is set, we'll use it as initial accounts
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
        if not self.discord_token and not self.discord_webhook_url:
            logger.error("Either DISCORD_BOT_TOKEN or DISCORD_WEBHOOK_URL must be configured.")
            logger.error("For bot mode (recommended): Set DISCORD_BOT_TOKEN")
            logger.error("For webhook mode (legacy): Set DISCORD_WEBHOOK_URL")
            return False
        
        if self.discord_token:
            logger.info("Bot mode enabled - Discord bot will handle commands and notifications")
        else:
            logger.info("Webhook mode enabled - Using legacy webhook notifications")
            if not self.initial_tracked_accounts:
                logger.error("Webhook mode requires TRACKED_ACCOUNTS to be configured.")
                return False
        
        logger.info(f"Configuration loaded:")
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
    
    async def run_bot_mode(self):
        """Run in Discord bot mode"""
        logger.info("Starting PoE Character Level Tracker in Bot Mode")
        
        # Initialize tracker (without webhook since bot handles notifications)
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
    
    def run_webhook_mode(self):
        """Run in legacy webhook mode (for backwards compatibility)"""
        logger.info("Starting PoE Character Level Tracker in Webhook Mode")
        
        # Initialize tracker with webhook
        self.tracker = PoECharacterTracker(discord_webhook_url=self.discord_webhook_url)
        
        logger.info("Starting monitoring loop...")
        
        cycle_count = 0
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"Starting check cycle #{cycle_count}")
                
                start_time = time.time()
                level_ups_found = self.run_single_check()
                check_duration = time.time() - start_time
                
                logger.info(f"Check cycle #{cycle_count} completed in {check_duration:.2f}s, found {level_ups_found} level-ups")
                
                # Sleep until next check interval
                if self.running:
                    logger.info(f"Sleeping for {self.check_interval} seconds until next check...")
                    for _ in range(self.check_interval):
                        if not self.running:
                            break
                        time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                logger.info(f"Continuing after 60 second delay...")
                time.sleep(60)
    
    def run_single_check(self):
        """Run a single check cycle for all tracked accounts (webhook mode only)"""
        total_level_ups = 0
        
        for account in self.initial_tracked_accounts:
            try:
                logger.info(f"Checking account: {account}")
                
                # Check for level-ups
                level_ups = self.tracker.track_characters_for_levelups(account, self.monitored_leagues)
                
                if level_ups:
                    logger.info(f"Found {len(level_ups)} level-ups for {account}")
                    total_level_ups += len(level_ups)
                    
                    for character, old_level, new_level in level_ups:
                        logger.info(f"Level up: {character.name} ({character.league}) {old_level} -> {new_level}")
                else:
                    logger.debug(f"No level-ups detected for {account}")
                
                # Small delay between accounts to be respectful to the API
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error checking account {account}: {e}")
        
        return total_level_ups
    
    def run(self):
        """Main application entry point"""
        if not self.validate_configuration():
            return 1
        
        if self.discord_token:
            # Run in bot mode
            try:
                asyncio.run(self.run_bot_mode())
            except Exception as e:
                logger.error(f"Bot mode error: {e}")
                return 1
        else:
            # Run in webhook mode
            try:
                self.run_webhook_mode()
            except Exception as e:
                logger.error(f"Webhook mode error: {e}")
                return 1
        
        logger.info("PoE Character Level Tracker stopped")
        return 0


def main():
    """Entry point for the application"""
    app = PoETrackerApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())