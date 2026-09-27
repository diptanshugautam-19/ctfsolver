#!/bin/bash
# Quick build and test script for both PWN challenges

echo "================================================"
echo "  H7CTF PWN Challenges - Build & Test"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Challenge 1: seccomp-jail
echo -e "${YELLOW}[*] Building Challenge 1: seccomp-jail${NC}"
cd cachegrim-pwn-1/seccomp-jail/
docker build -t seccomp-jail . || { echo -e "${RED}[!] Build failed${NC}"; exit 1; }
echo -e "${GREEN}[✓] Build successful${NC}"

echo -e "${YELLOW}[*] Starting seccomp-jail on port 1337...${NC}"
docker stop seccomp-jail-challenge 2>/dev/null
docker rm seccomp-jail-challenge 2>/dev/null
docker run -d -p 1337:1337 --name seccomp-jail-challenge seccomp-jail
sleep 2

echo -e "${YELLOW}[*] Testing connection...${NC}"
timeout 2 nc localhost 1337 </dev/null && echo -e "${GREEN}[✓] Challenge 1 is responsive${NC}" || echo -e "${RED}[!] No response${NC}"

echo -e "${YELLOW}[*] Checking flag format...${NC}"
FLAG1=$(docker exec seccomp-jail-challenge cat /flag 2>/dev/null)
if [[ $FLAG1 =~ H7CTF\{pr1s0n_bre4k_r0p_3dition_[a-f0-9-]{36}\} ]]; then
    echo -e "${GREEN}[✓] Flag format correct: $FLAG1${NC}"
else
    echo -e "${RED}[!] Flag format incorrect: $FLAG1${NC}"
fi

echo ""
echo "================================================"
echo ""

# Challenge 2: 0x0f05
cd ../../cachegrim-pwn-2/0x0f05/
echo -e "${YELLOW}[*] Building Challenge 2: 0x0f05${NC}"
docker build -t shellcode-0x0f05 . || { echo -e "${RED}[!] Build failed${NC}"; exit 1; }
echo -e "${GREEN}[✓] Build successful${NC}"

echo -e "${YELLOW}[*] Starting 0x0f05 on port 9999...${NC}"
docker stop shellcode-challenge 2>/dev/null
docker rm shellcode-challenge 2>/dev/null
docker run -d -p 9999:9999 --name shellcode-challenge shellcode-0x0f05
sleep 2

echo -e "${YELLOW}[*] Testing connection...${NC}"
timeout 2 nc localhost 9999 </dev/null && echo -e "${GREEN}[✓] Challenge 2 is responsive${NC}" || echo -e "${RED}[!] No response${NC}"

echo -e "${YELLOW}[*] Checking flag format...${NC}"
FLAG2=$(docker exec shellcode-challenge cat /flag.txt 2>/dev/null)
if [[ $FLAG2 =~ H7CTF\{sh3llc0d3_a1nt_g0nn4_m4k3_y0u_r1ch_[a-f0-9-]{36}\} ]]; then
    echo -e "${GREEN}[✓] Flag format correct: $FLAG2${NC}"
else
    echo -e "${RED}[!] Flag format incorrect: $FLAG2${NC}"
fi

echo ""
echo "================================================"
echo "  Summary"
echo "================================================"
echo ""
echo "Challenge 1 (seccomp-jail):"
echo "  - Port: 1337"
echo "  - Connect: nc localhost 1337"
echo "  - Flag: $FLAG1"
echo ""
echo "Challenge 2 (0x0f05):"
echo "  - Port: 9999"
echo "  - Connect: nc localhost 9999"
echo "  - Flag: $FLAG2"
echo ""
echo -e "${GREEN}[✓] Both challenges are running!${NC}"
echo ""
echo "To stop:"
echo "  docker stop seccomp-jail-challenge shellcode-challenge"
echo "  docker rm seccomp-jail-challenge shellcode-challenge"
