#!/usr/bin/env python3
"""
TCP Server wrapper for the BackDoor challenge
Users connect via: nc <host> <port>
"""

import socket
import os
import sys
import threading
import select

HOST = '0.0.0.0'
PORT = 3000

# Import the challenge directly
sys.path.insert(0, '/app')
from answer import QUESTIONS, ask_question, CORRECT

def handle_client(conn, addr):
    """Run the quiz for the connected client"""
    print(f"[+] Connection from {addr}", flush=True)
    
    def send(msg):
        """Helper to send messages to client"""
        try:
            conn.sendall(msg.encode('utf-8') if isinstance(msg, str) else msg)
        except:
            pass
    
    def recv_line():
        """Helper to receive a line from client"""
        try:
            data = b""
            while True:
                chunk = conn.recv(1)
                if not chunk:
                    return None
                if chunk == b'\n':
                    return data.decode('utf-8').strip()
                data += chunk
        except:
            return None
    
    try:
        send("=" * 50 + "\n")
        send("  BackDoor Forensics Challenge\n")
        send("=" * 50 + "\n")
        send("Answer each question correctly to proceed.\n")
        send(f"You have 3 attempts per question.\n\n")
        
        # Run through each question
        for q in QUESTIONS:
            qid = q["id"]
            correct = CORRECT[qid]
            normalize = q["normalize"]
            attempts = 0
            
            while attempts < 3:
                attempts += 1
                send("\n" + q["text"] + "\n")
                if q.get("hint"):
                    send("Hint: " + q["hint"] + "\n")
                send("> ")
                
                user_input = recv_line()
                if user_input is None:
                    return
                
                usr_norm = normalize(user_input)
                
                # Validation for question 6 (hex)
                if qid == "6":
                    import re
                    SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
                    if not SHA256_RE.fullmatch(user_input.strip()):
                        send("Invalid format: value must be 64 hex characters.\n")
                        if attempts < 3:
                            send(f"Attempts left: {3 - attempts}\n")
                        continue
                    if usr_norm == correct.lower():
                        send("Correct.\n")
                        break
                    else:
                        send("Incorrect hex value.\n")
                elif qid == "1":
                    # Domain: case-insensitive
                    if usr_norm == correct.lower():
                        send("Correct.\n")
                        break
                    else:
                        send("Incorrect domain.\n")
                else:
                    # Exact match for others
                    if usr_norm == correct:
                        send("Correct.\n")
                        break
                    else:
                        send("Incorrect.\n")
                
                if attempts < 3:
                    send(f"Try again ({3 - attempts} attempts left).\n")
                else:
                    send("No attempts left for this question. Exiting.\n")
                    send("\nQuiz failed. Goodbye.\n")
                    return
        
        # All correct - send flag
        send("\n" + "=" * 50 + "\n")
        send("All questions correct. Congratulations!\n")
        send("=" * 50 + "\n")
        flag = os.environ.get("FLAG", "H7CTF{test_flag}")
        send(f"\nFlag: {flag}\n")
        
    except Exception as e:
        print(f"[-] Error: {e}", flush=True)
    finally:
        conn.close()
        print(f"[-] Connection closed from {addr}", flush=True)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    
    print(f"[*] TCP Server listening on {HOST}:{PORT}", flush=True)
    print(f"[*] Connect with: nc <host> {PORT}", flush=True)
    
    while True:
        try:
            conn, addr = server.accept()
            # Handle each client in a separate thread
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
        except KeyboardInterrupt:
            print("\n[!] Shutting down...", flush=True)
            break
        except Exception as e:
            print(f"[-] Server error: {e}", flush=True)
    
    server.close()

if __name__ == "__main__":
    main()
