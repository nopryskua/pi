import threading
import os
import requests
import base64
import pygame
import time
import sys
import logging
from flask import Flask, request, jsonify
from openai import OpenAI
from pydantic import BaseModel
from typing import Tuple, List

# Configure logging to ensure stdout is not buffered
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

SPOTIFY_DEVICE_ID = os.getenv("SPOTIFY_DEVICE_ID")

# Helper function to ensure logs are flushed immediately
def log(msg: str):
    """Print message with immediate flush to ensure Docker logs visibility."""
    print(msg, flush=True)

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI()

class SongRecommendation(BaseModel):
    songSearch: str
    introduction: str


def exchange_token():
    """Exchange refresh token for access token"""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError("Missing Spotify credentials")
    
    if not SPOTIFY_DEVICE_ID:
        raise RuntimeError("Spotify device ID should be set")
    
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    if response.status_code != 200:
        raise RuntimeError(f"Token exchange failed: {response.text}")
    
    return response.json()["access_token"]


def setup_soundbar():
    """Setup soundbar - check power and set function to 6"""
    try:
        # Call the /setup endpoint directly
        setup_response = requests.post("http://localhost:5050/setup")
        if setup_response.status_code != 200:
            log(f"Warning: Failed to setup soundbar: {setup_response.text}")
    except Exception as e:
        log(f"Warning: Soundbar setup failed: {e}")


def get_song_from_prompt(prompt: str, previous_songs: List[str], previous_intros: List[str]):
    """Get a song recommendation with context persistence and schema validation."""

    # Build context for non-repetition
    prev_songs_str = (
        f"Previous recommendations: {', '.join(previous_songs[-30:])}.\n"
        if previous_songs else ""
    )
    prev_intros_str = (
        f"Previous introductions: {' | '.join(previous_intros[-30:])}.\n"
        if previous_intros else ""
    )

    system_instructions = f"""
You are a precise music recommender.
Respond ONLY in JSON that validates against the schema.
Rules for `songSearch`:
- Track name and artist for Spotify search
- No quotes, no 'by'
- Example: Space Oddity David Bowie
The `introduction` should prepare the listener emotionally with around 2 poetic sentences mixed with the most interesting information about the track and the author.
{prev_songs_str}{prev_intros_str}
Do NOT repeat any previous song or introduction.
Ensure smooth transitioning from previous songs and introductions. The experience should create a feeling of an unfolding narrative.
"""

    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.responses.parse(
            model="gpt-5",
            input=messages,
            text_format=SongRecommendation,
        )

        return response.output_parsed.model_dump()
    except Exception as e:
        raise RuntimeError(f"OpenAI API failed: {e}")

def speak_text(text: str, filename="intro.mp3"):
    """Generate TTS audio using official OpenAI library"""
    try:

        instructions = f"""
Voice: Deep and resonant, with a velvety timbre that carries warmth and gravity. Each word feels grounded, like the voice of someone who has lived many lives and listens as deeply as they speak. But not snobby. Not too slow.
Tone: Reflective and soulful, with a calm, measured delivery. Emphasizes serenity and emotional depth rather than excitement, guiding the listener into a contemplative atmosphere. But not too slow.
Dialect: Neutral, clear, and articulate — no regionalisms. A subtle hint of poetic phrasing in everyday words, like a philosopher speaking casually but beautifully.
Pronunciation: Smooth and deliberate, with rounded vowels and softly emphasized consonants. Slight elongation of key words to let them linger in the air, like notes of music.
"""

        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="verse",
            input=text,
            instructions=instructions,
            response_format="mp3",
        )
        
        with open(filename, "wb") as f:
            for chunk in response.iter_bytes(chunk_size=4096):
                if chunk:
                    f.write(chunk)
        
        return filename
    except Exception as e:
        raise RuntimeError(f"TTS failed: {str(e)}")


