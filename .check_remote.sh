#!/bin/bash

REMOTE_URL="https://1.1.1.1"
LOG_FILE="~/.check_remote.log"

# Try to reach remote, quietly
if ! curl -s --head --fail "$REMOTE_URL" >/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Remote unreachable" >> "$LOG_FILE"
fi
