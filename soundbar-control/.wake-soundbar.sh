#!/bin/bash

# Spotifyd on-song-change hook

STATUS=$(curl -s http://localhost:5050/power | jq -r '.power_status')

if [ "$STATUS" = "false" ]; then
    # Wake the soundbar
    curl -s -X POST http://localhost:5050/wake

    # Set pleasant volume
    curl -s -X POST -H "Content-Type: application/json" -d '{"volume":12}' http://localhost:5050/volume

    # No EQ
    curl -s -X POST -H "Content-Type: application/json" -d '{"eq":0}' http://localhost:5050/eq

    # Ensure not muted
    curl -s -X POST -H "Content-Type: application/json" -d '{"mute": false}' http://localhost:5050/mute
fi

CURRENT_FUNC=$(curl -s http://localhost:5050/func | jq -r '.func')

if [ "$CURRENT_FUNC" != "6" ]; then
    curl -s -X POST -H "Content-Type: application/json" -d '{"func":6}' http://localhost:5050/func
fi
