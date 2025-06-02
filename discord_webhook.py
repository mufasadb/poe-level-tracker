#!/usr/bin/env python3
"""
Discord webhook functionality for PoE character tracker
"""

import requests
import json
import os
from typing import Optional


class DiscordWebhook:
    """Handle Discord webhook notifications"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_message(self, message: str, username: str = "PoE Character Tracker") -> bool:
        """
        Send a simple text message to Discord
        
        Args:
            message (str): The message to send
            username (str): Bot username to display
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.webhook_url:
            print("Error: No webhook URL configured")
            return False
            
        payload = {
            "content": message,
            "username": username
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:  # Discord webhook success
                print(f"Discord message sent successfully: {message}")
                return True
            else:
                print(f"Discord webhook failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Error sending Discord message: {e}")
            return False
    
    def send_level_up_notification(self, character_name: str, league: str, old_level: int, new_level: int) -> bool:
        """
        Send a formatted level-up notification
        
        Args:
            character_name (str): Name of the character
            league (str): League name
            old_level (int): Previous level
            new_level (int): New level
            
        Returns:
            bool: True if successful, False otherwise
        """
        message = f"🎉 **Congrats {character_name} on reaching Level {new_level} in {league}!** 🎉"
        
        if old_level:
            message += f" (Level {old_level} → {new_level})"
        
        return self.send_message(message)
    
    def send_embed_message(self, title: str, description: str, color: int = 0x00ff00, fields: list = None) -> bool:
        """
        Send a rich embed message to Discord
        
        Args:
            title (str): Embed title
            description (str): Embed description
            color (int): Color of the embed (hex)
            fields (list): List of field dictionaries with 'name', 'value', 'inline' keys
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.webhook_url:
            print("Error: No webhook URL configured")
            return False
        
        embed = {
            "title": title,
            "description": description,
            "color": color
        }
        
        if fields:
            embed["fields"] = fields
        
        payload = {
            "embeds": [embed],
            "username": "PoE Character Tracker"
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                print(f"Discord embed sent successfully: {title}")
                return True
            else:
                print(f"Discord webhook failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Error sending Discord embed: {e}")
            return False


def test_discord_webhook():
    """Test Discord webhook functionality with environment variable"""
    
    # Get webhook URL from environment variable
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("Discord webhook test skipped - no webhook URL configured")
        print("To test Discord functionality:")
        print("1. Create a Discord webhook in your server")
        print("2. Set DISCORD_WEBHOOK_URL environment variable")
        print("3. Run this test again")
        return
    
    discord = DiscordWebhook(webhook_url)
    
    # Test simple message
    print("Testing simple message...")
    discord.send_message("Test message from PoE Character Tracker!")
    
    # Test level-up notification
    print("Testing level-up notification...")
    discord.send_level_up_notification("TestCharacter", "Standard", 85, 86)
    
    # Test embed message
    print("Testing embed message...")
    fields = [
        {"name": "Character", "value": "TestCharacter", "inline": True},
        {"name": "Class", "value": "Berserker", "inline": True},
        {"name": "League", "value": "Standard", "inline": True}
    ]
    discord.send_embed_message(
        "Level Up Detected!",
        "A character has gained a level!",
        0xff6b35,  # Orange color
        fields
    )


if __name__ == "__main__":
    test_discord_webhook()