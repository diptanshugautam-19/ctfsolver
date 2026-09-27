#!/bin/bash

gcc -o imperial_archive imperial_archive_src.c -fno-stack-protector -no-pie -m32 -g
