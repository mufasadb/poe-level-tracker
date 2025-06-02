#!/usr/bin/env python3
"""
Discord bot functionality for PoE character tracker
Provides commands to manage tracked accounts dynamically
"""

import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import logging
import re
from typing import List, Dict, Set
from character_tracker import PoECharacterTracker

logger = logging.getLogger(__name__)


class PoETrackerBot(commands.Bot):
    """Discord bot for managing PoE character tracking"""
    
    def __init__(self, tracker: PoECharacterTracker, monitored_leagues: List[str], check_interval: int = 300):
        # Setup bot with minimal required intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for prefix commands
        # Disable unnecessary intents
        intents.presences = False
        intents.members = False
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None  # Disable default help command so we can use our own
        )
        
        self.tracker = tracker
        self.monitored_leagues = monitored_leagues
        self.check_interval = check_interval
        self.tracked_accounts: Set[str] = set()
        self.notification_channel_id = None
        
        # Load tracked accounts from file
        self.load_tracked_accounts()
        
        # Add commands
        self.add_commands()
    
    def load_tracked_accounts(self):
        """Load tracked accounts from JSON file"""
        try:
            accounts_file = "tracked_accounts.json"
            if os.path.exists(accounts_file):
                with open(accounts_file, 'r') as f:
                    data = json.load(f)
                    self.tracked_accounts = set(data.get('accounts', []))
                    self.notification_channel_id = data.get('notification_channel_id')
                logger.info(f"Loaded {len(self.tracked_accounts)} tracked accounts")
            else:
                logger.info("No existing tracked accounts file found")
        except Exception as e:
            logger.error(f"Error loading tracked accounts: {e}")
    
    def save_tracked_accounts(self):
        """Save tracked accounts to JSON file"""
        try:
            accounts_file = "tracked_accounts.json"
            data = {
                'accounts': list(self.tracked_accounts),
                'notification_channel_id': self.notification_channel_id
            }
            with open(accounts_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.tracked_accounts)} tracked accounts")
        except Exception as e:
            logger.error(f"Error saving tracked accounts: {e}")
    
    def add_commands(self):
        """Add all bot commands"""
        
        @self.command(name='track')
        async def track_command(ctx, action: str = None, *, account: str = None):
            """
            Manage tracked PoE accounts
            
            Usage:
            !track add AccountName#1234 - Add account to tracking
            !track remove AccountName#1234 - Remove account from tracking  
            !track list - List all tracked accounts
            !track channel - Set this channel for notifications
            !track status - Show tracking status
            """
            if action is None:
                await ctx.send("**PoE Character Tracker Commands:**\n"
                             "```\n"
                             "!track add AccountName#1234    - Add account to tracking\n"
                             "!track remove AccountName#1234 - Remove account from tracking\n"
                             "!track list                    - List all tracked accounts\n"
                             "!track channel                 - Set this channel for notifications\n"
                             "!track status                  - Show tracking status\n"
                             "!track test AccountName#1234   - Test if account is accessible\n"
                             "\n"
                             "!highest AccountName#1234      - Show highest level character\n"
                             "!characters AccountName#1234   - List all characters for account\n"
                             "!leagues                       - Show monitored leagues\n"
                             "!ping                          - Check bot responsiveness\n"
                             "!help                          - Show detailed help\n"
                             "```")
                return
            
            if action.lower() == 'add':
                await self.handle_add_account(ctx, account)
            elif action.lower() == 'remove':
                await self.handle_remove_account(ctx, account)
            elif action.lower() == 'list':
                await self.handle_list_accounts(ctx)
            elif action.lower() == 'channel':
                await self.handle_set_channel(ctx)
            elif action.lower() == 'status':
                await self.handle_status(ctx)
            elif action.lower() == 'test':
                await self.handle_test_account(ctx, account)
            else:
                await ctx.send(f"Unknown action: {action}. Use `!track` for help.")
        
        @self.command(name='leagues')
        async def leagues_command(ctx):
            """Show monitored leagues"""
            leagues_text = ", ".join(self.monitored_leagues) if self.monitored_leagues else "All leagues"
            embed = discord.Embed(
                title="📋 Monitored Leagues",
                description=f"Currently monitoring: **{leagues_text}**",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        
        @self.command(name='ping')
        async def ping_command(ctx):
            """Check if bot is responsive"""
            latency = round(self.latency * 1000)
            await ctx.send(f"🏓 Pong! Latency: {latency}ms")
        
        @self.command(name='highest')
        async def highest_command(ctx, *, account: str = None):
            """
            Show the highest level character for an account
            
            Usage: !highest AccountName#1234
            """
            if not account:
                await ctx.send("❌ Please provide an account name: `!highest AccountName#1234`")
                return
            
            await self.handle_highest_character(ctx, account)
        
        @self.command(name='characters')
        async def characters_command(ctx, *, account: str = None):
            """
            List all characters for an account
            
            Usage: !characters AccountName#1234
            """
            if not account:
                await ctx.send("❌ Please provide an account name: `!characters AccountName#1234`")
                return
            
            await self.handle_list_characters(ctx, account)
        
        @self.command(name='help')
        async def help_command(ctx):
            """Show comprehensive help information"""
            embed = discord.Embed(
                title="🤖 PoE Character Level Tracker - Help",
                description="I monitor Path of Exile characters and notify when they level up!",
                color=0xff6b35
            )
            
            # Account Management
            embed.add_field(
                name="📋 Account Management", 
                value="```\n"
                      "!track add AccountName#1234    - Add account to tracking\n"
                      "!track remove AccountName#1234 - Remove account\n"
                      "!track list                    - List tracked accounts\n"
                      "!track test AccountName#1234   - Test account access\n"
                      "```",
                inline=False
            )
            
            # Setup Commands
            embed.add_field(
                name="⚙️ Setup Commands",
                value="```\n"
                      "!track channel                 - Set notification channel\n"
                      "!track status                  - Show tracking status\n"
                      "!leagues                       - Show monitored leagues\n"
                      "```",
                inline=False
            )
            
            # Character Info
            embed.add_field(
                name="👤 Character Information",
                value="```\n"
                      "!highest AccountName#1234      - Show highest level character\n"
                      "!characters AccountName#1234   - List all characters\n"
                      "```",
                inline=False
            )
            
            # How it works
            embed.add_field(
                name="❓ How It Works",
                value="1️⃣ Add PoE accounts to track with `!track add`\n"
                      "2️⃣ Set notification channel with `!track channel`\n"
                      "3️⃣ I check every 5 minutes for level-ups\n"
                      "4️⃣ Get notified when characters level up!\n\n"
                      "**Note:** PoE accounts must have PUBLIC character profiles!",
                inline=False
            )
            
            # Utility
            embed.add_field(
                name="🔧 Utility",
                value="`!ping` - Check if I'm responsive\n"
                      "`!help` - Show this help message",
                inline=False
            )
            
            embed.set_footer(text="💡 Tip: Use !track for quick command reference")
            
            await ctx.send(embed=embed)
    
    async def handle_add_account(self, ctx, account: str):
        """Handle adding an account to tracking"""
        if not account:
            await ctx.send("❌ Please provide an account name: `!track add AccountName#1234`")
            return
        
        # Validate account format
        if '#' not in account:
            await ctx.send("❌ Account name must include discriminator: `AccountName#1234`")
            return
        
        if account in self.tracked_accounts:
            await ctx.send(f"⚠️ Account `{account}` is already being tracked!")
            return
        
        # Test if account is accessible
        await ctx.send(f"🔍 Testing account `{account}`...")
        
        try:
            characters = self.tracker.fetch_account_characters(account)
            if characters is None:
                await ctx.send(f"❌ Failed to access account `{account}`. Make sure the profile is public!")
                return
            
            # Add to tracking
            self.tracked_accounts.add(account)
            self.save_tracked_accounts()
            
            # Show what we found
            filtered_chars = [c for c in characters if not self.monitored_leagues or c.league in self.monitored_leagues]
            
            embed = discord.Embed(
                title="✅ Account Added Successfully",
                description=f"Now tracking account: **{account}**",
                color=0x00ff00
            )
            embed.add_field(
                name="Characters Found",
                value=f"{len(characters)} total, {len(filtered_chars)} in monitored leagues",
                inline=False
            )
            
            if filtered_chars[:5]:  # Show up to 5 characters
                char_list = "\n".join([f"• {c.name} (Level {c.level}, {c.league})" for c in filtered_chars[:5]])
                if len(filtered_chars) > 5:
                    char_list += f"\n... and {len(filtered_chars) - 5} more"
                embed.add_field(name="Tracked Characters", value=char_list, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error adding account {account}: {e}")
            await ctx.send(f"❌ Error testing account: {e}")
    
    async def handle_remove_account(self, ctx, account: str):
        """Handle removing an account from tracking"""
        if not account:
            await ctx.send("❌ Please provide an account name: `!track remove AccountName#1234`")
            return
        
        if account not in self.tracked_accounts:
            await ctx.send(f"⚠️ Account `{account}` is not currently being tracked!")
            return
        
        self.tracked_accounts.remove(account)
        self.save_tracked_accounts()
        
        embed = discord.Embed(
            title="✅ Account Removed",
            description=f"Stopped tracking account: **{account}**",
            color=0xff6b35
        )
        await ctx.send(embed=embed)
    
    async def handle_list_accounts(self, ctx):
        """Handle listing all tracked accounts"""
        if not self.tracked_accounts:
            await ctx.send("📝 No accounts are currently being tracked. Use `!track add AccountName#1234` to start tracking!")
            return
        
        embed = discord.Embed(
            title="📋 Tracked Accounts",
            description=f"Currently tracking {len(self.tracked_accounts)} accounts:",
            color=0x0099ff
        )
        
        account_list = "\n".join([f"• {account}" for account in sorted(self.tracked_accounts)])
        embed.add_field(name="Accounts", value=account_list, inline=False)
        
        leagues_text = ", ".join(self.monitored_leagues) if self.monitored_leagues else "All leagues"
        embed.add_field(name="Monitored Leagues", value=leagues_text, inline=False)
        
        await ctx.send(embed=embed)
    
    async def handle_set_channel(self, ctx):
        """Handle setting notification channel"""
        self.notification_channel_id = ctx.channel.id
        self.save_tracked_accounts()
        
        embed = discord.Embed(
            title="✅ Notification Channel Set",
            description=f"Level-up notifications will be sent to {ctx.channel.mention}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    
    async def handle_status(self, ctx):
        """Handle showing tracking status"""
        embed = discord.Embed(
            title="📊 Tracker Status",
            color=0x0099ff
        )
        
        embed.add_field(name="Tracked Accounts", value=str(len(self.tracked_accounts)), inline=True)
        embed.add_field(name="Check Interval", value=f"{self.check_interval} seconds", inline=True)
        embed.add_field(name="Notification Channel", 
                       value=f"<#{self.notification_channel_id}>" if self.notification_channel_id else "Not set", 
                       inline=True)
        
        leagues_text = ", ".join(self.monitored_leagues) if self.monitored_leagues else "All leagues"
        embed.add_field(name="Monitored Leagues", value=leagues_text, inline=False)
        
        await ctx.send(embed=embed)
    
    async def handle_test_account(self, ctx, account: str):
        """Handle testing account accessibility"""
        if not account:
            await ctx.send("❌ Please provide an account name: `!track test AccountName#1234`")
            return
        
        await ctx.send(f"🔍 Testing account `{account}`...")
        
        try:
            characters = self.tracker.fetch_account_characters(account)
            if characters is None:
                await ctx.send(f"❌ Cannot access account `{account}`. Profile may be private or account name incorrect.")
                return
            
            filtered_chars = [c for c in characters if not self.monitored_leagues or c.league in self.monitored_leagues]
            
            embed = discord.Embed(
                title="✅ Account Test Successful",
                description=f"Account `{account}` is accessible!",
                color=0x00ff00
            )
            embed.add_field(name="Total Characters", value=str(len(characters)), inline=True)
            embed.add_field(name="In Monitored Leagues", value=str(len(filtered_chars)), inline=True)
            
            if filtered_chars[:3]:  # Show up to 3 characters
                char_list = "\n".join([f"• {c.name} (Level {c.level}, {c.league})" for c in filtered_chars[:3]])
                embed.add_field(name="Sample Characters", value=char_list, inline=False)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error testing account {account}: {e}")
            await ctx.send(f"❌ Error testing account: {e}")
    
    async def handle_highest_character(self, ctx, account: str):
        """Handle showing highest level character for an account"""
        await ctx.send(f"🔍 Finding highest level character for `{account}`...")
        
        try:
            characters = self.tracker.fetch_account_characters(account)
            if characters is None:
                await ctx.send(f"❌ Cannot access account `{account}`. Profile may be private or account name incorrect.")
                return
            
            if not characters:
                await ctx.send(f"❌ No characters found for account `{account}`.")
                return
            
            # Filter by monitored leagues if specified
            if self.monitored_leagues:
                filtered_characters = [c for c in characters if c.league in self.monitored_leagues]
                if not filtered_characters:
                    await ctx.send(f"❌ No characters found in monitored leagues for `{account}`.\n"
                                 f"Monitored leagues: {', '.join(self.monitored_leagues)}")
                    return
                characters = filtered_characters
            
            # Find highest level character
            highest_char = max(characters, key=lambda c: c.level)
            
            embed = discord.Embed(
                title="🏆 Highest Level Character",
                description=f"**{highest_char.name}** is the highest level character for `{account}`",
                color=0xffd700  # Gold color
            )
            embed.add_field(name="Character", value=highest_char.name, inline=True)
            embed.add_field(name="Level", value=highest_char.level, inline=True)
            embed.add_field(name="Class", value=highest_char.class_name, inline=True)
            embed.add_field(name="League", value=highest_char.league, inline=True)
            
            # Show if there are other high-level characters
            same_level_chars = [c for c in characters if c.level == highest_char.level]
            if len(same_level_chars) > 1:
                other_chars = [c.name for c in same_level_chars if c.name != highest_char.name]
                embed.add_field(
                    name="Also at Level " + str(highest_char.level), 
                    value=", ".join(other_chars[:5]), 
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting highest character for {account}: {e}")
            await ctx.send(f"❌ Error retrieving character data: {e}")
    
    async def handle_list_characters(self, ctx, account: str):
        """Handle listing all characters for an account"""
        await ctx.send(f"🔍 Retrieving characters for `{account}`...")
        
        try:
            characters = self.tracker.fetch_account_characters(account)
            if characters is None:
                await ctx.send(f"❌ Cannot access account `{account}`. Profile may be private or account name incorrect.")
                return
            
            if not characters:
                await ctx.send(f"❌ No characters found for account `{account}`.")
                return
            
            # Sort characters by level (highest first)
            characters.sort(key=lambda c: c.level, reverse=True)
            
            # Filter by monitored leagues if specified
            if self.monitored_leagues:
                monitored_chars = [c for c in characters if c.league in self.monitored_leagues]
                other_chars = [c for c in characters if c.league not in self.monitored_leagues]
            else:
                monitored_chars = characters
                other_chars = []
            
            embed = discord.Embed(
                title="📋 Character List",
                description=f"Characters for account: **{account}**",
                color=0x0099ff
            )
            
            # Show monitored league characters
            if monitored_chars:
                char_list = []
                for char in monitored_chars[:15]:  # Limit to 15 to avoid embed limits
                    char_list.append(f"• **{char.name}** - Level {char.level} {char.class_name} ({char.league})")
                
                field_name = "Monitored Leagues" if self.monitored_leagues else "All Characters"
                embed.add_field(
                    name=field_name, 
                    value="\n".join(char_list), 
                    inline=False
                )
                
                if len(monitored_chars) > 15:
                    embed.add_field(
                        name="...", 
                        value=f"And {len(monitored_chars) - 15} more characters", 
                        inline=False
                    )
            
            # Show other league characters (if any)
            if other_chars and self.monitored_leagues:
                other_list = []
                for char in other_chars[:10]:  # Limit to 10
                    other_list.append(f"• {char.name} - Level {char.level} {char.class_name} ({char.league})")
                
                embed.add_field(
                    name="Other Leagues (Not Monitored)", 
                    value="\n".join(other_list), 
                    inline=False
                )
                
                if len(other_chars) > 10:
                    embed.add_field(
                        name="...", 
                        value=f"And {len(other_chars) - 10} more in other leagues", 
                        inline=False
                    )
            
            # Add summary
            total_chars = len(characters)
            monitored_count = len(monitored_chars) if self.monitored_leagues else total_chars
            embed.add_field(
                name="📊 Summary", 
                value=f"Total: {total_chars} characters, Monitored: {monitored_count}", 
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing characters for {account}: {e}")
            await ctx.send(f"❌ Error retrieving character data: {e}")
    
    def is_help_question(self, message_content: str) -> bool:
        """Check if message is asking for help with the bot"""
        # Normalize message: lowercase, remove extra spaces
        content = re.sub(r'\s+', ' ', message_content.lower().strip())
        
        # Define patterns for help-seeking messages
        help_patterns = [
            # How does questions
            r'how\s+do(?:es)?\s+(?:the\s+)?(?:this\s+)?bot\s+work',
            r'how\s+do(?:es)?\s+(?:this\s+)?(?:it\s+)?work',
            
            # How to message/talk/use
            r'how\s+(?:do\s+)?(?:i\s+|you\s+)?(?:message|msg|talk\s+to|contact|use|communicate\s+with)\s+(?:the\s+)?bot',
            r'how\s+(?:do\s+)?(?:i\s+|you\s+)?(?:message|msg|talk\s+to|contact|use|communicate\s+with)\s+(?:this|it)',
            
            # Commands questions
            r'what\s+(?:are\s+the\s+)?commands',
            r'(?:show\s+|list\s+)?(?:bot\s+)?commands',
            r'how\s+(?:do\s+)?(?:i\s+|you\s+)?(?:use|control)\s+(?:the\s+)?(?:this\s+)?bot',
            
            # Help requests
            r'help\s+(?:me\s+)?(?:with\s+)?(?:the\s+)?(?:this\s+)?bot',
            r'bot\s+help',
            r'need\s+help',
            
            # What does questions
            r'what\s+do(?:es)?\s+(?:the\s+)?(?:this\s+)?bot\s+do',
            r'what\s+(?:is\s+)?(?:this\s+)?(?:for|about)',
        ]
        
        # Check for mentions of the bot
        bot_mentioned = any(word in content for word in ['bot', 'tracker', '@'])
        
        # Check if any pattern matches
        for pattern in help_patterns:
            if re.search(pattern, content):
                return True
        
        # Additional simple keyword combinations
        help_keywords = ['help', 'how', 'what', 'commands', 'use', 'work']
        bot_keywords = ['bot', 'tracker', 'this', 'it']
        
        has_help_word = any(word in content for word in help_keywords)
        has_bot_word = any(word in content for word in bot_keywords)
        
        return has_help_word and (has_bot_word or bot_mentioned)
    
    async def on_message(self, message):
        """Handle incoming messages for auto-responses"""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Check for help questions (only if bot is mentioned or message contains bot keywords)
        if (self.user in message.mentions or 
            any(keyword in message.content.lower() for keyword in ['bot', 'tracker']) or
            message.content.startswith('!')) and self.is_help_question(message.content):
            
            await message.reply("**YOU RANG?!** 📢\n\nType `!help` for the list of commands! 🤖")
            return
        
        # Process commands normally
        await self.process_commands(message)
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'Bot logged in as {self.user} (ID: {self.user.id})')
        logger.info(f'Tracking {len(self.tracked_accounts)} accounts')
        
        # Start the tracking loop
        if not self.tracking_loop.is_running():
            self.tracking_loop.start()
    
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument. Use `!help {ctx.command}` for usage.")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send(f"❌ An error occurred: {error}")
    
    @tasks.loop(seconds=60)  # Check every minute, but respect the actual interval
    async def tracking_loop(self):
        """Main tracking loop that runs periodically"""
        try:
            # Only run if it's time for a check
            current_time = asyncio.get_event_loop().time()
            if hasattr(self, '_last_check'):
                if (current_time - self._last_check) < self.check_interval:
                    return
            
            self._last_check = current_time
            
            if not self.tracked_accounts:
                return
            
            logger.info(f"Running tracking check for {len(self.tracked_accounts)} accounts")
            
            total_level_ups = 0
            for account in self.tracked_accounts.copy():  # Copy to avoid modification during iteration
                try:
                    level_ups = self.tracker.track_characters_for_levelups(account, self.monitored_leagues)
                    
                    if level_ups:
                        total_level_ups += len(level_ups)
                        await self.send_level_up_notifications(level_ups)
                    
                    # Small delay between accounts
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error checking account {account}: {e}")
            
            if total_level_ups > 0:
                logger.info(f"Found {total_level_ups} level-ups this cycle")
                
        except Exception as e:
            logger.error(f"Error in tracking loop: {e}")
    
    async def send_level_up_notifications(self, level_ups):
        """Send Discord notifications for level-ups"""
        if not self.notification_channel_id:
            logger.warning("No notification channel set, skipping Discord notifications")
            return
        
        try:
            channel = self.get_channel(self.notification_channel_id)
            if not channel:
                logger.error(f"Could not find notification channel {self.notification_channel_id}")
                return
            
            for character, old_level, new_level in level_ups:
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"**{character.name}** reached Level **{new_level}** in **{character.league}**!",
                    color=0xff6b35
                )
                embed.add_field(name="Character", value=character.name, inline=True)
                embed.add_field(name="Class", value=character.class_name, inline=True)
                embed.add_field(name="League", value=character.league, inline=True)
                embed.add_field(name="Level Progress", value=f"{old_level} → {new_level}", inline=True)
                
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error sending level-up notification: {e}")
    
    def get_tracked_accounts(self) -> List[str]:
        """Get list of currently tracked accounts"""
        return list(self.tracked_accounts)