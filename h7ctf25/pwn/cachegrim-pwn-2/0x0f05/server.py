#!/usr/bin/env python3
"""
TCP Server wrapper for 0x0f05 shellcode challenge
Allows nc-based remote access
"""
import socket
import subprocess
import threading
import sys

HOST = '0.0.0.0'
PORT = 9999

def handle_client(client_socket, addr):
    """Handle individual client connection"""
    print(f"[+] Connection from {addr[0]}:{addr[1]}")
    
    try:
        # Start chal.py as subprocess
        proc = subprocess.Popen(
            [sys.executable, '/app/chal.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0
        )
        
        def forward_output():
            """Forward subprocess output to client"""
            try:
                while True:
                    data = proc.stdout.read(1)
                    if not data:
                        break
                    client_socket.sendall(data)
            except:
                pass
        
        # Start output forwarding thread
        output_thread = threading.Thread(target=forward_output, daemon=True)
        output_thread.start()
        
        # Forward client input to subprocess
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            proc.stdin.write(data)
            proc.stdin.flush()
        
    except Exception as e:
        print(f"[-] Error handling client {addr}: {e}")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=1)
        except:
            try:
                proc.kill()
            except:
                pass
        client_socket.close()
        print(f"[-] Connection closed from {addr[0]}:{addr[1]}")

def main():
    """Start TCP server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    
    print(f"[*] TCP Server listening on {HOST}:{PORT}")
    
    try:
        while True:
            client_sock, client_addr = server.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(client_sock, client_addr),
                daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print("\n[!] Server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    main()
