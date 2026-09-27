import socket
import threading
import hashlib
import uuid
import random

ROCKYOU_PATH = "rockyou.txt"
PORT = 1337

# Load rockyou words
with open(ROCKYOU_PATH, "r", encoding="latin-1") as f:
    words = [line.strip() for line in f if line.strip()]

def generate_flag():
    unique = uuid.uuid4().hex
    return f"h7ctf{{h@sh3s_ar3_m3@nt_t0_b3_crack3d_{unique}}}"

def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")

    # Pick random word and hash it
    word = random.choice(words)
    hashed = hashlib.sha256(word.encode()).hexdigest()

    conn.sendall(f"SHA256: {hashed}\n".encode())
    conn.sendall(b"Enter plaintext: ")

    try:
        data = conn.recv(1024).decode().strip()
    except:
        conn.close()
        return

    if data == word:
        flag = generate_flag()
        conn.sendall(f"Correct!\nYour flag is: {flag}\n".encode())
    else:
        conn.sendall(b"Wrong plaintext. Try again!\n")

    conn.close()
    print(f"[-] Connection from {addr} closed.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", PORT))
    server.listen(5)
    print(f"[*] Listening on port {PORT}")

    while True:
        conn, addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.daemon = True
        client_thread.start()

if __name__ == "__main__":
    start_server()
