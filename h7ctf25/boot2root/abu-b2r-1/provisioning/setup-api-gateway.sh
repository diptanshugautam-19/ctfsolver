#!/bin/bash
set -e

echo "[+] Setting up H7Corp API Gateway..."

# Install dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv

# Create API Gateway directory
mkdir -p /opt/api-gateway
cd /opt/api-gateway

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Flask and requests
pip install flask requests

# Create API Gateway application
cat > /opt/api-gateway/gateway.py << 'GATEWAY_EOF'
from flask import Flask, request, jsonify, render_template_string
import requests
import json
from urllib.parse import urlparse

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>H7Corp API Gateway</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            border: 2px solid #00ff00;
            padding: 20px;
            margin-bottom: 20px;
            background: #0a0a0a;
        }
        .header h1 {
            margin: 0;
            color: #00ff00;
            font-size: 28px;
        }
        .header .subtitle {
            color: #888;
            font-size: 14px;
            margin-top: 5px;
        }
        .card {
            background: #0a0a0a;
            border: 1px solid #333;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .card h2 {
            color: #00ff00;
            margin-top: 0;
            font-size: 20px;
        }
        pre {
            background: #000;
            border: 1px solid #333;
            padding: 15px;
            overflow-x: auto;
            color: #0f0;
        }
        code {
            color: #0ff;
        }
        .warning {
            background: #2a1a00;
            border: 1px solid #ff6600;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        .info {
            background: #001a2a;
            border: 1px solid #0066ff;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>H7Corp API Gateway</h1>
        <div class="subtitle">Internal Service Router | Version 1.0.3</div>
    </div>
    
    <div class="card">
        <h2>About This Service</h2>
        <p>The H7Corp API Gateway provides internal routing between microservices. This service is for internal use only and should not be exposed to external networks.</p>
        
        <div class="info">
            <strong>Service Information</strong><br>
            Status: <span style="color: #0f0;">ONLINE</span><br>
            Port: 8090<br>
            Access: Internal Only<br>
            Last Updated: 2025-10-14
        </div>
    </div>
    
    <div class="card">
        <h2>Available Endpoints</h2>
        
        <h3 style="color: #0ff; font-size: 16px;">GET /</h3>
        <p>Main gateway page (this page)</p>
        
        <h3 style="color: #0ff; font-size: 16px; margin-top: 20px;">GET /docs</h3>
        <p>Complete API documentation</p>
        
        <h3 style="color: #0ff; font-size: 16px; margin-top: 20px;">GET /routes</h3>
        <p>List available service routes</p>
        
        <h3 style="color: #0ff; font-size: 16px; margin-top: 20px;">GET /proxy</h3>
        <p>Proxy requests to internal services</p>
        <pre>Parameters:
  service - Service name (string)
  path    - Endpoint path (string)
  
Example:
  /proxy?service=metrics&path=api/health</pre>
        
        <h3 style="color: #0ff; font-size: 16px; margin-top: 20px;">GET /request</h3>
        <p>Forward HTTP requests to internal services with configurable methods</p>
        <pre>Parameters:
  url    - Target URL (string)
  method - HTTP method (GET|POST|PUT|DELETE, default: GET)
  data   - Request body (JSON string, optional)
  
Example:
  /request?url=http://localhost:9090/metrics&method=GET</pre>
        
        <div class="warning">
            <strong>Security Notice:</strong> The request forwarder is for internal service integration testing. Certain operations are restricted by security policy.
        </div>
    </div>
    
    <div class="card">
        <h2>Usage Examples</h2>
        
        <h3 style="color: #0ff; font-size: 16px;">List Available Routes</h3>
        <pre>curl http://localhost:8090/routes</pre>
        
        <h3 style="color: #0ff; font-size: 16px; margin-top: 20px;">Proxy to Internal Service</h3>
        <pre>curl "http://localhost:8090/proxy?service=metrics&path=status"</pre>
        
        <h3 style="color: #0ff; font-size: 16px; margin-top: 20px;">Forward Request (POST)</h3>
        <pre>curl "http://localhost:8090/request?url=http://localhost:9090/api/status&method=POST&data={}"</pre>
    </div>
</body>
</html>
'''

DOCS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>API Gateway - Documentation</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #00ff00;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 { color: #0f0; }
        h2 { color: #0ff; margin-top: 30px; }
        h3 { color: #ff0; margin-top: 20px; }
        pre {
            background: #000;
            border: 1px solid #333;
            padding: 15px;
            overflow-x: auto;
            color: #0f0;
        }
        .card {
            background: #0a0a0a;
            border: 1px solid #333;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <h1>H7Corp API Gateway - Complete Documentation</h1>
    
    <div class="card">
        <h2>Service Architecture</h2>
        <p>The API Gateway routes requests between internal microservices:</p>
        <pre>
Client → API Gateway (8090) → Internal Services
                               ├─ Metrics (9090)
                               ├─ Cache (6379)
                               └─ Docker (2375) [Hidden]</pre>
    </div>
    
    <div class="card">
        <h2>Endpoint: /proxy</h2>
        <h3>Description</h3>
        <p>Routes GET requests to internal services</p>
        
        <h3>Parameters</h3>
        <pre>service (required) - Target service name
path (optional)    - Endpoint path within service</pre>
        
        <h3>Example</h3>
        <pre>GET /proxy?service=metrics&path=api/stats
Response: JSON data from metrics service</pre>
    </div>
    
    <div class="card">
        <h2>Endpoint: /request</h2>
        <h3>Description</h3>
        <p>Forward HTTP requests to internal services with support for multiple HTTP methods. Used for automated testing and service integration validation.</p>
        
        <h3>Parameters</h3>
        <pre>url (required)     - Target service URL
method (optional)  - HTTP method (GET, POST, PUT, DELETE, default: GET)
data (optional)    - Request payload for POST/PUT operations</pre>
        
        <h3>Security Policy</h3>
        <p>Certain infrastructure modification operations are restricted by policy.</p>
        
        <h3>Example</h3>
        <pre>GET /request?url=http://localhost:9090/status&method=GET
Response: Service status information</pre>
    </div>
    
    <div class="card">
        <h2>Available Services</h2>
        <p>Use /routes to discover available service mappings</p>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/docs')
def docs():
    return render_template_string(DOCS_TEMPLATE)

@app.route('/routes')
def routes():
    """List available service routes"""
    services = {
        "app": {
            "host": "localhost:8080",
            "description": "Main web application"
        },
        "metrics": {
            "host": "localhost:9090",
            "description": "Prometheus metrics (not running)"
        },
        "cache": {
            "host": "localhost:6379",
            "description": "Redis cache (not running)"
        }
        # Docker service intentionally hidden - must be discovered via fuzzing!
    }
    
    return jsonify({
        "status": "success",
        "available_services": services,
        "note": "Some services may not be running. Use /proxy to test connectivity."
    })

@app.route('/proxy')
def proxy():
    """Proxy GET requests to internal services"""
    service = request.args.get('service', '')
    path = request.args.get('path', '')
    
    if not service:
        return jsonify({"error": "Missing 'service' parameter"}), 400
    
    # Service mapping (including hidden docker service)
    services = {
        'app': 'localhost:8080',
        'metrics': 'localhost:9090',
        'cache': 'localhost:6379',
        'docker': 'localhost:2375'  # Hidden! Not in /routes
    }
    
    if service not in services:
        return jsonify({"error": f"Unknown service: {service}"}), 404
    
    # Build target URL
    target_url = f"http://{services[service]}/{path}"
    
    try:
        response = requests.get(target_url, timeout=5)
        
        # Try to return JSON if possible
        try:
            return jsonify(response.json())
        except:
            return response.text, response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Service '{service}' is not reachable"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/request')
def forward_request():
    """Forward HTTP requests to internal services"""
    url = request.args.get('url', '')
    method = request.args.get('method', 'GET').upper()
    data = request.args.get('data', '')
    
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400
    
    if method not in ['GET', 'POST', 'PUT', 'DELETE']:
        return jsonify({"error": "Invalid method. Supported: GET, POST, PUT, DELETE"}), 400
    
    # Security policy - block infrastructure modification operations
    blocked_operations = ['/containers/create?', '/build?', 'Privileged', '--privileged']
    
    # Validate request against security policy
    check_string = url + data
    for blocked in blocked_operations:
        if blocked in check_string:
            return jsonify({
                "error": "Operation not permitted",
                "reason": "Request denied by security policy"
            }), 403
    
    try:
        headers = {'Content-Type': 'application/json'} if data else {}
        
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, data=data, headers=headers, timeout=5)
        elif method == 'PUT':
            response = requests.put(url, data=data, headers=headers, timeout=5)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=5)
        
        # Try to return JSON
        try:
            return jsonify(response.json())
        except:
            return response.text, response.status_code
            
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connection failed"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "api-gateway", "version": "1.0.3"})

@app.route('/status')
def status():
    return jsonify({"uptime": "operational", "services": ["proxy", "request"]})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8090, debug=False)
GATEWAY_EOF

# Create systemd service
cat > /etc/systemd/system/api-gateway.service << 'SERVICE_EOF'
[Unit]
Description=H7Corp API Gateway
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/api-gateway
Environment="PATH=/opt/api-gateway/venv/bin"
ExecStart=/opt/api-gateway/venv/bin/python /opt/api-gateway/gateway.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Enable and start service
systemctl daemon-reload
systemctl enable api-gateway.service
systemctl start api-gateway.service

echo "[+] API Gateway installed and running on port 8090"
echo "[+] Access: http://localhost:8090"
