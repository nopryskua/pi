# Soundbar Control

For LG SC9S

# Temescal

The current Soundbar control server is heavily based on the Temescal library.

https://github.com/google/python-temescal/blob/79e34f07517bd42d1d6fae0aa1d3a5ddf4873837/temescal/__init__.py

# Build & Run

```bash
docker build -t soundbar-server .
docker run --network=host -e SOUNDBAR_IP=192.168.1.113 soundbar-server
```

Now the server is listening at `5050`.

# Capabilities

```bash
# Volume control
curl -X POST -H "Content-Type: application/json" -d '{"volume":15}' http://localhost:5050/volume

curl http://localhost:5050/volume

# Mute control
curl http://localhost:5050/mute

curl -X POST -H "Content-Type: application/json" -d '{"mute": true}' http://localhost:5050/mute
curl -X POST -H "Content-Type: application/json" -d '{"mute": false}' http://localhost:5050/mute

...
```

# Desired Config

```bash
# Check if awake
curl http://localhost:5050/power

# Check "audio_source", not playing if "NO SIGNAL"
curl http://localhost:5050/status

# Awake
curl -X POST http://localhost:5050/wake

# Mid volume
curl -X POST -H "Content-Type: application/json" -d '{"volume":12}' http://localhost:5050/volume

# No EQ
curl -X POST -H "Content-Type: application/json" -d '{"eq":0}' http://localhost:5050/eq

# No mute
curl -X POST -H "Content-Type: application/json" -d '{"mute": false}' http://localhost:5050/mute

# HDMI
curl -X POST -H "Content-Type: application/json" -d '{"func":6}' http://localhost:5050/func
```
