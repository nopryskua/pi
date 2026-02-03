## Build & Run

Note that the following variables should be set - `OPENAI_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` from Spotify UI, `SPOTIFY_REFRESH_TOKEN` from running `spotify-auth`, and `SPOTIFY_DEVICE_ID` from running the Spotify devices endpoint.

### Build the Docker image

```bash
docker build -t spotify-dj .
```

### Run the server

Note: It's not up to date since "pulseaudio" is replaced by pipewire (not fixing since spotifyd will be replaced)

```bash
docker run --rm \
  --network host \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e SPOTIFY_CLIENT_ID="$SPOTIFY_CLIENT_ID" \
  -e SPOTIFY_CLIENT_SECRET="$SPOTIFY_CLIENT_SECRET" \
  -e SPOTIFY_REFRESH_TOKEN="$SPOTIFY_REFRESH_TOKEN" \
  -e SPOTIFY_DEVICE_ID="$SPOTIFY_DEVICE_ID" \
  -e PULSE_SERVER=unix:/run/user/1000/pulse/native \
  -e SDL_AUDIODRIVER=pulseaudio \
  -v /run/user/1000/pulse:/run/user/1000/pulse \
  -e PYTHONUNBUFFERED=1 \
  spotify-dj
```

The server will start on port 5555 and provide the following endpoints:

### API Endpoints

#### POST /workflow/complete
Complete workflow: soundbar setup → token exchange → song recommendation → TTS generation → intro playback → Spotify playback

**Request:**
```bash
curl -X POST http://localhost:5555/workflow/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I want something cosmic and ethereal"}'
```

**Response:**
```json
{
  "success": true,
  "message": "Complete workflow executed successfully",
  "workflow_steps": [
    "soundbar_setup",
    "token_exchange", 
    "song_recommendation",
    "tts_generation",
    "intro_playback",
    "spotify_playback"
  ],
  "result": {
    "prompt": "I want something cosmic and ethereal",
    "song_query": "Space Oddity David Bowie",
    "introduction": "Prepare to journey through the cosmos...",
    "track": "Space Oddity",
    "artist": "David Bowie",
    "tts_file": "intro.mp3"
  }
}
```

#### GET /status
Check if something is currently playing on Spotify.

**Request:**
```bash
curl http://localhost:5555/status
```

**Response:**
```json
{
  "is_playing": true,
  "track": "Current Song",
  "artist": "Current Artist",
  "progress_ms": 45555,
  "duration_ms": 180000
}
```

#### GET /health
Health check endpoint.

**Request:**
```bash
curl http://localhost:5555/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Debugging Endpoints

For testing individual workflow steps:

- **POST /soundbar/setup** - Setup soundbar (power check and function setting)
- **POST /token/exchange** - Exchange refresh token for access token  
- **POST /recommendation** - Get song recommendation from prompt
- **POST /tts/generate** - Generate TTS audio from text
- **POST /audio/play** - Play audio file
- **POST /spotify/play** - Play song on Spotify

### Device Mounting

The `--device /dev/snd` flag is required to mount the audio device so the server can play the TTS introduction through the Raspberry Pi's audio output.
