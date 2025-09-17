import os
import time
import threading
from flask import Flask, jsonify, request
import temescal
import pychromecast
from pychromecast.controllers.media import MediaStatus

SOUNDBAR_IP = os.getenv("SOUNDBAR_IP", "192.168.1.113")
HTTP_PORT = int(os.getenv("PORT", 5050))

app = Flask(__name__)

# --- Global state for storing speaker responses ---
speaker_state = {
    "volume": None,
    "mute": None,
    "eq": None,
    "func": None,
    "play_info": None,
    "settings": None,
    "product_info": None,
    "power_status": None,
    "audio_source": None,
    "connect_status": None
}

# --- Global connection state ---
soundbar = None
connection_lock = threading.Lock()
last_connection_attempt = 0
CONNECTION_RETRY_DELAY = 5  # seconds between reconnection attempts

# --- Callback function for temescal responses ---
def speaker_callback(data):
    """Callback function to handle responses from the speaker"""
    try:
        # Parse the response data and update global state
        if isinstance(data, dict):
            # Handle SPK_LIST_VIEW_INFO (volume/mute/power info)
            if data.get("msg") == "SPK_LIST_VIEW_INFO" and "data" in data:
                speaker_data = data["data"]
                if "i_vol" in speaker_data:
                    speaker_state["volume"] = speaker_data["i_vol"]
                if "b_mute" in speaker_data:
                    speaker_state["mute"] = speaker_data["b_mute"]
                if "b_powerstatus" in speaker_data:
                    speaker_state["power_status"] = speaker_data["b_powerstatus"]
                if "s_audio_source" in speaker_data:
                    speaker_state["audio_source"] = speaker_data["s_audio_source"]
            
            # Handle EQ_VIEW_INFO (equalizer info)
            elif data.get("msg") == "EQ_VIEW_INFO" and "data" in data:
                speaker_data = data["data"]
                if "i_curr_eq" in speaker_data:
                    speaker_state["eq"] = speaker_data["i_curr_eq"]
            
            # Handle FUNC_VIEW_INFO (function info)
            elif data.get("msg") == "FUNC_VIEW_INFO" and "data" in data:
                speaker_data = data["data"]
                if "i_curr_func" in speaker_data:
                    speaker_state["func"] = speaker_data["i_curr_func"]
                if "b_connect" in speaker_data:
                    speaker_state["connect_status"] = speaker_data["b_connect"]
            
            # Handle PLAY_INFO (playback info)
            elif data.get("msg") == "PLAY_INFO" and "data" in data:
                # Merge new data with existing play_info
                if speaker_state["play_info"] is None:
                    speaker_state["play_info"] = {}
                speaker_state["play_info"].update(data["data"])
            
            # Handle SETTING_VIEW_INFO (settings info)
            elif data.get("msg") == "SETTING_VIEW_INFO" and "data" in data:
                # Merge new data with existing settings
                if speaker_state["settings"] is None:
                    speaker_state["settings"] = {}
                speaker_state["settings"].update(data["data"])
            
            # Handle PRODUCT_INFO (product info)
            elif data.get("msg") == "PRODUCT_INFO" and "data" in data:
                speaker_state["product_info"] = data["data"]
        
        print(f"Speaker callback received: {data}")
    except Exception as e:
        print(f"Error in speaker callback: {e}")

# --- Connection management functions ---
def create_soundbar_connection():
    """Create a new temescal connection to the soundbar"""
    global soundbar
    try:
        soundbar = temescal.temescal(SOUNDBAR_IP, callback=speaker_callback)
        print(f"Connected to soundbar at {SOUNDBAR_IP}")
        return True
    except Exception as e:
        print(f"Failed to connect to soundbar: {e}")
        soundbar = None
        return False

def ensure_connection():
    """Ensure we have a valid connection to the soundbar, reconnect if needed"""
    global soundbar, last_connection_attempt
    
    with connection_lock:
        current_time = time.time()
        
        # If we have a connection, try to use it
        if soundbar is not None:
            try:
                # Test the connection by making a simple request
                soundbar.get_info()
                return True
            except Exception as e:
                print(f"Connection test failed: {e}")
                soundbar = None
        
        # If no connection or connection failed, try to reconnect
        if soundbar is None and (current_time - last_connection_attempt) >= CONNECTION_RETRY_DELAY:
            print("Attempting to reconnect to soundbar...")
            last_connection_attempt = current_time
            return create_soundbar_connection()
        
        return soundbar is not None

