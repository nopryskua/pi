import os, socket, struct, json, time
from Crypto.Cipher import AES
from threading import Thread

IP = os.environ.get("SOUNDBAR_IP", "192.168.1.113")
PORT = int(os.environ.get("SOUNDBAR_PORT", 9741))

IV = b'\'%^Ur7gy$~t+f)%@'
KEY = b'T^&*J%^7tr~4^%^&I(o%^!jIJ__+a0 k'

def decrypt(data):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    decrypted = cipher.decrypt(data)
    pad = decrypted[-1]
    return decrypted[:-pad].decode()

def encrypt(data):
    data = json.dumps(data).encode()
    padlen = 16 - (len(data) % 16)
    data += bytes([padlen]*padlen)
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    encrypted = cipher.encrypt(data)
    length = len(encrypted)
    return bytes([0x10, 0, 0, 0]) + struct.pack(">I", length) + encrypted

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((IP, PORT))

def listener():
    while True:
        hdr = sock.recv(1)
        if len(hdr)==0: continue
        if hdr[0]==0x10:
            length = struct.unpack(">I", sock.recv(4))[0]
            data = sock.recv(length)
            try:
                print(json.dumps(json.loads(decrypt(data)), indent=2))
            except: pass

Thread(target=listener, daemon=True).start()

# Query periodically
while True:
    sock.send(encrypt({"cmd":"get","msg":"SPK_LIST_VIEW_INFO"}))  # volume/power/mute
    time.sleep(2)