def play_intro(filename: str, volume: float = 1.0):
    """
    Play audio file robustly using pygame with PipeWire/PulseAudio support.
    Prevents audio flickering and dropout by:
    - Pre-initializing mixer with stable sample rate (44.1 kHz)
    - Using adequate buffer size (4096) to prevent underruns
    - Waiting for mixer readiness before playback
    - Not quitting mixer to avoid expensive re-initialization
    
    Args:
        filename: Path to the audio file.
        volume: Float between 0.0 (mute) and 1.0 (max).
    """
    try:
        if not os.path.exists(filename):
            raise RuntimeError(f"File does not exist: {filename}")

        # Pre-initialize mixer with stable, compatible settings if not already done
        # This prevents sample-rate mismatches that cause flickering
        if not pygame.mixer.get_init():
            try:
                # Frequency: 44100 Hz (standard TTS rate)
                # Size: -16 (signed 16-bit)
                # Channels: 2 (stereo, safe for mono files)
                # Buffer: 4096 (large enough to avoid underruns, small enough for latency)
                pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
                pygame.mixer.init()
                log("Mixer initialized with 44100 Hz, 16-bit, stereo, buffer=4096")
            except Exception as e:
                log(f"Warning: pre_init failed, falling back to default: {e}")
                pygame.mixer.init(buffer=4096)

        # Stop any existing playback cleanly
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            time.sleep(0.1)  # Brief pause to let stop complete

        # Load the audio file
        pygame.mixer.music.load(filename)

        # Set volume
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

        # Wait for mixer to be fully ready (reduces initial crackling)
        time.sleep(0.2)

        # Start playback
        pygame.mixer.music.play()
        log(f"Playing {filename} at volume {volume}")

        # Poll for completion with adaptive sleep to reduce CPU usage
        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            clock.tick(10)  # Lower tick rate (10 fps) to reduce overhead

        # Stop cleanly but keep mixer alive for reuse
        pygame.mixer.music.stop()
        log(f"Finished playing {filename}")
    except pygame.error as e:
        raise RuntimeError(f"Pygame audio error: {e}")
    except Exception as e:
        raise RuntimeError(f"Audio playback failed: {e}")

def spotify_pause(spotify_token: str):
    headers = {"Authorization": f"Bearer {spotify_token}", "Content-Type": "application/json"}

    resp = requests.put(
        "https://api.spotify.com/v1/me/player/pause",
        headers=headers,
        params={"device_id": SPOTIFY_DEVICE_ID}
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Pause failed: {resp.status_code} – {resp.text}")

def spotify_resume(spotify_token: str):
    headers = {"Authorization": f"Bearer {spotify_token}", "Content-Type": "application/json"}

    resp = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        headers=headers,
        params={"device_id": SPOTIFY_DEVICE_ID}
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(f"Resume failed: {resp.status_code} – {resp.text}")


def spotify_play(song_query: str, spotify_token: str):
    """Play a song on Spotify"""

    headers = {"Authorization": f"Bearer {spotify_token}", "Content-Type": "application/json"}

    # Search track
    search_resp = requests.get(
        "https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": song_query, "type": "track", "limit": 1}
    )
    tracks = search_resp.json().get("tracks", {}).get("items", [])
    if not tracks:
        raise RuntimeError("No matching track found: {song_query}")

    track = tracks[0]

    # Play track
    play_resp = requests.put(
        "https://api.spotify.com/v1/me/player/play",
        headers=headers,
        params={"device_id": SPOTIFY_DEVICE_ID},
        json={"uris": [track["uri"]]}
    )
    if play_resp.status_code not in (200, 204):
        raise RuntimeError(f"Play failed: {play_resp.text}")
    
    return track