def wake_soundbar(ip, retries=3, delay=2):
    """Wake up the soundbar using Google Cast protocol with retries"""
    attempt = 0
    while attempt < retries:
        try:
            print(f"Attempt {attempt+1}/{retries} to wake soundbar...")
            host = (ip, 8009, None, None, None)
            cast = pychromecast.get_chromecast_from_host(host)
            cast.wait()

            # Launch the Default Media Receiver app
            cast.start_app("CC1AD845")  # App ID for Default Media Receiver
            print("Launched Default Media Receiver")

            # Send a dummy media load (short mp3)
            mc = cast.media_controller
            mc.play_media(
                "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                "audio/mp3"
            )
            mc.block_until_active()
            mc.stop()
            print("Wake signal sent via dummy media")
            return True
        except Exception as e:
            print(f"Failed to wake soundbar on attempt {attempt+1}: {e}")
            attempt += 1
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    print("All attempts to wake soundbar failed.")
    return False

# --- Initialize temescal client ---
create_soundbar_connection()

# --- Flask routes ---
@app.route("/volume", methods=["GET"])
def get_volume():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request current volume from speaker
        soundbar.get_info()  # This gets SPK_LIST_VIEW_INFO which includes volume
        # Return the last known volume from our state
        return jsonify({"volume": speaker_state["volume"]})
    except Exception as e:
        print(f"Volume get error: {e}")
        return jsonify({"error": f"Failed to get volume: {str(e)}"}), 500

@app.route("/volume", methods=["POST"])
def set_volume():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    vol = request.json.get("volume")
    if vol is not None and 0 <= vol <= 100:
        try:
            soundbar.set_volume(vol)
            speaker_state["volume"] = vol  # Update local state
            return jsonify({"volume": vol})
        except Exception as e:
            print(f"Volume set error: {e}")
            return jsonify({"error": f"Failed to set volume: {str(e)}"}), 500
    return jsonify({"error": "Invalid volume"}), 400

@app.route("/mute", methods=["GET"])
def get_mute():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request current mute status from speaker
        soundbar.get_info()  # This gets SPK_LIST_VIEW_INFO which includes mute
        # Return the last known mute status from our state
        return jsonify({"mute": speaker_state["mute"]})
    except Exception as e:
        print(f"Mute get error: {e}")
        return jsonify({"error": f"Failed to get mute status: {str(e)}"}), 500

@app.route("/mute", methods=["POST"])
def set_mute():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    enable = request.json.get("mute")
    if isinstance(enable, bool):
        try:
            soundbar.set_mute(enable)
            speaker_state["mute"] = enable  # Update local state
            return jsonify({"mute": enable})
        except Exception as e:
            print(f"Mute set error: {e}")
            return jsonify({"error": f"Failed to set mute: {str(e)}"}), 500
    return jsonify({"error": "Invalid mute value"}), 400

@app.route("/eq", methods=["GET"])
def get_eq():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request current equalizer state from speaker
        soundbar.get_eq()
        # Return the last known eq state from our state
        return jsonify({"eq": speaker_state["eq"]})
    except Exception as e:
        print(f"EQ get error: {e}")
        return jsonify({"error": f"Failed to get equalizer state: {str(e)}"}), 500

@app.route("/eq", methods=["POST"])
def set_eq():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    eq_value = request.json.get("eq")
    if eq_value is not None and 0 <= eq_value <= 18:  # Based on equalisers list
        try:
            soundbar.set_eq(eq_value)
            speaker_state["eq"] = eq_value  # Update local state
            return jsonify({"eq": eq_value})
        except Exception as e:
            print(f"EQ set error: {e}")
            return jsonify({"error": f"Failed to set equalizer: {str(e)}"}), 500
    return jsonify({"error": "Invalid equalizer value (0-18)"}), 400

@app.route("/func", methods=["GET"])
def get_func():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request current function from speaker
        soundbar.get_func()
        # Return the last known func state from our state
        return jsonify({"func": speaker_state["func"]})
    except Exception as e:
        print(f"Func get error: {e}")
        return jsonify({"error": f"Failed to get function: {str(e)}"}), 500

