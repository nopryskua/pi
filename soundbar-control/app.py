import os
import json
import socket
import struct
from threading import Thread
from flask import Flask, jsonify, request
from Crypto.Cipher import AES

SOUNDBAR_IP = os.getenv("SOUNDBAR_IP", "192.168.1.113")
SOUNDBAR_PORT = 9741
HTTP_PORT = int(os.getenv("PORT", 5050))

app = Flask(__name__)

# --- Temescal-like connection ---
class SoundbarClient:
    def __init__(self, ip, port=9741):
        self.ip = ip
        self.port = port
        self.iv = b'\'%^Ur7gy$~t+f)%@'
        self.key = b'T^&*J%^7tr~4^%^&I(o%^!jIJ__+a0 k'
        self.socket = None
        self.volume = None
        self.mute = None
        self.connect()
        self.thread = Thread(target=self.listen, daemon=True)
        self.thread.start()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))
        print(f"Connected to {self.ip}:{self.port}")

    def encrypt_packet(self, data):
        padlen = 16 - (len(data) % 16)
        data = data + chr(padlen) * padlen
        data = data.encode("utf-8")
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted = cipher.encrypt(data)
        length = len(encrypted)
        prelude = bytearray([0x10, 0, 0, 0, length])
        return prelude + encrypted

    def decrypt_packet(self, data):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypt = cipher.decrypt(data)
        padding = decrypt[-1]
        decrypt = decrypt[:-padding]
        return decrypt.decode("utf-8")

    def send_packet(self, data):
        packet = self.encrypt_packet(json.dumps(data))
        try:
            self.socket.send(packet)
        except Exception:
            self.connect()
            self.socket.send(packet)

    def listen(self):
        while True:
            try:
                header = self.socket.recv(1)
                if not header:
                    self.connect()
                    continue
                if header[0] == 0x10:
                    length_bytes = self.socket.recv(4)
                    length = struct.unpack(">I", length_bytes)[0]
                    payload = self.socket.recv(length)
                    if len(payload) % 16 != 0:
                        continue
                    response = self.decrypt_packet(payload)
                    self.handle_response(response)
            except Exception:
                self.connect()

    def handle_response(self, response):
        try:
            data = json.loads(response)
            if "msg" in data and data["msg"] == "SPK_LIST_VIEW_INFO":
                self.volume = data["data"].get("i_vol")
                self.mute = data["data"].get("b_mute")
        except:
            pass

    def get_volume(self):
        self.send_packet({"cmd": "get", "msg": "SPK_LIST_VIEW_INFO"})
        return self.volume

    def set_volume(self, vol):
        self.send_packet({"cmd": "set", "data": {"i_vol": vol}, "msg": "SPK_LIST_VIEW_INFO"})

    def get_mute(self):
        self.send_packet({"cmd": "get", "msg": "SPK_LIST_VIEW_INFO"})
        return self.mute

    def set_mute(self, enable):
        self.send_packet({"cmd": "set", "data": {"b_mute": enable}, "msg": "SPK_LIST_VIEW_INFO"})

# --- Initialize client ---
soundbar = SoundbarClient(SOUNDBAR_IP, SOUNDBAR_PORT)

# --- Flask routes ---
@app.route("/volume", methods=["GET"])
def get_volume():
    return jsonify({"volume": soundbar.get_volume()})

@app.route("/volume", methods=["POST"])
def set_volume():
    vol = request.json.get("volume")
    if vol is not None and 0 <= vol <= 100:
        soundbar.set_volume(vol)
        return jsonify({"volume": vol})
    return jsonify({"error": "Invalid volume"}), 400

@app.route("/mute", methods=["GET"])
def get_mute():
    return jsonify({"mute": soundbar.get_mute()})

@app.route("/mute", methods=["POST"])
def set_mute():
    enable = request.json.get("mute")
    if isinstance(enable, bool):
        soundbar.set_mute(enable)
        return jsonify({"mute": enable})
    return jsonify({"error": "Invalid mute value"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=HTTP_PORT)

