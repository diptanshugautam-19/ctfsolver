#!/bin/bash
set -e

echo "[*] Deploying H7Corp DevOps Portal - Infrastructure Service Monitor..."

# Stop existing service if running
systemctl stop h7corp-portal 2>/dev/null || true
sleep 2
# Kill any remaining Flask processes on port 8080
pkill -9 -f "python3 /opt/webapp/app.py" 2>/dev/null || true
pkill -9 -f "python3.*app.py" 2>/dev/null || true
fuser -k -9 8080/tcp 2>/dev/null || true
sleep 2
# Final verification and force kill if needed
if lsof -i :8080 >/dev/null 2>&1; then
    echo "[!] Port 8080 still in use, force terminating..."
    lsof -ti :8080 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

pip3 install -q flask requests

mkdir -p /opt/webapp/templates /opt/webapp/static
cd /opt/webapp

# Main application with sophisticated SSRF protection
cat > /opt/webapp/app.py << 'EOF'
from flask import Flask, request, render_template_string, jsonify, session
import requests
import json
import re
import ipaddress
from datetime import datetime
from urllib.parse import urlparse
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Simulated service registry data
SERVICES_REGISTRY = {
    "api-gateway": {"url": "http://10.0.10.5:8000", "status": "healthy", "uptime": "99.9%"},
    "auth-service": {"url": "http://10.0.10.12:3000", "status": "healthy", "uptime": "99.7%"},
    "user-service": {"url": "http://10.0.10.15:5000", "status": "healthy", "uptime": "99.6%"},
    "database-primary": {"url": "http://10.0.10.20:5432", "status": "healthy", "uptime": "99.99%"},
    "cache-redis": {"url": "http://10.0.10.25:6379", "status": "healthy", "uptime": "99.8%"},
    "message-queue": {"url": "http://10.0.10.40:5672", "status": "healthy", "uptime": "99.6%"},
    "analytics-engine": {"url": "http://10.0.10.50:9200", "status": "healthy", "uptime": "99.5%"},
}

