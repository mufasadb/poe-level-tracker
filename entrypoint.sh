#!/bin/bash

# Set default PUID and PGID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Create group if it doesn't exist
if ! getent group poe-tracker > /dev/null 2>&1; then
    groupadd -g $PGID poe-tracker
fi

# Create user if it doesn't exist
if ! id poe-tracker > /dev/null 2>&1; then
    useradd -u $PUID -g $PGID -m -s /bin/bash poe-tracker
fi

# Ensure data directory exists and has correct permissions
mkdir -p /app/data
chown -R poe-tracker:poe-tracker /app

# Switch to the poe-tracker user and run the command
exec gosu poe-tracker "$@"