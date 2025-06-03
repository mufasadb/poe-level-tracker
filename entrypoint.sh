#!/bin/bash

# Set default PUID and PGID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Get existing group name for the PGID, or create new one
GROUPNAME=$(getent group $PGID | cut -d: -f1)
if [ -z "$GROUPNAME" ]; then
    groupadd -g $PGID poe-tracker
    GROUPNAME="poe-tracker"
fi

# Get existing user name for the PUID, or create new one
USERNAME=$(getent passwd $PUID | cut -d: -f1)
if [ -z "$USERNAME" ]; then
    useradd -u $PUID -g $PGID -m -s /bin/bash poe-tracker
    USERNAME="poe-tracker"
fi

# Ensure data directory exists and has correct permissions
mkdir -p /app/data

# Set ownership using numeric IDs to avoid name conflicts
chown -R $PUID:$PGID /app

# Switch to the user and run the command
exec gosu $PUID:$PGID "$@"