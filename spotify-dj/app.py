import threading
import os
import requests
import base64
import pygame
import time
from flask import Flask, request, jsonify
from openai import OpenAI
from pydantic import BaseModel
from typing import Tuple, List

SPOTIFY_DEVICE_ID = os.getenv("SPOTIFY_DEVICE_ID")

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
        # Check power status
        power_response = requests.get("http://localhost:5050/power")
        if power_response.status_code == 200:
            power_status = power_response.json().get("power_status")
            if not power_status:
                # Turn on soundbar
                setup_response = requests.post("http://localhost:5050/setup")
                if setup_response.status_code != 200:
                    print(f"Warning: Failed to turn on soundbar: {setup_response.text}")
        
        # Check current function
        func_response = requests.get("http://localhost:5050/func")
        if func_response.status_code == 200:
            current_func = func_response.json().get("func")
            if current_func != "6":
                # Set function to 6
                func_set_response = requests.post(
                    "http://localhost:5050/func",
                    headers={"Content-Type": "application/json"},
                    json={"func": 6}
                )
                if func_set_response.status_code != 200:
                    print(f"Warning: Failed to set soundbar function: {func_set_response.text}")
    except Exception as e:
        print(f"Warning: Soundbar setup failed: {e}")


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
    Play audio file using pygame, with full volume and no cropping.
    
    Args:
        filename: Path to the audio file.
        volume: Float between 0.0 (mute) and 1.0 (max).
    """
    try:
        if not os.path.exists(filename):
            raise RuntimeError(f"File does not exist: {filename}")

        # Initialize mixer early with a small buffer to avoid cropping
        if not pygame.mixer.get_init():
            pygame.mixer.init(buffer=512)  # smaller buffer = less latency

        # Stop anything that might be playing
        pygame.mixer.music.stop()

        # Load and set volume before play
        pygame.mixer.music.load(filename)
        pygame.mixer.music.set_volume(volume)

        # Give the mixer a moment to prepare (prevents cropping)
        pygame.time.delay(1000)

        # Start playback
        pygame.mixer.music.play()

        # Wait until playback finishes
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(20)

        # Clean up
        pygame.mixer.music.stop()
        pygame.mixer.quit()

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
    
    # Get current playback state
    response = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    
    if response.status_code == 204:
        return jsonify({"is_playing": False, "reason": "No active device"})
    
    if response.status_code != 200:
        return jsonify({"is_playing": False, "error": f"Spotify API error: {response.text}"}), 500
    
    player_data = response.json()

    return player_data.get("is_playing", False)


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
        print(f"Audio play request data: {data}")
        
        if not data or 'filename' not in data:
            print("Error: Missing filename in request body")
            return jsonify({"error": "Missing filename in request body"}), 400
        
        filename = data['filename']
        print(f"Attempting to play file: {filename}")
        
        # Check if file exists
        if not os.path.exists(filename):
            print(f"Error: File {filename} does not exist")
            return jsonify({"success": False, "error": f"File {filename} does not exist"}), 400
        
        print(f"File exists, attempting to play: {filename}")
        play_intro(filename)
        print(f"Successfully played: {filename}")
        
        return jsonify({"success": True, "message": f"Played {filename}"})
    except Exception as e:
        print(f"Error in audio play endpoint: {str(e)}")
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

    setup_soundbar()
    spotify_token = exchange_token()
    recommendation = get_song_from_prompt(prompt, previous_songs, previous_intros)
    song_query = recommendation["songSearch"]
    introduction = recommendation["introduction"]

    # record history
    previous_songs.append(song_query)
    previous_intros.append(introduction)

    # synthesize the spoken intro
    audio_file = speak_text(introduction)

    return song_query, audio_file, spotify_token


# global variables to track the background task
_bg_lock = threading.Lock()
_bg_thread = None
_stop_event = threading.Event()


def _serve_loop(prompt: str):
    """Infinifely fetch songs from the prompt and serve them"""

    _stop_event.clear()
    previous_songs = []
    previous_intros = []

    song, audio_file, token = _precompute(prompt, previous_songs, previous_intros)
    done = True

    while not _stop_event.is_set():
        try:
            play_intro(audio_file)
            spotify_play(song, token)

            done = False

            while is_playing(token):
                if _stop_event.is_set():
                    # TODO: Spotify stop
                    break
                if not done:
                    song, audio_file, token = _precompute(prompt, previous_songs, previous_intros)
                    done = True

                time.sleep(2)

            time.sleep(1)

        except Exception as e:
            print(f"Serve failed: {e}")
            break


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
    print("🎵 Starting Spotify DJ server on port 5555...")
    app.run(host='0.0.0.0', port=5555, debug=False)
