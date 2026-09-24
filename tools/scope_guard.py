"""
Target Scope Enforcer & Safe Socket Connection Wrapper.
Guarantees that automated CTF scripts and agents only connect to explicitly authorized targets.
"""

import os
import socket
import yaml
from typing import Union, List

SCOPE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scope.yaml")


class ScopeViolationError(PermissionError):
    """Raised when an attempt is made to communicate with an unauthorized target."""
    pass


def load_scope(scope_path=SCOPE_FILE):
    if not os.path.exists(scope_path):
        return {"allowed_targets": [{"host": "127.0.0.1", "ports": ["1000-65535"]}]}
    try:
        with open(scope_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise RuntimeError(f"Failed to parse scope definition: {e}")


def _port_in_spec(port: int, port_spec: Union[int, str, List]) -> bool:
    if port_spec == "*":
        return True
    if isinstance(port_spec, int):
        return port == port_spec
    if isinstance(port_spec, str):
        if "-" in port_spec:
            parts = port_spec.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return int(parts[0]) <= port <= int(parts[1])
        elif port_spec.isdigit():
            return port == int(port_spec)
    elif isinstance(port_spec, list):
        for item in port_spec:
            if _port_in_spec(port, item):
                return True
    return False


def is_target_allowed(host: str, port: int, scope: dict = None) -> bool:
    if scope is None:
        scope = load_scope()

    host = host.strip().lower()
    
    # Check allowed_targets
    targets = scope.get("allowed_targets", [])
    for entry in targets:
        allowed_host = str(entry.get("host", "")).strip().lower()
        if allowed_host in (host, "*"):
            allowed_ports = entry.get("ports", "*")
            if _port_in_spec(port, allowed_ports):
                return True

    # Check challenge-specific entries
    challenges = scope.get("challenges", {})
    for chal_name, chal_data in challenges.items():
        if isinstance(chal_data, dict):
            c_host = str(chal_data.get("host", "")).strip().lower()
            c_port = chal_data.get("port")
            if c_host == host and _port_in_spec(port, c_port):
                return True
    return False


def validate_target(host: str, port: int):
    """Verify target authorization; raise ScopeViolationError if denied."""
    if not is_target_allowed(host, port):
        raise ScopeViolationError(
            f"[!] Out-of-Scope target access blocked: {host}:{port}. "
            f"Add this endpoint to scope.yaml if authorized."
        )


def safe_connect(host: str, port: int, timeout: float = 10.0) -> socket.socket:
    """Safe socket creator enforcing target scope allowlist."""
    validate_target(host, port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    return s
