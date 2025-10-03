# Debugging

```bash
# 1. Check if server is running
curl http://localhost:5555/health

# 2. Test soundbar setup
curl -X POST http://localhost:5555/soundbar/setup

# 3. Test token exchange
curl -X POST http://localhost:5555/token/exchange

# 4. Test recommendation
curl -X POST http://localhost:5555/recommendation \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test prompt"}'

# 5. Test TTS generation
curl -X POST http://localhost:5555/tts/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "test audio", "filename": "test.mp3"}'

# 6. Test audio playback
curl -X POST http://localhost:5555/audio/play \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.mp3"}'

# 7. Test Spotify playback
curl -X POST http://localhost:5555/spotify/play \
  -H "Content-Type: application/json" \
  -d '{"song_query": "Bohemian Rhapsody Queen"}'

# 8. Playback status
curl http://localhost:5555/status

# All together
curl -X POST http://localhost:5555/serve \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I want something cosmic and ethereal"}'
```