NETWORK_TOPOLOGY = """
H7Corp Infrastructure Network Map
==================================

DMZ Zone (10.0.1.0/24):
  - Load Balancers: 10.0.1.10-15
  - Web Frontends: 10.0.1.20-30
  - CDN Origins: 10.0.1.40-45

Internal Services (10.0.10.0/24):
  - API Gateway: 10.0.10.5:8000
  - Auth Service: 10.0.10.12:3000
  - User Service: 10.0.10.15:5000
  - Database: 10.0.10.20:5432
  - Cache Layer: 10.0.10.25:6379
  - Message Queue: 10.0.10.40:5672
  - Analytics: 10.0.10.50:9200

Management Network (127.0.0.0/8):
  - Localhost services for monitoring tools
  - Internal health check endpoints
"""

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>H7Corp DevOps Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #000;
            color: #888;
            min-height: 100vh;
        }
        .navbar {
            background: #000;
            border-bottom: 1px solid #1a1a1a;
            padding: 0;
        }
        .navbar-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
            height: 50px;
        }
        .logo-section {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .logo {
            font-size: 16px;
            font-weight: 700;
            color: #00ff00;
        }
        .logo-sub {
            color: #444;
            font-size: 10px;
            padding: 2px 6px;
            border: 1px solid #222;
        }
        .nav-links {
            display: flex;
            gap: 25px;
        }
        .nav-links a {
            color: #555;
            text-decoration: none;
            font-size: 11px;
            transition: color 0.2s;
        }
        .nav-links a:hover, .nav-links a.active {
            color: #00ff00;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        .page-header {
            margin-bottom: 25px;
            padding-bottom: 12px;
            border-bottom: 1px solid #1a1a1a;
        }
        .page-header h1 {
            font-size: 20px;
            font-weight: 400;
            color: #fff;
            margin-bottom: 6px;
        }
        .page-header p {
            font-size: 11px;
            color: #555;
        }
        .badge {
            display: inline-block;
            padding: 2px 6px;
            background: #111;
            border: 1px solid #222;
            color: #00ff00;
            font-size: 9px;
            text-transform: uppercase;
            margin-left: 8px;
        }
        .badge.warning {
            border-color: #332200;
            color: #ffa500;
        }
        .card {
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 20px;
            margin-bottom: 15px;
        }
        .card h2 {
            font-size: 14px;
            font-weight: 400;
            color: #aaa;
            margin-bottom: 4px;
        }
        .card .subtitle {
            color: #555;
            font-size: 10px;
            margin-bottom: 15px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 18px;
        }
        .stat-card h3 {
            font-size: 10px;
            color: #555;
            font-weight: 400;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        .stat-card .value {
            font-size: 24px;
            color: #00ff00;
            font-weight: 400;
            margin-bottom: 4px;
        }
        .stat-card .label {
            font-size: 10px;
            color: #555;
        }
        .form-group {
            margin-bottom: 18px;
        }
        label {
            display: block;
            margin-bottom: 6px;
            color: #888;
            font-size: 10px;
            text-transform: uppercase;
        }
        input[type="text"], select {
            width: 100%;
            padding: 10px;
            border: 1px solid #222;
            background: #0a0a0a;
            color: #aaa;
            font-size: 12px;
            font-family: 'Courier New', monospace;
        }
        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #00ff00;
        }
        button {
            background: #00ff00;
            color: #000;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            font-family: 'Courier New', monospace;
        }
        button:hover {
            background: #00cc00;
        }
        .result {
            margin-top: 18px;
            padding: 12px;
            background: #000;
            border: 1px solid #1a1a1a;
            border-left: 2px solid #00ff00;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            color: #00ff00;
            font-size: 11px;
            line-height: 1.5;
            overflow-x: auto;
            max-height: 350px;
            overflow-y: auto;
        }
        .result.error {
            border-left-color: #ff0000;
            color: #ff4444;
        }
        .info-box {
            background: #0a0a0a;
            border: 1px solid #1a3a1a;
            border-left: 2px solid #00ff00;
            padding: 12px;
            margin: 18px 0;
            color: #888;
            font-size: 11px;
        }
        .warning-box {
            background: #0a0a0a;
            border: 1px solid #3a2a1a;
            border-left: 2px solid #ffa500;
            padding: 12px;
            margin: 18px 0;
            color: #888;
            font-size: 11px;
        }
        .service-table {
            width: 100%;
            border-collapse: collapse;
            margin: 18px 0;
        }
        .service-table th {
            background: #0a0a0a;
            color: #666;
            padding: 10px;
            text-align: left;
            font-size: 10px;
            font-weight: 400;
            text-transform: uppercase;
            border-bottom: 1px solid #1a1a1a;
        }
        .service-table td {
            padding: 10px;
            border-bottom: 1px solid #111;
            color: #888;
            font-size: 11px;
        }
        .service-table tr:hover {
            background: #0a0a0a;
        }
        .status-dot {
            display: inline-block;
            width: 5px;
            height: 5px;
            border-radius: 50%;
            margin-right: 6px;
        }
        .status-dot.healthy { background: #00ff00; }
        .status-dot.degraded { background: #ffa500; }
        .status-dot.down { background: #ff4444; }
        .footer {
            text-align: center;
            padding: 50px 0 30px;
            color: #555;
            font-size: 13px;
            border-top: 1px solid #1a1a1a;
            margin-top: 80px;
        }
        .security-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            background: rgba(0, 255, 0, 0.05);
            border: 1px solid rgba(0, 255, 0, 0.2);
            border-radius: 4px;
            color: #00ff00;
            font-size: 11px;
            font-weight: 600;
            margin-left: 15px;
        }
        pre {
            background: #000;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            color: #00ff00;
            font-size: 12px;
            line-height: 1.6;
            border: 1px solid #2a2a2a;
        }
        code {
            font-family: 'Courier New', monospace;
            color: #00ff00;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="logo-section">
                <div class="logo">H7Corp</div>
                <div class="logo-sub">DevOps Portal</div>
            </div>
            <div class="nav-links">
                <a href="/" class="{{ 'active' if page == 'dashboard' else '' }}">Dashboard</a>
                <a href="/services" class="{{ 'active' if page == 'services' else '' }}">Services</a>
                <a href="/validator" class="{{ 'active' if page == 'validator' else '' }}">Endpoint Validator</a>
                <a href="/docs" class="{{ 'active' if page == 'docs' else '' }}">Documentation</a>
            </div>
        </div>
    </nav>
    
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    
    <div class="footer">
        H7CORP ENTERPRISE &copy; 2025
    </div>
</body>
</html>
'''

DASHBOARD_CONTENT = '''<div class="page-header">
        <h1>Infrastructure Overview<span class="badge">Live</span></h1>
        <p>Real-time monitoring and health status of all production services</p>
    </div>

    <div class="grid">
        <div class="stat-card">
            <h3>Total Services</h3>
            <div class="value">{{ services_count }}</div>
            <div class="label">Monitored endpoints</div>
        </div>
        <div class="stat-card">
            <h3>System Health</h3>
            <div class="value">99.8%</div>
            <div class="label">Last 30 days uptime</div>
        </div>
        <div class="stat-card">
            <h3>Active Alerts</h3>
            <div class="value">0</div>
            <div class="label">No critical issues</div>
        </div>
        <div class="stat-card">
            <h3>Last Updated</h3>
            <div class="value">{{ current_time }}</div>
            <div class="label">System time</div>
        </div>
    </div>

    <div class="card">
        <h2>Quick Actions</h2>
        <div class="subtitle">Common operations for infrastructure management</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px;">
            <a href="/services" style="display: block; padding: 20px; background: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 6px; text-decoration: none; color: #00ff00; text-align: center; transition: all 0.2s;">
                <div style="font-size: 14px; font-weight: 600;">View Services</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">Service registry</div>
            </a>
            <a href="/validator" style="display: block; padding: 20px; background: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 6px; text-decoration: none; color: #00ff00; text-align: center; transition: all 0.2s;">
                <div style="font-size: 14px; font-weight: 600;">Endpoint Validator</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">Test endpoints</div>
            </a>
            <a href="/docs" style="display: block; padding: 20px; background: #0a0a0a; border: 1px solid #2a2a2a; border-radius: 6px; text-decoration: none; color: #00ff00; text-align: center; transition: all 0.2s;">
                <div style="font-size: 14px; font-weight: 600;">Documentation</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">API reference</div>
            </a>
        </div>
    </div>'''

SERVICES_CONTENT = '''<div class="page-header">
        <h1>Service Registry<span class="security-badge">🔒 Protected Network</span></h1>
        <p>Comprehensive list of all registered internal microservices</p>
    </div>

    <div class="card">
        <h2>Registered Services</h2>
        <div class="subtitle">Current production services with health status and network endpoints</div>
        
        <table class="service-table">
            <thead>
                <tr>
                    <th>Service Name</th>
                    <th>Endpoint</th>
                    <th>Status</th>
                    <th>Uptime</th>
                    <th>Type</th>
                </tr>
            </thead>
            <tbody>
                {% for name, data in services.items() %}
                <tr>
                    <td><strong>{{ name }}</strong></td>
                    <td><code>{{ data.url }}</code></td>
                    <td><span class="status-dot healthy"></span>{{ data.status }}</td>
                    <td>{{ data.uptime }}</td>
                    <td>microservice</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="info-box">
            <strong>Note:</strong> Services are deployed across internal network segments (10.0.10.0/24). 
            Use the <a href="/validator" style="color: #0066ff;">Endpoint Validator</a> to test connectivity to new services before adding them to this registry.
        </div>
    </div>'''

VALIDATOR_CONTENT = '''<div class="page-header">
        <h1>Custom Endpoint Validator<span class="badge warning">DevOps Only</span></h1>
        <p>Test and validate service endpoints before adding them to the production registry</p>
    </div>

    <div class="card">
        <h2>Endpoint Health Check</h2>
        <div class="subtitle">
            Validate that internal service endpoints are responding correctly. This tool performs connectivity tests 
            and health checks against localhost services before they're added to the monitoring system.
        </div>

        <div class="warning-box">
            <strong>⚠️ Security Notice:</strong> This validator is restricted to localhost endpoints only for security purposes. 
            External endpoint testing is disabled. Only authorized DevOps personnel should use this tool.
        </div>

        <form method="POST" action="/validator">
            <div class="form-group">
                <label for="url">Service Endpoint URL</label>
                <input type="text" 
                       id="url" 
                       name="url" 
                       placeholder="http://localhost:9000/api/health" 
                       value="{{ url or '' }}"
                       required>
                <div style="font-size: 12px; color: #666; margin-top: 8px;">
                    Examples: <code>http://localhost:8080/status</code>, <code>http://127.0.0.1:3000/health</code>
                </div>
            </div>
            
            <button type="submit">Validate Endpoint</button>
        </form>

        {% if result %}
            <div class="result {{ 'error' if 'Error' in result else '' }}">{{ result }}</div>
        {% endif %}
    </div>

    <div class="card">
        <h2>How It Works</h2>
        <div class="subtitle">Understanding the endpoint validation process</div>
        
        <div style="color: #aaa; font-size: 14px; line-height: 1.8;">
            <p style="margin-bottom: 15px;">
                <strong style="color: #fff;">1. URL Validation:</strong> The system validates that the provided endpoint uses localhost addresses only.
            </p>
            <p style="margin-bottom: 15px;">
                <strong style="color: #fff;">2. Security Checks:</strong> Multiple security layers prevent SSRF attacks:
                <ul style="margin: 10px 0 10px 30px;">
                    <li>Hostname whitelist enforcement</li>
                    <li>IP address format validation</li>
                    <li>Port restriction checks</li>
                    <li>URL encoding bypass prevention</li>
                </ul>
            </p>
            <p style="margin-bottom: 15px;">
                <strong style="color: #fff;">3. Health Check:</strong> Performs HTTP GET request to the endpoint and returns the response.
            </p>
            <p>
                <strong style="color: #fff;">4. Response Analysis:</strong> Validates response format and checks for proper service health indicators.
            </p>
        </div>
    </div>'''

DOCS_CONTENT = '''<div class="page-header">
        <h1>Documentation<span class="badge">API Reference</span></h1>
        <p>Technical documentation for the H7Corp DevOps Portal</p>
    </div>

    <div class="card">
        <h2>Network Architecture</h2>
        <div class="subtitle">Understanding H7Corp's internal infrastructure layout</div>
        
        <pre>{{ network_topology }}</pre>

        <div class="info-box" style="margin-top: 25px;">
            <strong>Infrastructure Overview:</strong> All services run in containerized environments for 
            scalability and isolation. The internal network uses standard microservice architecture patterns 
            with service discovery and load balancing.
        </div>
    </div>

    <div class="card">
        <h2>API Endpoints</h2>
        <div class="subtitle">Available REST API endpoints for service management</div>
        
        <div style="margin: 25px 0;">
            <h3 style="color: #00ff00; font-size: 16px; margin-bottom: 15px;">GET /api/services</h3>
            <p style="color: #aaa; margin-bottom: 10px;">Returns the complete service registry with health status.</p>
            <pre style="margin-top: 10px;">curl http://localhost:8080/api/services</pre>
        </div>

        <div style="margin: 25px 0;">
            <h3 style="color: #00ff00; font-size: 16px; margin-bottom: 15px;">GET /health</h3>
            <p style="color: #aaa; margin-bottom: 10px;">Portal health check endpoint.</p>
            <pre style="margin-top: 10px;">curl http://localhost:8080/health</pre>
        </div>

        <div style="margin: 25px 0;">
            <h3 style="color: #00ff00; font-size: 16px; margin-bottom: 15px;">POST /validator</h3>
            <p style="color: #aaa; margin-bottom: 10px;">Validate custom service endpoints (localhost only).</p>
            <pre style="margin-top: 10px;">curl -X POST -d "url=http://localhost:9000" http://localhost:8080/validator</pre>
        </div>
    </div>

    <div class="card">
        <h2>Security Considerations</h2>
        <div class="subtitle">Understanding the portal's security mechanisms</div>
        
        <div style="color: #aaa; font-size: 14px; line-height: 1.8;">
            <p style="margin-bottom: 15px;">
                The Endpoint Validator implements multiple security layers to prevent unauthorized access:
            </p>
            <ul style="margin: 10px 0 15px 30px;">
                <li style="margin-bottom: 8px;"><strong style="color: #fff;">Hostname Whitelist:</strong> Only allows localhost, 127.0.0.1, and ::1</li>
                <li style="margin-bottom: 8px;"><strong style="color: #fff;">IP Validation:</strong> Blocks decimal IP encoding, octal, and hex formats</li>
                <li style="margin-bottom: 8px;"><strong style="color: #fff;">Port Restrictions:</strong> Prevents access to sensitive internal ports</li>
                <li style="margin-bottom: 8px;"><strong style="color: #fff;">URL Parser:</strong> Validates URL structure before processing</li>
            </ul>
            <p style="margin-top: 15px;">
                These protections are designed to prevent Server-Side Request Forgery (SSRF) attacks while 
                allowing legitimate localhost service validation.
            </p>
        </div>
    </div>'''

def is_valid_hostname(hostname):
    """
    Advanced hostname validation with multiple security checks
    Blocks common SSRF bypasses but has a subtle vulnerability
    """
    if not hostname:
        return False
    
    # Whitelist check - basic validation
    allowed_hosts = ['localhost', '127.0.0.1', '::1']
    
    # Direct match
    if hostname in allowed_hosts:
        return True
    
    # Block obvious bypass attempts
    hostname_lower = hostname.lower()
    
    # Block decimal/octal/hex IP encodings
    if re.match(r'^\d+$', hostname):  # Pure decimal like 2130706433
        return False
    
    if '0x' in hostname_lower:  # Hex encoding
        return False
        
    if hostname.startswith('0') and len(hostname) > 1 and hostname[1].isdigit():  # Octal
        return False
    
    # Block @ redirects
    if '@' in hostname:
        return False
    
    # Block common domain bypasses
    blocked_suffixes = ['.localhost', '.local', 'localdomain']
    if any(hostname_lower.endswith(suffix) for suffix in blocked_suffixes):
        return False
    
    # Block IP addresses in standard notation (with all 4 octets)
    try:
        # Check if it's a full IP address (e.g., 127.0.0.1)
        if hostname.count('.') == 3:  # Standard IPv4 format
            ipaddress.ip_address(hostname)
            # If we get here, it's a valid IP - only allow whitelisted ones
            return hostname in allowed_hosts
    except ValueError:
        pass
    
    # VULNERABILITY: Shortened IP notation is not validated
    # 127.1 resolves to 127.0.0.1, which is equivalent to localhost
    # But our check only looks for full 4-octet IPs (x.x.x.x)
    # Shortened notation like 127.1 or 127.0.1 bypasses this check
    # This is valid IPv4 shorthand documented in RFC 3986
    # Many developers don't know about this legacy format
    
    return False

def validate_port(port):
    """
    Port validation - blocks dangerous ports
    """
    if not port:
        return True  # Allow if no port specified
    
    try:
        port_num = int(port)
        # Block obviously dangerous ports (but allow 2375 which is our target)
        blocked_ports = [22, 23, 25, 3306, 5432, 6379]  # SSH, Telnet, SMTP, MySQL, PostgreSQL, Redis
        if port_num in blocked_ports:
            return False
        return 1 <= port_num <= 65535
    except ValueError:
        return False

@app.route('/')
def dashboard():
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', DASHBOARD_CONTENT),
        page='dashboard',
        services_count=len(SERVICES_REGISTRY),
        current_time=datetime.now().strftime('%H:%M:%S'),
        datetime=datetime
    )

@app.route('/services')
def services():
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', SERVICES_CONTENT),
        page='services',
        services=SERVICES_REGISTRY,
        datetime=datetime
    )

@app.route('/validator', methods=['GET', 'POST'])
def validator():
    result = None
    url = None
    
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        
        if not url:
            result = "Error: Endpoint URL is required"
        else:
            try:
                parsed = urlparse(url)
                
                # Validate hostname
                if not is_valid_hostname(parsed.hostname):
                    result = "Error: Invalid endpoint. Only localhost endpoints are permitted for security compliance."
                # Validate port
                elif not validate_port(parsed.port):
                    result = "Error: Invalid or restricted port specified."
                else:
                    # Attempt to fetch the endpoint
                    try:
                        response = requests.get(url, timeout=5, allow_redirects=False)
                        
                        # Try to parse as JSON first
                        try:
                            json_data = response.json()
                            result = json.dumps(json_data, indent=2)
                        except:
                            # Return raw text if not JSON
                            result = response.text[:2000]  # Limit response size
                            
                    except requests.exceptions.ConnectionError:
                        result = "Error: Connection failed. Service may be unreachable or not running."
                    except requests.exceptions.Timeout:
                        result = "Error: Request timeout. Service is not responding within acceptable time."
                    except requests.exceptions.RequestException as e:
                        result = f"Error: Request failed - {str(e)}"
                        
            except Exception as e:
                result = f"Error: Invalid URL format - {str(e)}"
    
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', VALIDATOR_CONTENT),
        page='validator',
        url=url,
        result=result,
        datetime=datetime
    )

@app.route('/docs')
def docs():
    return render_template_string(
        BASE_TEMPLATE.replace('{% block content %}{% endblock %}', DOCS_CONTENT),
        page='docs',
        network_topology=NETWORK_TOPOLOGY,
        datetime=datetime
    )

@app.route('/api/services')
def api_services():
    """API endpoint to list all registered services"""
    return jsonify({
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "services": SERVICES_REGISTRY
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "operational",
        "service": "h7corp-devops-portal",
        "version": "2.8.1",
        "timestamp": datetime.now().isoformat(),
        "uptime": "99.8%"
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
EOF

# Create systemd service
cat > /etc/systemd/system/h7corp-portal.service << 'SVCEOF'
[Unit]
Description=H7Corp DevOps Portal - Infrastructure Service Monitor
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/webapp
ExecStart=/usr/bin/python3 /opt/webapp/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

# Start the service
systemctl daemon-reload
systemctl enable h7corp-portal
systemctl start h7corp-portal

# Wait for service to start
sleep 5

# Check if service is running
if systemctl is-active --quiet h7corp-portal; then
    echo "[✓] H7Corp DevOps Portal deployed successfully!"
    echo "[✓] Portal available at: http://0.0.0.0:8080"
    echo "[✓] Professional enterprise DevOps dashboard active"
else
    echo "[✗] Failed to start H7Corp DevOps Portal"
    echo "[*] Checking logs..."
    journalctl -u h7corp-portal -n 30 --no-pager
fi