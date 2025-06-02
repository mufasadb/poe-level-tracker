#!/usr/bin/env python3
"""
Path of Exile Character Level Tracker
Monitors character levels and detects level-ups for Discord notifications
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional, Tuple


class RateLimitTracker:
    """Track and manage PoE API rate limits"""
    
    def __init__(self):
        self.limits = {}  # window_seconds: (current_requests, max_requests)
        self.last_request_time = 0
        self.backoff_until = 0
    
    def parse_rate_limit_headers(self, headers: Dict[str, str]):
        """Parse rate limit headers and update internal state"""
        if 'X-Rate-Limit-Ip' in headers and 'X-Rate-Limit-Ip-State' in headers:
            # Parse limits: "15:60:120,90:1800:600,180:7200:3600"
            # Format: requests:window_seconds:max_requests
            limits_str = headers['X-Rate-Limit-Ip']
            state_str = headers['X-Rate-Limit-Ip-State']
            
            # Parse current state: "1:60:0,1:1800:0,1:7200:0"
            # Format: current_requests:window_seconds:hits_in_window
            state_parts = state_str.split(',')
            
            for state_part in state_parts:
                try:
                    current, window, hits = map(int, state_part.split(':'))
                    self.limits[window] = (current, self._get_max_for_window(limits_str, window))
                except ValueError:
                    continue
                    
    def _get_max_for_window(self, limits_str: str, window: int) -> int:
        """Extract max requests for a specific window from limits string"""
        for limit_part in limits_str.split(','):
            try:
                requests, win_sec, max_req = map(int, limit_part.split(':'))
                if win_sec == window:
                    return max_req
            except ValueError:
                continue
        return 0
    
    def update_from_headers(self, headers: Dict[str, str]):
        """Update rate limit info from API response headers"""
        self.parse_rate_limit_headers(headers)
        
        if self.limits:
            print(f"Rate limits: {self.limits}")
            
            # Check if we're close to any limits (80% threshold)
            for window, (current, max_req) in self.limits.items():
                if max_req > 0 and current / max_req >= 0.8:
                    print(f"Warning: Close to rate limit for {window}s window: {current}/{max_req}")
    
    def can_make_request(self) -> bool:
        """Check if we can safely make another request"""
        current_time = time.time()
        
        # Check if we're in a backoff period
        if current_time < self.backoff_until:
            return False
        
        # Check rate limits
        for window, (current, max_req) in self.limits.items():
            if max_req > 0 and current >= max_req:
                print(f"Rate limit reached for {window}s window: {current}/{max_req}")
                return False
        
        # Enforce minimum delay between requests (1 second)
        if current_time - self.last_request_time < 1.0:
            return False
        
        return True
    
    def wait_if_needed(self):
        """Wait if we need to respect rate limits"""
        while not self.can_make_request():
            time.sleep(1)
    
    def record_request(self):
        """Record that we made a request"""
        self.last_request_time = time.time()
    
    def handle_rate_limit_error(self, retry_after: int = None):
        """Handle a 429 rate limit error"""
        if retry_after:
            self.backoff_until = time.time() + retry_after
            print(f"Rate limited, backing off for {retry_after} seconds")
        else:
            # Default backoff
            self.backoff_until = time.time() + 60
            print("Rate limited, backing off for 60 seconds")


class CharacterData:
    """Represents a PoE character"""
    
    def __init__(self, name: str, realm: str, class_name: str, league: str, level: int):
        self.name = name
        self.realm = realm
        self.class_name = class_name
        self.league = league
        self.level = level
    
    def __repr__(self):
        return f"Character({self.name}, {self.class_name}, Level {self.level}, {self.league})"


class PoECharacterTracker:
    """Main character tracking class"""
    
    def __init__(self, data_file: str = None):
        if data_file is None:
            # Use the data directory if it exists, otherwise current directory
            data_dir = "/app/data" if os.path.exists("/app/data") else "."
            data_file = os.path.join(data_dir, "tracked_characters_data.json")
        self.rate_limiter = RateLimitTracker()
        self.data_file = data_file
        
        # Storage format: {character_name: {league: {level: int, last_updated: timestamp}}}
        self.character_data: Dict[str, Dict[str, Dict[str, any]]] = {}
        
        # Load existing data
        self.load_character_data()
        
    def fetch_account_characters(self, account_name: str, realm: str = "pc") -> Optional[List[CharacterData]]:
        """
        Fetch all characters for an account from PoE API
        
        Args:
            account_name (str): Account name with discriminator (e.g., "dtmhawk#4430")
            realm (str): Realm (pc, xbox, sony)
        
        Returns:
            List of CharacterData objects, or None if failed
        """
        # Wait if rate limiting is needed
        self.rate_limiter.wait_if_needed()
            
        url = "https://www.pathofexile.com/character-window/get-characters"
        params = {"accountName": account_name, "realm": realm}
        headers = {"User-Agent": "PoE-Character-Tracker/1.0"}
        
        try:
            # Record that we're making a request
            self.rate_limiter.record_request()
            
            response = requests.get(url, params=params, headers=headers)
            self.rate_limiter.update_from_headers(response.headers)
            
            if response.status_code == 200:
                characters_data = response.json()
                characters = []
                
                for char_data in characters_data:
                    character = CharacterData(
                        name=char_data['name'],
                        realm=char_data['realm'],
                        class_name=char_data['class'],
                        league=char_data['league'],
                        level=char_data['level']
                    )
                    characters.append(character)
                
                return characters
                
            elif response.status_code == 403:
                print(f"Error: Account '{account_name}' profile is private")
                return None
            elif response.status_code == 404:
                print(f"Error: Account '{account_name}' not found")
                return None
            elif response.status_code == 429:
                # Handle rate limiting
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    self.rate_limiter.handle_rate_limit_error(int(retry_after))
                else:
                    self.rate_limiter.handle_rate_limit_error()
                return None
            else:
                print(f"Error: Unexpected status code {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
    
    def get_character_by_name(self, account_name: str, character_name: str) -> Optional[CharacterData]:
        """Get a specific character by name from an account"""
        characters = self.fetch_account_characters(account_name)
        if characters:
            for char in characters:
                if char.name == character_name:
                    return char
        return None
    
    def load_character_data(self):
        """Load character data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.character_data = json.load(f)
                print(f"Loaded character data from {self.data_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading character data: {e}")
                self.character_data = {}
        else:
            print(f"No existing data file found at {self.data_file}")
    
    def save_character_data(self):
        """Save character data to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.character_data, f, indent=2)
            print(f"Character data saved to {self.data_file}")
        except IOError as e:
            print(f"Error saving character data: {e}")
    
    def store_character_data(self, character: CharacterData):
        """Store character data in memory cache and save to file"""
        char_name = character.name
        league = character.league
        
        if char_name not in self.character_data:
            self.character_data[char_name] = {}
        
        self.character_data[char_name][league] = {
            'level': character.level,
            'class': character.class_name,
            'last_updated': time.time()
        }
        
        # Save to file after updating
        self.save_character_data()
    
    def check_level_up(self, character: CharacterData) -> bool:
        """
        Check if character has leveled up since last check
        Returns True if level up detected, False otherwise
        """
        char_name = character.name
        league = character.league
        current_level = character.level
        
        # If we haven't seen this character/league combo before, store it and return False
        if (char_name not in self.character_data or 
            league not in self.character_data[char_name]):
            self.store_character_data(character)
            print(f"First time tracking {char_name} in {league} - Level {current_level}")
            return False
        
        # Check if level increased
        stored_level = self.character_data[char_name][league]['level']
        if current_level > stored_level:
            print(f"LEVEL UP! {char_name} ({league}): Level {stored_level} -> {current_level}")
            self.store_character_data(character)  # Update stored data
            return True
        
        # Check if character moved to different league (league start)
        elif current_level != stored_level:
            print(f"Character {char_name} level changed in {league}: {stored_level} -> {current_level}")
            self.store_character_data(character)  # Update stored data
            return False
        
        return False
    
    def track_characters_for_levelups(self, account_name: str, monitored_leagues: List[str] = None) -> List[Tuple[CharacterData, int, int]]:
        """
        Check all characters for level ups, optionally filtered by leagues
        Returns list of (character, old_level, new_level) tuples for level ups
        """
        if monitored_leagues is None:
            monitored_leagues = []  # Track all leagues if none specified
            
        characters = self.fetch_account_characters(account_name)
        if not characters:
            return []
        
        level_ups = []
        
        for character in characters:
            # Skip if we're monitoring specific leagues and this isn't one of them
            if monitored_leagues and character.league not in monitored_leagues:
                continue
                
            # Store old level before checking
            old_level = None
            if (character.name in self.character_data and 
                character.league in self.character_data[character.name]):
                old_level = self.character_data[character.name][character.league]['level']
            
            # Check for level up
            if self.check_level_up(character):
                level_ups.append((character, old_level, character.level))
        
        return level_ups
    
    def print_character_info(self, character: CharacterData):
        """Print formatted character information"""
        print(f"Character {character.name} (League: {character.league}) is Level {character.level}")
    
    def print_stored_data(self):
        """Print all stored character data for debugging"""
        print("\n=== Stored Character Data ===")
        for char_name, leagues in self.character_data.items():
            for league, data in leagues.items():
                print(f"{char_name} ({league}): Level {data['level']}, Class: {data['class']}")


def main():
    """Test the character tracker with level-up detection"""
    tracker = PoECharacterTracker()
    
    # Test with known public account
    test_account = "dtmhawk#4430"
    
    print("=== Testing Character Tracker ===")
    print(f"Account: {test_account}")
    
    # First check - should store initial data
    print("\n--- First Check (Initial Data Storage) ---")
    level_ups = tracker.track_characters_for_levelups(test_account, ["Standard", "Hardcore", "Settlers", "Phrecia"])
    print(f"Level ups detected: {len(level_ups)}")
    
    # Show stored data
    tracker.print_stored_data()
    
    # Second check - should detect no level ups (same data)
    print("\n--- Second Check (Should detect no changes) ---")
    level_ups = tracker.track_characters_for_levelups(test_account, ["Standard", "Hardcore", "Settlers", "Phrecia"])
    print(f"Level ups detected: {len(level_ups)}")
    
    # Simulate testing with a specific character for more detailed output
    print("\n--- Testing Individual Character Methods ---")
    characters = tracker.fetch_account_characters(test_account)
    if characters and len(characters) > 0:
        test_char = characters[0]
        print(f"Testing with character: {test_char.name}")
        tracker.print_character_info(test_char)
        
        # Test level up detection (should return False since already stored)
        level_up_detected = tracker.check_level_up(test_char)
        print(f"Level up detected: {level_up_detected}")
    
    print("\n=== Test Complete ===")
    
    # Show what leagues we found
    print("\n--- Available Leagues ---")
    if characters:
        leagues = set()
        for char in characters:
            leagues.add(char.league)
        print(f"Leagues found: {sorted(leagues)}")


if __name__ == "__main__":
    main()