def is_playing(spotify_token: str):
    """Check if something is playing on Spotify"""

    headers = {"Authorization": f"Bearer {spotify_token}"}

    # Get current playback state; always return a boolean
    try:
        response = requests.get("https://api.spotify.com/v1/me/player", headers=headers, timeout=10)
    except Exception as e:
        log(f"[is_playing] Error fetching playback state: {e}")
        return False

    if response.status_code == 204:
        # No active device
        return False

    if response.status_code != 200:
        log(f"[is_playing] Spotify API error: {response.status_code} - {response.text}")
        return False

    try:
        player_data = response.json()
    except Exception as e:
        log(f"[is_playing] Failed to parse Spotify response JSON: {e}")
        return False

    return bool(player_data.get("is_playing", False))


# Individual workflow endpoints for debugging


@app.route('/health', methods=['GET'])
def health_endpoint():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


@app.route('/soundbar/setup', methods=['POST'])
def soundbar_setup_endpoint():
    """Setup soundbar - check power and set function to 6"""
    try:
        setup_soundbar()
        return jsonify({"success": True, "message": "Soundbar setup completed"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/token/exchange', methods=['POST'])
def token_exchange_endpoint():
    """Exchange refresh token for access token"""
    try:
        token = exchange_token()
        return jsonify({"success": True, "access_token": token})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/recommendation', methods=['POST'])
def recommendation_endpoint():
    """Get song recommendation and introduction from prompt"""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing prompt in request body"}), 400
        
        result = get_song_from_prompt(data['prompt'], [], [])

        return jsonify({"success": True, "recommendation": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/tts/generate', methods=['POST'])
def tts_generate_endpoint():
    """Generate TTS audio from text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing text in request body"}), 400
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return jsonify({"error": "Missing OPENAI_API_KEY"}), 500
        
        filename = data.get('filename', 'intro.mp3')
        audio_file = speak_text(data['text'], filename)
        return jsonify({"success": True, "filename": audio_file})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/audio/play', methods=['POST'])
def play_audio_endpoint():
    """Play audio file"""
    try:
        data = request.get_json()
        log(f"Audio play request data: {data}")
        
        if not data or 'filename' not in data:
            log("Error: Missing filename in request body")
            return jsonify({"error": "Missing filename in request body"}), 400
        
        filename = data['filename']
        log(f"Attempting to play file: {filename}")
        
        # Check if file exists
        if not os.path.exists(filename):
            log(f"Error: File {filename} does not exist")
            return jsonify({"success": False, "error": f"File {filename} does not exist"}), 400
        
        log(f"File exists, attempting to play: {filename}")
        play_intro(filename)
        log(f"Successfully played: {filename}")
        
        return jsonify({"success": True, "message": f"Played {filename}"})
    except Exception as e:
        log(f"Error in audio play endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/spotify/play', methods=['POST'])
def spotify_play_endpoint():
    """Play song on Spotify"""
    try:
        data = request.get_json()
        if not data or 'song_query' not in data:
            return jsonify({"error": "Missing song_query in request body"}), 400
        
        spotify_token = exchange_token()

        track = spotify_play(data['song_query'], spotify_token)

        return jsonify({
            "success": True,
            "track": track["name"],
            "artist": track["artists"][0]["name"],
            "uri": track["uri"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/spotify/pause', methods=['POST'])
def spotify_pause_endpoint():
    try:
        spotify_token = exchange_token()

        spotify_pause(spotify_token)

        return jsonify({
            "success": True,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/spotify/resume', methods=['POST'])
def spotify_resume_endpoint():
    """Play song on Spotify"""
    try:
        spotify_token = exchange_token()

        spotify_resume(spotify_token)

        return jsonify({
            "success": True,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status_endpoint():
    """Endpoint to check if something is playing on Spotify"""
    try:
        spotify_token = exchange_token()

        result = {"is_playing": is_playing(spotify_token)}
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"is_playing": False, "error": str(e)}), 500


def _precompute(prompt: str, previous_songs: List[str], previous_intros: List[str]) -> Tuple[str, str, str]:
    """Do everything except the play_intro/spotify_play bits."""

    log(f"\n[_precompute] Starting precompute with prompt: {prompt}")

    log(f"[_precompute] Exchanging Spotify token...")
    spotify_token = exchange_token()

    log(f"[_precompute] Requesting song recommendation from OpenAI...")
    recommendation = get_song_from_prompt(prompt, previous_songs, previous_intros)
    song_query = recommendation["songSearch"]
    introduction = recommendation["introduction"]

    log(f"[_precompute] 📝 Song recommendation: {song_query}")
    log(f"[_precompute] 📝 Introduction text: {introduction}")

    # record history
    previous_songs.append(song_query)
    previous_intros.append(introduction)
    log(f"[_precompute] Recorded history (total songs: {len(previous_songs)})")

    # synthesize the spoken intro
    log(f"[_precompute] Generating TTS audio from introduction...")
    audio_file = speak_text(introduction)
    log(f"[_precompute] ✅ TTS generated: {audio_file}")

    log(f"[_precompute] Precompute complete")
    return song_query, audio_file, spotify_token


# global variables to track the background task
_bg_lock = threading.Lock()
_bg_thread = None
_stop_event = threading.Event()


def _serve_loop(prompt: str):
    """Infinifely fetch songs from the prompt and serve them"""

    log(f"\n🎵 [_serve_loop] Starting serve loop with prompt: {prompt}")
    _stop_event.clear()
    previous_songs = []
    previous_intros = []

    log(f"[_serve_loop] Setting up soundbar...")
    setup_soundbar()

    song, audio_file, token = _precompute(prompt, previous_songs, previous_intros)
    done = True

    while not _stop_event.is_set():
        try:
            log(f"\n[_serve_loop] 🔊 Playing intro: {audio_file}")
            play_intro(audio_file)
            log(f"[_serve_loop] ✅ Intro playback complete")

            time.sleep(3) # Sleeping between intro and music
            log(f"[_serve_loop] ⏳ Waited 3s before starting Spotify...")

            log(f"[_serve_loop] 🎶 Starting Spotify playback: {song}")
            spotify_play(song, token)
            log(f"[_serve_loop] ✅ Spotify playback started")

            time.sleep(30) # Waiting to start playing
            log(f"[_serve_loop] ⏳ Waited 30s for song to start...")

            done = False

            while is_playing(token):
                if _stop_event.is_set():
                    log(f"[_serve_loop] 🛑 Stop event received, breaking playback loop")

                    # TODO: Spotify stop
                    break
                if not done:
                    log(f"[_serve_loop] Song still playing, precomputing next song...")
                    song, audio_file, token = _precompute(prompt, previous_songs, previous_intros)
                    done = True
                    log(f"[_serve_loop] ✅ Next song precomputed and ready")

                time.sleep(2)

            log(f"[_serve_loop] Song finished, waiting before next cycle...")
            time.sleep(5)

        except Exception as e:
            import traceback
            log(f"\n❌ [_serve_loop] Serve failed: {e}")
            traceback.print_exc()
            break

    log(f"\n🛑 [_serve_loop] Serve loop ended")


@app.route('/serve', methods=['POST'])
def serve():
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing prompt"}), 400

    prompt = data['prompt']

    global _bg_thread
    with _bg_lock:
        # guardrail: are we already running?
        if _bg_thread and _bg_thread.is_alive():
            return jsonify({"error": "Already serving"}), 409

        # start the background thread
        _bg_thread = threading.Thread(target=_serve_loop, args=(prompt,))
        _bg_thread.daemon = True
        _bg_thread.start()

    # immediately return to caller
    return jsonify({"success": True, "message": "Service started"}), 202


@app.route('/abort', methods=['POST'])
def abort():
    global _bg_thread
    if _bg_thread and _bg_thread.is_alive():
        _stop_event.set()
        return jsonify({"success": True, "message": "Serve loop aborted"}), 200
    return jsonify({"error": "No serve loop running"}), 400


if __name__ == "__main__":
    log("🎵 Starting Spotify DJ server on port 5555...")
    sys.stdout.flush()
    sys.stderr.flush()
    app.run(host='0.0.0.0', port=5555, debug=False, use_reloader=False)