@app.route("/func", methods=["POST"])
def set_func():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    func_value = request.json.get("func")
    if func_value is not None and 0 <= func_value <= 19:  # Based on functions list
        try:
            soundbar.set_func(func_value)
            speaker_state["func"] = func_value  # Update local state
            return jsonify({"func": func_value})
        except Exception as e:
            print(f"Func set error: {e}")
            return jsonify({"error": f"Failed to set function: {str(e)}"}), 500
    return jsonify({"error": "Invalid function value (0-19)"}), 400

@app.route("/play", methods=["GET"])
def get_play():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request current playback info from speaker
        soundbar.get_play()
        # Return the last known play info from our state
        return jsonify({"play_info": speaker_state["play_info"]})
    except Exception as e:
        print(f"Play get error: {e}")
        return jsonify({"error": f"Failed to get playback info: {str(e)}"}), 500

@app.route("/settings", methods=["GET"])
def get_settings():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request current settings from speaker
        soundbar.get_settings()
        # Return the last known settings from our state
        return jsonify({"settings": speaker_state["settings"]})
    except Exception as e:
        print(f"Settings get error: {e}")
        return jsonify({"error": f"Failed to get settings: {str(e)}"}), 500

@app.route("/product", methods=["GET"])
def get_product():
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request product info from speaker
        soundbar.get_product_info()
        # Return the last known product info from our state
        return jsonify({"product_info": speaker_state["product_info"]})
    except Exception as e:
        print(f"Product get error: {e}")
        return jsonify({"error": f"Failed to get product info: {str(e)}"}), 500

@app.route("/setup", methods=["POST"])
def setup():
    """Wake up the soundbar, set pleasant voice, no EQ, not muted, and HDMI output"""
    try:
        success = wake_soundbar(SOUNDBAR_IP)
        if not success:
            return jsonify({"error": "Failed to send wake signal"}), 500

        if not ensure_connection():
            return jsonify({"error": "Soundbar not connected"}), 500

        soundbar.set_volume(12) # Pleasant
        speaker_state["volume"] = 12  # Update local state

        soundbar.set_eq(0) # Off
        speaker_state["eq"] = 0  # Update local state

        soundbar.set_mute(False)
        speaker_state["mute"] = False  # Update local state

        soundbar.set_func(6) # HDMI
        speaker_state["func"] = 6  # Update local state

        return jsonify({"message": "Setup successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to setup soundbar: {str(e)}"}), 500

@app.route("/wake", methods=["POST"])
def wake():
    """Wake up the soundbar using Google Cast protocol"""
    try:
        success = wake_soundbar(SOUNDBAR_IP)
        if success:
            return jsonify({"message": "Wake signal sent successfully", "wake": True})
        else:
            return jsonify({"error": "Failed to send wake signal", "wake": False}), 500
    except Exception as e:
        return jsonify({"error": f"Failed to wake soundbar: {str(e)}", "wake": False}), 500

@app.route("/status", methods=["GET"])
def get_status():
    """Get comprehensive status of the soundbar"""
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request current status from speaker
        soundbar.get_info()
        soundbar.get_func()
        soundbar.get_settings()
        soundbar.get_play()

        return jsonify({
            "volume": speaker_state["volume"],
            "mute": speaker_state["mute"],
            "eq": speaker_state["eq"],
            "func": speaker_state["func"],
            "power_status": speaker_state["power_status"],
            "audio_source": speaker_state["audio_source"],
            "connect_status": speaker_state["connect_status"],
            "play_info": speaker_state["play_info"],
            "settings": speaker_state["settings"]
        })
    except Exception as e:
        print(f"Status get error: {e}")
        return jsonify({"error": f"Failed to get status: {str(e)}"}), 500

@app.route("/power", methods=["GET"])
def get_power():
    """Get power status of the soundbar"""
    if not ensure_connection():
        return jsonify({"error": "Soundbar not connected"}), 500
    try:
        # Request current status from speaker
        soundbar.get_info()
        return jsonify({"power_status": speaker_state["power_status"]})
    except Exception as e:
        print(f"Power get error: {e}")
        return jsonify({"error": f"Failed to get power status: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=HTTP_PORT)

