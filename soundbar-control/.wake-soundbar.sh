#!/bin/bash

# Spotifyd on-song-change hook

STATUS=$(curl -s http://localhost:5050/power | jq -r '.power_status')

if [ "$STATUS" = "false" ]; then
    curl -s -X POST http://localhost:5050/setup
fi

CURRENT_FUNC=$(curl -s http://localhost:5050/func | jq -r '.func')

if [ "$CURRENT_FUNC" != "6" ]; then
    curl -s -X POST -H "Content-Type: application/json" -d '{"func":6}' http://localhost:5050/func
fi
