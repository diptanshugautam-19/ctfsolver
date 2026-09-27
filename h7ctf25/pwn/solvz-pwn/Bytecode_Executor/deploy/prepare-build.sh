#!/bin/bash

set -e

echo "[*] Preparing build context..."

cp ../src/*.c .
cp ../src/*.h .
cp ../src/*.asm .
cp ../src/Makefile .

echo "[+] Build context ready"
