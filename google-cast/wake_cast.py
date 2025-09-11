#!/usr/bin/env python3
import os
import pychromecast
from pychromecast.controllers.media import MediaStatus

CAST_IP = os.environ.get("CAST_IP", "192.168.1.113")

def wake_cast(ip):
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

if __name__ == "__main__":
    wake_cast(CAST_IP)

