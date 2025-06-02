#!/usr/bin/env python3
"""
Basic PoE API client for testing character data retrieval.
Based on research findings:
- Endpoint: https://www.pathofexile.com/character-window/get-characters
- Parameters: accountName (required), realm (optional, defaults to PC)
- Public access available for accounts with public character profiles
"""

import requests
import json
import sys


def fetch_character_data(account_name, realm="pc"):
    """
    Fetch character data from PoE API for a given account.
    
    Args:
        account_name (str): The PoE account name
        realm (str): The realm (pc, xbox, sony) - defaults to pc
    
    Returns:
        dict: JSON response from the API
    """
    url = "https://www.pathofexile.com/character-window/get-characters"
    
    params = {
        "accountName": account_name,
        "realm": realm
    }
    
    headers = {
        "User-Agent": "PoE-Character-Tracker/1.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            print("Error: Account profile is private")
            return None
        elif response.status_code == 404:
            print("Error: Account name is incorrect")
            return None
        else:
            print(f"Error: Unexpected status code {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None


def main():
    # Test with known public account (new format with discriminator)
    test_account = "dtmhawk#4430"  # Known public profile with discriminator
    
    print(f"Testing PoE API with account: {test_account}")
    data = fetch_character_data(test_account)
    
    if data:
        print("Raw JSON Response:")
        print(json.dumps(data, indent=2))
    else:
        print("Failed to fetch character data - may need different auth method")


if __name__ == "__main__":
    main()