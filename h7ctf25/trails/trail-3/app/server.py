from flask import Flask, request, redirect, make_response, render_template_string
import jwt
import random

app = Flask(__name__)

secrets = ["letmein", "password", "supersecretkey", "qwerty", "123456"]
SECRET_KEY = random.choice(secrets)

users = {}

BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CyberX - Advanced Security Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            margin: 0;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .navbar-brand {
            font-weight: 700;
            font-size: 1.5rem;
            color: white !important;
        }
        
        .btn-glass {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        
        .btn-glass:hover {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }
        
        .card-glass {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.1);
            color: white;
        }
        
        .form-control {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            backdrop-filter: blur(10px);
        }
        
        .form-control:focus {
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 0 0 0.2rem rgba(255, 255, 255, 0.25);
            color: white;
        }
        
        .form-control.is-invalid {
            border-color: #dc3545;
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
        }
        
        .form-check-input {
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .form-check-input:checked {
            background-color: #667eea;
            border-color: #667eea;
        }
        
        .form-control::placeholder {
            color: rgba(255, 255, 255, 0.7);
        }
        
        .form-label {
            color: white;
            font-weight: 500;
        }
        
        .btn-primary {
            background: var(--primary-gradient);
            border: none;
            font-weight: 600;
            padding: 12px 30px;
            border-radius: 50px;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        .btn-success {
            background: var(--success-gradient);
            border: none;
            font-weight: 600;
            padding: 12px 30px;
            border-radius: 50px;
            transition: all 0.3s ease;
        }
        
        .btn-success:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(79, 172, 254, 0.4);
        }
        
        .btn-warning {
            background: var(--secondary-gradient);
            border: none;
            font-weight: 600;
            padding: 12px 30px;
            border-radius: 50px;
            transition: all 0.3s ease;
        }
        
        .btn-warning:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(240, 147, 251, 0.4);
        }
        
        .floating-shapes {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: -1;
        }
        
        .shape {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            animation: float 6s ease-in-out infinite;
        }
        
        .shape:nth-child(1) {
            width: 100px;
            height: 100px;
            top: 20%;
            left: 10%;
            animation-delay: 0s;
        }
        
        .shape:nth-child(2) {
            width: 150px;
            height: 150px;
            top: 60%;
            right: 10%;
            animation-delay: 2s;
        }
        
        .shape:nth-child(3) {
            width: 80px;
            height: 80px;
            bottom: 20%;
            left: 30%;
            animation-delay: 4s;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(180deg); }
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
            height: 100%;
        }
        
        .feature-card:hover {
            transform: translateY(-10px);
            background: rgba(255, 255, 255, 0.1);
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stats-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        
        .stats-number {
            font-size: 2rem;
            font-weight: 700;
            background: var(--success-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .pulse {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="floating-shapes">
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
    </div>
    
    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-shield-alt me-2"></i>CyberX
            </a>
            <div class="navbar-nav ms-auto">
                <a class="btn btn-glass btn-sm me-2" href="/register">
                    <i class="fas fa-user-plus me-1"></i>Register
                </a>
                <a class="btn btn-glass btn-sm" href="/login">
                    <i class="fas fa-sign-in-alt me-1"></i>Login
                </a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-5">
        {{ content|safe }}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.route("/")
def index():
    token = request.cookies.get("token")
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user = payload.get("user")
            role = payload.get("role")
            content = f"""
            <div class="card-glass p-5 mb-4">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h1 class="mb-3 display-6 fw-bold">
                            <i class="fas fa-user-shield me-3 text-warning"></i>
                            Welcome back, {user}!
                        </h1>
                        <p class="lead mb-4">
                            <span class="badge bg-gradient rounded-pill px-3 py-2" style="background: var(--success-gradient);">
                                <i class="fas fa-crown me-1"></i>Role: {role.upper()}
                            </span>
                        </p>
                        <div class="d-flex gap-3">
                            <a class="btn btn-primary pulse" href="/dashboard">
                                <i class="fas fa-tachometer-alt me-2"></i>Access Dashboard
                            </a>
                            <form action="/logout" method="POST" class="d-inline">
                                <button type="submit" class="btn btn-glass">
                                    <i class="fas fa-sign-out-alt me-2"></i>Secure Logout
                                </button>
                            </form>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="stats-card">
                            <i class="fas fa-check-circle text-success fa-3x mb-3"></i>
                            <h5>Session Active</h5>
                            <p class="mb-0 text-white-50">Secure Connection Established</p>
                        </div>
                    </div>
                </div>
            </div>
            """
            return render_template_string(BASE_HTML, content=content)
        except jwt.InvalidTokenError:
            pass

    content = """
    <div class="text-center mb-5">
        <div class="card-glass p-5 mb-5">
            <h1 class="display-4 fw-bold mb-4">
                <i class="fas fa-shield-alt me-3"></i>CyberX
            </h1>
            <p class="lead fs-5 mb-4">Enterprise-Grade Security Platform</p>
            <p class="mb-5 text-white-50">
                Advanced threat detection, real-time monitoring, and comprehensive security solutions 
                for modern businesses. Protect your digital assets with our cutting-edge technology.
            </p>
            <div class="d-flex justify-content-center gap-3 mb-5">
                <a class="btn btn-success px-4 py-2" href="/register">
                    <i class="fas fa-rocket me-2"></i>Get Started Free
                </a>
                <a class="btn btn-primary px-4 py-2" href="/login">
                    <i class="fas fa-sign-in-alt me-2"></i>Sign In
                </a>
            </div>
        </div>
    </div>
    
    <div class="row mb-5">
        <div class="col-md-4 mb-4">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-lock"></i>
                </div>
                <h4 class="mb-3">Advanced Encryption</h4>
                <p class="text-white-50">
                    Military-grade encryption protocols to protect your sensitive data 
                    from unauthorized access and cyber threats.
                </p>
            </div>
        </div>
        <div class="col-md-4 mb-4">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-eye"></i>
                </div>
                <h4 class="mb-3">Real-time Monitoring</h4>
                <p class="text-white-50">
                    24/7 security monitoring with instant threat detection and 
                    automated response systems for maximum protection.
                </p>
            </div>
        </div>
        <div class="col-md-4 mb-4">
            <div class="feature-card">
                <div class="feature-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <h4 class="mb-3">Analytics Dashboard</h4>
                <p class="text-white-50">
                    Comprehensive analytics and reporting tools to track security 
                    metrics and identify potential vulnerabilities.
                </p>
            </div>
        </div>
    </div>
    
    <div class="row mb-5">
        <div class="col-md-3 mb-3">
            <div class="stats-card">
                <div class="stats-number">99.9%</div>
                <p class="mb-0">Uptime</p>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="stats-card">
                <div class="stats-number">10K+</div>
                <p class="mb-0">Protected Assets</p>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="stats-card">
                <div class="stats-number">24/7</div>
                <p class="mb-0">Support</p>
            </div>
        </div>
        <div class="col-md-3 mb-3">
            <div class="stats-card">
                <div class="stats-number">256-bit</div>
                <p class="mb-0">Encryption</p>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/register", methods=["GET", "POST"])
def register():
    error_message = None
    success_message = None
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            error_message = "Please fill in all required fields."
        elif len(username.strip()) < 3:
            error_message = "Username must be at least 3 characters long."
        elif len(password) < 6:
            error_message = "Password must be at least 6 characters long."
        elif username in users:
            error_message = f"Username '{username}' is already taken. Please choose a different username."
        else:
            users[username] = password
            success_message = f"Account created successfully! You can now log in with username '{username}'."
            # Instead of redirecting immediately, show success message
            # return redirect("/login")

    content = f"""
    <div class="row justify-content-center">
        <div class="col-md-5 col-lg-4">
            <div class="card-glass p-4">
                <div class="text-center mb-4">
                    <i class="fas fa-user-plus fa-2x mb-3" style="color: #4facfe;"></i>
                    <h2 class="mb-3 fw-bold">Create Account</h2>
                    <p class="text-white-50 small">Join thousands of users securing their digital assets</p>
                </div>
                
                {f'''
                <div class="alert alert-danger bg-transparent border-danger text-danger mb-3" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Registration Failed:</strong> {error_message}
                </div>
                ''' if error_message else ''}
                
                {f'''
                <div class="alert alert-success bg-transparent border-success text-success mb-3" role="alert">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>Success:</strong> {success_message}
                    <div class="mt-2">
                        <a href="/login" class="btn btn-success btn-sm">
                            <i class="fas fa-sign-in-alt me-1"></i>Continue to Login
                        </a>
                    </div>
                </div>
                ''' if success_message else ''}
                
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">
                            <i class="fas fa-user me-2"></i>Username
                        </label>
                        <input name="username" class="form-control" placeholder="Enter your username" 
                               value="{request.form.get('username', '') if request.method == 'POST' else ''}" required>
                        <div class="form-text text-white-50 small mt-1">
                            <i class="fas fa-info-circle me-1"></i>Must be at least 3 characters long
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">
                            <i class="fas fa-lock me-2"></i>Password
                        </label>
                        <input name="password" type="password" class="form-control" placeholder="Create a secure password" required>
                        <div class="form-text text-white-50 small mt-1">
                            <i class="fas fa-shield-alt me-1"></i>Minimum 6 characters for security
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-success w-100 mb-3" {'disabled' if success_message else ''}>
                        <i class="fas fa-rocket me-2"></i>Create Account
                    </button>
                </form>
                
                <div class="text-center">
                    <p class="text-white-50 mb-2 small">Already have an account?</p>
                    <a href="/login" class="btn btn-glass btn-sm">
                        <i class="fas fa-sign-in-alt me-2"></i>Sign In
                    </a>
                </div>
                
                <div class="mt-3 pt-3 border-top border-secondary">
                    <div class="row text-center">
                        <div class="col-4">
                            <i class="fas fa-shield-alt text-success fa-lg mb-1"></i>
                            <p class="small text-white-50 mb-0">Secure</p>
                        </div>
                        <div class="col-4">
                            <i class="fas fa-lock text-info fa-lg mb-1"></i>
                            <p class="small text-white-50 mb-0">Encrypted</p>
                        </div>
                        <div class="col-4">
                            <i class="fas fa-users text-warning fa-lg mb-1"></i>
                            <p class="small text-white-50 mb-0">Trusted</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    attempted_username = ""
    
    # Check for query parameters for error messages
    error_type = request.args.get('error')
    if error_type == 'session_required':
        error_message = "Please log in to access your dashboard."
    elif error_type == 'invalid_token':
        error_message = "Your session has expired or is invalid. Please log in again."
    elif error_type == 'access_denied':
        error_message = "Session expired. Please log in again to continue."
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        attempted_username = username or ""
        
        if not username or not password:
            error_message = "Please enter both username and password."
        elif username not in users:
            error_message = f"No account found with username '{username}'. Please check your username or create an account."
        elif users.get(username) != password:
            error_message = "Incorrect password. Please check your password and try again."
        else:
            # Successful login
            token = jwt.encode({"user": username, "role": "user"}, SECRET_KEY, algorithm="HS256")
            resp = make_response(redirect("/dashboard"))
            resp.set_cookie("token", token)
            return resp

    # Determine alert type based on error source
    alert_type = "info" if error_type in ['session_required', 'invalid_token', 'access_denied'] else "danger"
    alert_icon = "fa-info-circle" if alert_type == "info" else "fa-exclamation-triangle"

    content = f"""
    <div class="row justify-content-center">
        <div class="col-md-5 col-lg-4">
            <div class="card-glass p-4">
                <div class="text-center mb-4">
                    <i class="fas fa-sign-in-alt fa-2x mb-3" style="color: #667eea;"></i>
                    <h2 class="mb-3 fw-bold">Welcome Back</h2>
                    <p class="text-white-50 small">Sign in to access your secure dashboard</p>
                </div>
                
                {f'''
                <div class="alert alert-{alert_type} bg-transparent border-{alert_type} text-{alert_type} mb-3" role="alert">
                    <div class="row align-items-center">
                        <div class="col-2 text-center">
                            <i class="fas {alert_icon} fa-lg"></i>
                        </div>
                        <div class="col-10">
                            <h6 class="mb-1">{'Authentication Required' if alert_type == 'info' else 'Login Failed'}</h6>
                            <p class="mb-0 small">{error_message}</p>
                        </div>
                    </div>
                </div>
                ''' if error_message else ''}
                
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">
                            <i class="fas fa-user me-2"></i>Username
                        </label>
                        <input name="username" class="form-control {'is-invalid' if error_message and 'username' in (error_message or '') else ''}" 
                               placeholder="Enter your username" value="{attempted_username}" required>
                        <div class="form-text text-white-50 small mt-1">
                            <i class="fas fa-info-circle me-1"></i>Enter the username you registered with
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">
                            <i class="fas fa-lock me-2"></i>Password
                        </label>
                        <input name="password" type="password" class="form-control {'is-invalid' if error_message and 'password' in (error_message or '') else ''}" 
                               placeholder="Enter your password" required>
                        <div class="form-text text-white-50 small mt-1">
                            <i class="fas fa-shield-alt me-1"></i>Password is case-sensitive
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="rememberMe">
                            <label class="form-check-label text-white-50 small" for="rememberMe">
                                <i class="fas fa-clock me-1"></i>Remember me for 30 days
                            </label>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100 mb-3">
                        <i class="fas fa-shield-alt me-2"></i>Secure Login
                    </button>
                </form>
                
                <div class="text-center mb-3">
                    <a href="#" class="text-info text-decoration-none small">
                        <i class="fas fa-key me-1"></i>Forgot your password?
                    </a>
                </div>
                
                <div class="text-center">
                    <p class="text-white-50 mb-2 small">Don't have an account?</p>
                    <a href="/register" class="btn btn-glass btn-sm">
                        <i class="fas fa-user-plus me-2"></i>Create Account
                    </a>
                </div>
                
                <div class="mt-3 pt-3 border-top border-secondary">
                    <div class="row text-center">
                        <div class="col-6">
                            <i class="fas fa-users text-primary fa-lg mb-1"></i>
                            <p class="small text-white-50 mb-0">{len(users):,} Active Users</p>
                        </div>
                        <div class="col-6">
                            <i class="fas fa-shield-alt text-success fa-lg mb-1"></i>
                            <p class="small text-white-50 mb-0">Bank-Level Security</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

@app.route("/dashboard")
def dashboard():
    token = request.cookies.get("token")
    if not token:
        # No token provided - redirect to login with message
        return redirect("/login?error=session_required")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        role = payload.get("role")
        content = f"""
        <div class="row mb-4">
            <div class="col-12">
                <div class="card-glass p-4">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1 class="h2 fw-bold mb-2">
                                <i class="fas fa-tachometer-alt me-3 text-primary"></i>
                                Security Dashboard
                            </h1>
                            <p class="lead mb-0">
                                Welcome <span class="fw-bold text-warning">{user}</span> | 
                                Access Level: <span class="badge bg-gradient rounded-pill px-3 py-1" style="background: var(--primary-gradient);">
                                    <i class="fas fa-user-tag me-1"></i>{role.upper()}
                                </span>
                            </p>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="stats-card">
                                <i class="fas fa-shield-alt text-success fa-2x mb-2"></i>
                                <h6>System Status</h6>
                                <span class="badge bg-success">
                                    <i class="fas fa-check-circle me-1"></i>SECURE
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <i class="fas fa-shield-alt text-success fa-2x mb-2"></i>
                    <div class="stats-number">247</div>
                    <p class="mb-0">Threats Blocked</p>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <i class="fas fa-eye text-info fa-2x mb-2"></i>
                    <div class="stats-number">1,847</div>
                    <p class="mb-0">Events Monitored</p>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <i class="fas fa-lock text-warning fa-2x mb-2"></i>
                    <div class="stats-number">99.2%</div>
                    <p class="mb-0">Security Score</p>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="stats-card">
                    <i class="fas fa-chart-line text-primary fa-2x mb-2"></i>
                    <div class="stats-number">24h</div>
                    <p class="mb-0">Uptime</p>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-6 mb-4">
                <div class="card-glass p-4">
                    <h5 class="mb-3">
                        <i class="fas fa-activity me-2 text-success"></i>
                        Recent Activity
                    </h5>
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span><i class="fas fa-sign-in-alt text-success me-2"></i>User login successful</span>
                            <small class="text-white-50">2 min ago</small>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span><i class="fas fa-shield-alt text-info me-2"></i>Security scan completed</span>
                            <small class="text-white-50">15 min ago</small>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span><i class="fas fa-ban text-danger me-2"></i>Threat blocked: IP 192.168.1.100</span>
                            <small class="text-white-50">1 hour ago</small>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span><i class="fas fa-sync text-warning me-2"></i>System update applied</span>
                            <small class="text-white-50">3 hours ago</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 mb-4">
                <div class="card-glass p-4">
                    <h5 class="mb-3">
                        <i class="fas fa-exclamation-triangle me-2 text-warning"></i>
                        Security Alerts
                    </h5>
                    <div class="mb-3">
                        <div class="alert alert-warning bg-transparent border-warning text-warning mb-2" role="alert">
                            <i class="fas fa-info-circle me-2"></i>
                            <strong>Medium Priority:</strong> Unusual login pattern detected
                        </div>
                        <div class="alert alert-info bg-transparent border-info text-info mb-2" role="alert">
                            <i class="fas fa-bell me-2"></i>
                            <strong>Info:</strong> Scheduled maintenance in 2 hours
                        </div>
                        <div class="alert alert-success bg-transparent border-success text-success mb-2" role="alert">
                            <i class="fas fa-check-circle me-2"></i>
                            <strong>Resolved:</strong> SSL certificate renewed successfully
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card-glass p-4">
                    <h5 class="mb-3">
                        <i class="fas fa-cogs me-2 text-primary"></i>
                        Quick Actions
                    </h5>
                    <div class="row">
                        <div class="col-md-3 mb-3">
                            <a href="#" class="btn btn-glass w-100 p-3">
                                <i class="fas fa-scan-virus fa-2x mb-2 d-block"></i>
                                Run Security Scan
                            </a>
                        </div>
                        <div class="col-md-3 mb-3">
                            <a href="#" class="btn btn-glass w-100 p-3">
                                <i class="fas fa-download fa-2x mb-2 d-block"></i>
                                Download Report
                            </a>
                        </div>
                        <div class="col-md-3 mb-3">
                            <a href="#" class="btn btn-glass w-100 p-3">
                                <i class="fas fa-users fa-2x mb-2 d-block"></i>
                                Manage Users
                            </a>
                        </div>
                        <div class="col-md-3 mb-3">
                            <a href="/admin" class="btn btn-warning w-100 p-3 pulse">
                                <i class="fas fa-crown fa-2x mb-2 d-block"></i>
                                Admin Panel
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-8 mb-4">
                <div class="card-glass p-4">
                    <h5 class="mb-3">
                        <i class="fas fa-chart-bar me-2 text-info"></i>
                        Security Metrics
                    </h5>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>Firewall Protection</span>
                                    <span class="text-success">98%</span>
                                </div>
                                <div class="progress" style="height: 8px; background: rgba(255,255,255,0.1);">
                                    <div class="progress-bar bg-success" style="width: 98%"></div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>Malware Detection</span>
                                    <span class="text-info">94%</span>
                                </div>
                                <div class="progress" style="height: 8px; background: rgba(255,255,255,0.1);">
                                    <div class="progress-bar bg-info" style="width: 94%"></div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>Data Encryption</span>
                                    <span class="text-warning">100%</span>
                                </div>
                                <div class="progress" style="height: 8px; background: rgba(255,255,255,0.1);">
                                    <div class="progress-bar bg-warning" style="width: 100%"></div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>Access Control</span>
                                    <span class="text-primary">96%</span>
                                </div>
                                <div class="progress" style="height: 8px; background: rgba(255,255,255,0.1);">
                                    <div class="progress-bar bg-primary" style="width: 96%"></div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>Network Security</span>
                                    <span class="text-success">92%</span>
                                </div>
                                <div class="progress" style="height: 8px; background: rgba(255,255,255,0.1);">
                                    <div class="progress-bar bg-success" style="width: 92%"></div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>System Integrity</span>
                                    <span class="text-info">99%</span>
                                </div>
                                <div class="progress" style="height: 8px; background: rgba(255,255,255,0.1);">
                                    <div class="progress-bar bg-info" style="width: 99%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4 mb-4">
                <div class="card-glass p-4">
                    <h5 class="mb-3">
                        <i class="fas fa-globe me-2 text-warning"></i>
                        Global Threat Map
                    </h5>
                    <div class="text-center mb-3">
                        <i class="fas fa-map-marked-alt fa-3x text-primary mb-3"></i>
                        <p class="mb-2">Active Threats Worldwide</p>
                        <div class="stats-number" style="font-size: 1.5rem;">1,247</div>
                    </div>
                    <div class="mb-2">
                        <div class="d-flex justify-content-between">
                            <span><i class="fas fa-circle text-danger me-2"></i>Critical</span>
                            <span>23</span>
                        </div>
                    </div>
                    <div class="mb-2">
                        <div class="d-flex justify-content-between">
                            <span><i class="fas fa-circle text-warning me-2"></i>High</span>
                            <span>156</span>
                        </div>
                    </div>
                    <div class="mb-2">
                        <div class="d-flex justify-content-between">
                            <span><i class="fas fa-circle text-info me-2"></i>Medium</span>
                            <span>789</span>
                        </div>
                    </div>
                    <div class="mb-2">
                        <div class="d-flex justify-content-between">
                            <span><i class="fas fa-circle text-success me-2"></i>Low</span>
                            <span>279</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        return render_template_string(BASE_HTML, content=content)
    except jwt.InvalidTokenError:
        # Invalid token - redirect to login with error message
        return redirect("/login?error=invalid_token")

@app.route("/admin")
def admin():
    token = request.cookies.get("token")
    if not token:
        return redirect("/login?error=session_required")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        role = payload.get("role")
        
        if role == "admin":
            # Admin access granted - show the flag
            flag_content = open("flag.txt").read().strip()
            content = f"""
            <div class="row justify-content-center">
                <div class="col-lg-10">
                    <div class="card-glass p-5 mb-4">
                        <div class="text-center mb-4">
                            <i class="fas fa-crown fa-4x mb-3" style="color: #f5576c;"></i>
                            <h1 class="display-5 fw-bold mb-3">
                                <span style="background: var(--secondary-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                                    ADMIN CONTROL PANEL
                                </span>
                            </h1>
                            <p class="lead">Welcome, Administrator <strong>{user}</strong></p>
                        </div>
                        
                        <div class="alert alert-success bg-transparent border-success text-success mb-4" role="alert">
                            <i class="fas fa-check-circle me-2"></i>
                            <strong>Access Granted:</strong> Administrative privileges confirmed
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-md-3 mb-3">
                                <div class="stats-card">
                                    <i class="fas fa-users text-primary fa-2x mb-2"></i>
                                    <div class="stats-number">1,247</div>
                                    <p class="mb-0">Total Users</p>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="stats-card">
                                    <i class="fas fa-server text-success fa-2x mb-2"></i>
                                    <div class="stats-number">99.9%</div>
                                    <p class="mb-0">System Health</p>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="stats-card">
                                    <i class="fas fa-shield-alt text-warning fa-2x mb-2"></i>
                                    <div class="stats-number">2,847</div>
                                    <p class="mb-0">Security Events</p>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="stats-card">
                                    <i class="fas fa-database text-info fa-2x mb-2"></i>
                                    <div class="stats-number">847GB</div>
                                    <p class="mb-0">Data Processed</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-md-6 mb-4">
                                <div class="feature-card h-100">
                                    <i class="fas fa-users-cog text-primary fa-3x mb-3"></i>
                                    <h4 class="mb-3">User Management</h4>
                                    <p class="text-white-50 mb-3">Manage user accounts, permissions, and access levels across the platform.</p>
                                    <button class="btn btn-primary">
                                        <i class="fas fa-cog me-2"></i>Manage Users
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-6 mb-4">
                                <div class="feature-card h-100">
                                    <i class="fas fa-chart-bar text-success fa-3x mb-3"></i>
                                    <h4 class="mb-3">System Analytics</h4>
                                    <p class="text-white-50 mb-3">View detailed analytics, performance metrics, and system reports.</p>
                                    <button class="btn btn-success">
                                        <i class="fas fa-chart-line me-2"></i>View Reports
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-md-6 mb-4">
                                <div class="feature-card h-100">
                                    <i class="fas fa-shield-alt text-warning fa-3x mb-3"></i>
                                    <h4 class="mb-3">Security Center</h4>
                                    <p class="text-white-50 mb-3">Configure security policies, monitor threats, and manage firewall rules.</p>
                                    <button class="btn btn-warning">
                                        <i class="fas fa-shield me-2"></i>Security Config
                                    </button>
                                </div>
                            </div>
                            <div class="col-md-6 mb-4">
                                <div class="feature-card h-100">
                                    <i class="fas fa-cogs text-info fa-3x mb-3"></i>
                                    <h4 class="mb-3">System Settings</h4>
                                    <p class="text-white-50 mb-3">Configure global settings, API endpoints, and system preferences.</p>
                                    <button class="btn" style="background: var(--dark-gradient); border: none; color: white;">
                                        <i class="fas fa-wrench me-2"></i>Settings
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card-glass p-4 mb-4" style="border: 2px solid #f5576c;">
                            <div class="row align-items-center">
                                <div class="col-md-2 text-center">
                                    <i class="fas fa-flag fa-4x" style="color: #f5576c;"></i>
                                </div>
                                <div class="col-md-8">
                                    <h4 class="mb-2">
                                        <span style="color: #f5576c;">SYSTEM FLAG RETRIEVED</span>
                                    </h4>
                                    <p class="mb-2 text-white-50">Congratulations! You have successfully gained administrative access.</p>
                                    <div class="alert alert-info bg-transparent border-info text-info">
                                        <i class="fas fa-key me-2"></i>
                                        <strong>FLAG:</strong> <code style="background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 4px; font-size: 1.1em;">{flag_content}</code>
                                    </div>
                                </div>
                                <div class="col-md-2 text-center">
                                    <div class="pulse">
                                        <i class="fas fa-trophy fa-3x text-warning"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="text-center">
                            <a href="/dashboard" class="btn btn-glass me-3">
                                <i class="fas fa-arrow-left me-2"></i>Back to Dashboard
                            </a>
                            <form action="/logout" method="POST" class="d-inline">
                                <button type="submit" class="btn btn-glass">
                                    <i class="fas fa-sign-out-alt me-2"></i>Secure Logout
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            """
            return render_template_string(BASE_HTML, content=content)
        else:
            # Regular user trying to access admin panel
            content = f"""
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="card-glass p-5">
                        <div class="text-center mb-4">
                            <i class="fas fa-exclamation-triangle fa-4x mb-3 text-danger"></i>
                            <h1 class="display-6 fw-bold mb-3 text-danger">ACCESS DENIED</h1>
                            <p class="lead">Insufficient Privileges</p>
                        </div>
                        
                        <div class="alert alert-danger bg-transparent border-danger text-danger mb-4" role="alert">
                            <div class="row align-items-center">
                                <div class="col-md-2 text-center">
                                    <i class="fas fa-ban fa-3x"></i>
                                </div>
                                <div class="col-md-10">
                                    <h5 class="mb-2">Unauthorized Access Attempt Detected</h5>
                                    <p class="mb-1"><strong>User:</strong> {user}</p>
                                    <p class="mb-1"><strong>Role:</strong> {role}</p>
                                    <p class="mb-1"><strong>Required Role:</strong> admin</p>
                                    <p class="mb-0"><strong>Action:</strong> Access to Admin Panel Denied</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row mb-4">
                            <div class="col-md-6 mb-3">
                                <div class="feature-card">
                                    <i class="fas fa-user-shield text-warning fa-3x mb-3"></i>
                                    <h5 class="mb-3">Your Current Access Level</h5>
                                    <div class="mb-3">
                                        <span class="badge bg-gradient rounded-pill px-3 py-2" style="background: var(--primary-gradient);">
                                            <i class="fas fa-user me-1"></i>{role.upper()} USER
                                        </span>
                                    </div>
                                    <p class="text-white-50 small">
                                        You have standard user privileges with access to dashboard and personal settings.
                                    </p>
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <div class="feature-card">
                                    <i class="fas fa-crown text-danger fa-3x mb-3"></i>
                                    <h5 class="mb-3">Required Access Level</h5>
                                    <div class="mb-3">
                                        <span class="badge bg-gradient rounded-pill px-3 py-2" style="background: var(--secondary-gradient);">
                                            <i class="fas fa-crown me-1"></i>ADMIN USER
                                        </span>
                                    </div>
                                    <p class="text-white-50 small">
                                        Administrative privileges required to access the control panel and system configuration.
                                    </p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card-glass p-4 mb-4">
                            <h5 class="mb-3">
                                <i class="fas fa-info-circle me-2 text-info"></i>
                                Available Actions
                            </h5>
                            <div class="row">
                                <div class="col-md-6 mb-2">
                                    <i class="fas fa-check text-success me-2"></i>
                                    Access personal dashboard
                                </div>
                                <div class="col-md-6 mb-2">
                                    <i class="fas fa-check text-success me-2"></i>
                                    View security metrics
                                </div>
                                <div class="col-md-6 mb-2">
                                    <i class="fas fa-check text-success me-2"></i>
                                    Update profile settings
                                </div>
                                <div class="col-md-6 mb-2">
                                    <i class="fas fa-check text-success me-2"></i>
                                    Download personal reports
                                </div>
                                <div class="col-md-6 mb-2">
                                    <i class="fas fa-times text-danger me-2"></i>
                                    User management
                                </div>
                                <div class="col-md-6 mb-2">
                                    <i class="fas fa-times text-danger me-2"></i>
                                    System configuration
                                </div>
                                <div class="col-md-6 mb-2">
                                    <i class="fas fa-times text-danger me-2"></i>
                                    Security policy settings
                                </div>
                                <div class="col-md-6 mb-2">
                                    <i class="fas fa-times text-danger me-2"></i>
                                    Admin control panel
                                </div>
                            </div>
                        </div>
                        
                        <div class="alert alert-info bg-transparent border-info text-info mb-4" role="alert">
                            <i class="fas fa-lightbulb me-2"></i>
                            <strong>Need Admin Access?</strong> Contact your system administrator to request elevated privileges. 
                            All access attempts are logged for security purposes.
                        </div>
                        
                        <div class="text-center">
                            <a href="/dashboard" class="btn btn-primary me-3">
                                <i class="fas fa-arrow-left me-2"></i>Return to Dashboard
                            </a>
                            <form action="/logout" method="POST" class="d-inline">
                                <button type="submit" class="btn btn-glass">
                                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            """
            return render_template_string(BASE_HTML, content=content)
            
    except jwt.InvalidTokenError:
        # Invalid token case
        content = """
        <div class="row justify-content-center">
            <div class="col-lg-6">
                <div class="card-glass p-5">
                    <div class="text-center mb-4">
                        <i class="fas fa-exclamation-circle fa-4x mb-3 text-warning"></i>
                        <h1 class="display-6 fw-bold mb-3">INVALID SESSION</h1>
                        <p class="lead">Authentication Token Error</p>
                    </div>
                    
                    <div class="alert alert-warning bg-transparent border-warning text-warning mb-4" role="alert">
                        <div class="text-center">
                            <i class="fas fa-key fa-2x mb-3"></i>
                            <h5 class="mb-2">Token Validation Failed</h5>
                            <p class="mb-0">Your authentication token is invalid, expired, or corrupted.</p>
                        </div>
                    </div>
                    
                    <div class="feature-card mb-4">
                        <h5 class="mb-3">
                            <i class="fas fa-shield-alt me-2 text-danger"></i>
                            Security Violation Detected
                        </h5>
                        <ul class="text-white-50 mb-0">
                            <li>Invalid JWT signature detected</li>
                            <li>Token may have been tampered with</li>
                            <li>Session has been terminated for security</li>
                            <li>Please re-authenticate to continue</li>
                        </ul>
                    </div>
                    
                    <div class="text-center">
                        <a href="/login" class="btn btn-warning me-3">
                            <i class="fas fa-sign-in-alt me-2"></i>Re-authenticate
                        </a>
                        <a href="/" class="btn btn-glass">
                            <i class="fas fa-home me-2"></i>Go Home
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """
        return render_template_string(BASE_HTML, content=content)

@app.route("/logout", methods=["POST"])
def logout():
    resp = make_response(redirect("/"))
    resp.delete_cookie("token")
    return resp

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
