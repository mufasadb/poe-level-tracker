Path of Exile Level-Up Tracker & Discord Bot - Junior Developer Tasks
Overarching Goal:

Develop a robust, automated system (Discord Bot) that monitors a predefined list of Path of Exile characters across specified leagues using the official PoE API. When a monitored character levels up, the system will announce this event in a designated Discord channel, ensuring respectful API usage by adhering to rate limits. The system will be easily deployable on Unraid via Docker.

Tasks for a Junior Developer:
Phase 1: Research, Setup & API Strategy
Task: Research PoE API & Define Access Strategy

Description:

Locate and thoroughly read the official Path of Exile API documentation. Focus on endpoints for retrieving character information (level, experience, class, current league).

Investigate and decide on the primary authentication method:

Can public character data be accessed without auth if profiles are public?

Is an API key available/required for this type of access?

Is OAuth 2.0 necessary? If so, what's the flow?

Research if PoE API access can be linked or simplified for users through Discord authentication (e.g., a bot command that initiates a PoE OAuth flow, with the bot securely managing tokens). This might be an advanced/stretch goal; initial focus on simplest viable auth for public data.

Note any required headers (like User-Agent) and data privacy implications.

Acceptance Criteria: Dev can clearly explain the chosen API access method, authentication flow (if any), and any prerequisites for tracking a character (e.g., public profile). Potential for Discord auth integration is assessed. Dev has URLs for relevant API endpoints and understands how to get league information.

Task: Setup Development Environment & Basic API Client

Description: Set up a Python development environment. Write a simple Python script using the requests library to make a GET request to a public PoE character API endpoint based on the chosen access strategy (using a known public character for testing). The script should print the raw JSON response.

Acceptance Criteria: Script successfully fetches and prints JSON data for a test character, including their league. Dependencies (requests) are managed (e.g., in requirements.txt).

Task: Understand and Implement Rate Limit Awareness (Initial)

Description: Research PoE API rate limits from the documentation. Modify the test script to inspect response headers for rate limit information. Log these values.

Acceptance Criteria: Script can output the current rate limit status after an API call.

Phase 2: Core Logic - Tracking Levels & Leagues
Task: Parse Character Data from API Response

Description: Modify the script to parse the JSON response from the character API and extract the character's name, current level, and current league.

Acceptance Criteria: Script can take an account name and character name as input (hardcoded for now) and output "Character [Name] (League: [LeagueName]) is Level [Level]".

Task: Implement Basic Data Storage (In-Memory)

Description: Create a Python dictionary to store the last known level and league for a few hardcoded test characters (e.g., {'CharacterName1': {'level': 75, 'league': 'Standard'}, ...}).

Acceptance Criteria: Data structure for storing character data is implemented.

Task: Detect Level-Up Events (League Aware)

Description: Create a function that, for a given character:

Fetches their current level and league via the API.

Compares it to the stored level for that league.

If the current level is higher, prints a "Level Up!" message and updates the stored level and league in the dictionary. Handles cases where a character might appear in a new league (e.g., after a league start).

Acceptance Criteria: Function correctly identifies a level up for a test character and updates the in-memory store, considering the character's league.

Phase 3: Discord Integration & Configuration
Task: Basic Discord Message Posting

Description: Write a function that takes a message string and posts it to a hardcoded Discord channel using a Webhook URL.

Acceptance Criteria: A test message from the Python script appears in the target Discord channel.

Task: Integrate Level-Up Detection with Discord Notification

Description: When a level-up is detected, use the Discord posting function to send a formatted message (e.g., "Congrats CharacterName on reaching Level X in [LeagueName]!").

Acceptance Criteria: Level-up events trigger a league-aware Discord message.

Task: Persistent Data Storage (File-based)

Description: Modify data storage to read from and write to a local JSON file (e.g., tracked_characters_data.json). This file should store character names, their last known levels, and their last known leagues. Load on startup, save on updates.

Acceptance Criteria: Character data (level, league) persists between script restarts.

Task: Configuration for Tracked Characters & Leagues

Description:

Allow the list of characters to be tracked to be easily configured (e.g., in the tracked_characters_data.json or a separate config file).

Add a configuration option (e.g., in the same config file or via environment variable) to specify a list of leagues to actively monitor (e.g., ["LeagueName1", "ChallengeLeagueHardcore"]). The bot should only process/report level-ups for characters currently in one of these specified leagues.

Acceptance Criteria: The script processes only characters in configured leagues. New characters can be added with their target account/name.

Phase 4: Refinement, Error Handling & Deployment
Task: Implement Robust Rate Limiting Handling

Description: Implement proper handling of API rate limits. Before making a batch of API calls, check current status. If close to limit, wait. Implement back-off strategy for HTTP 429 errors.

Acceptance Criteria: The script avoids hitting rate limits and handles them gracefully.

Task: Looping and Scheduling

Description: Structure the main script to loop through configured characters (respecting league filters), check their levels, and sleep for a configurable interval.

Acceptance Criteria: The script runs continuously, checking characters in specified leagues periodically.

Task: Error Handling & Logging

Description: Add comprehensive error handling (e.g., API errors, network issues, characters not found, private profiles, character not in a monitored league). Implement basic logging.

Acceptance Criteria: Script handles common errors without crashing and provides useful log output.

Task: Containerize with Docker

Description: Create a Dockerfile to package the application.

Acceptance Criteria: Application can be built and run as a Docker container.

Task: Update README with Unraid Docker Deployment Instructions

Description: Create/update a README.md file in the project. Include clear, step-by-step instructions on how to deploy and configure the Docker container on an Unraid server. This should cover:

Pulling the image (or building, if applicable).

Setting necessary environment variables (Discord Webhook, API keys if any, check interval, monitored leagues list).

Mapping the persistent storage volume for tracked_characters_data.json.

Basic troubleshooting tips based on logs.

Acceptance Criteria: A user familiar with Unraid can deploy and run the bot using the README.