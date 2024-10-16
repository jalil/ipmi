from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_caching import Cache
import subprocess
from concurrent.futures import ThreadPoolExecutor
import paramiko
import time

app = Flask(__name__)

# PostgreSQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:admin@localhost/server_dashboard'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# Cache Configuration
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300})

# In-memory dictionary for basic auth
users = {
    "admin": "admin"
}

# Model for saving power cycle logs
class PowerCycleLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    bmc_ip = db.Column(db.String(80), nullable=False)
    reason = db.Column(db.String(120), nullable=False)

    def __init__(self, username, bmc_ip, reason):
        self.username = username
        self.bmc_ip = bmc_ip
        self.reason = reason

# Basic Authentication
@auth.get_password
def get_pw(username):
    if username in users:
        return users.get(username)
    return None

# Load servers from the server list files (one for each group)
def load_servers(file_path):
    with open(file_path) as file:
        servers = [line.strip().split(',') for line in file]
    return servers

# Function to get the BMC status using ipmitool
@cache.memoize(timeout=60)  # Cache the result for 60 seconds
def get_bmc_status(bmc_ip):
    try:
        result = subprocess.run(['ipmitool', '-I', 'lanplus', '-H', bmc_ip, '-U', 'admin', '-P', 'password', 'chassis', 'power', 'status'], capture_output=True, text=True, timeout=5)
        if 'on' in result.stdout:
            return 'On'
        elif 'off' in result.stdout:
            return 'Off'
        else:
            return 'Unknown'
    except subprocess.TimeoutExpired:
        return 'Timeout'
    except Exception as e:
        return f'Error: {e}'

# Function to check if kubelet is running on a given Kubernetes IP
@cache.memoize(timeout=60)  # Cache the result for 60 seconds
def check_kubelet_status(kube_ip):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(kube_ip, username='user', password='password', timeout=5)
        stdin, stdout, stderr = ssh.exec_command('systemctl is-active kubelet')
        kubelet_status = stdout.read().decode().strip()
        ssh.close()
        return "active" if kubelet_status == "active" else "inactive"
    except Exception as e:
        return f'Error: {e}'

# Function to power cycle the server
def power_cycle_server(bmc_ip):
    try:
        subprocess.run(['ipmitool', '-I', 'lanplus', '-H', bmc_ip, '-U', 'admin', '-P', 'password', 'chassis', 'power', 'cycle'], capture_output=True, text=True, timeout=10)
        cache.delete_memoized(get_bmc_status, bmc_ip)  # Invalidate the cache for this BMC IP
        return "Power cycle initiated"
    except subprocess.TimeoutExpired:
        return 'Timeout'
    except Exception as e:
        return f'Error: {e}'

# Route to fetch BMC status dynamically
@app.route('/check_bmc_status/<bmc_ip>', methods=['POST'])
def check_bmc_status(bmc_ip):
    status = get_bmc_status(bmc_ip)
    return jsonify({'status': status})

# Route to power cycle the server and provide a reason
@app.route('/power_cycle/<bmc_ip>', methods=['POST'])
@auth.login_required
def power_cycle(bmc_ip):
    reason = request.form.get('reason')
    result = power_cycle_server(bmc_ip)

    # Log the power cycle action
    log_entry = PowerCycleLog(username=auth.username(), bmc_ip=bmc_ip, reason=reason)
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({'result': result})

# Homepage route that loads and displays the server statuses
@app.route('/')
@auth.login_required
def index():
    servers_group1 = load_servers('servers_group1.txt')
    servers_group2 = load_servers('servers_group2.txt')
    servers_group3 = load_servers('servers_group3.txt')

    # Use ThreadPoolExecutor to run BMC and kubelet checks concurrently
    with ThreadPoolExecutor() as executor:
        futures = []
        for server in servers_group1 + servers_group2 + servers_group3:
            server_name, bmc_ip, kube_ip = server
            futures.append(executor.submit(get_bmc_status, bmc_ip))
            futures.append(executor.submit(check_kubelet_status, kube_ip))

        # Wait for all futures to complete
        results = [future.result() for future in futures]

    # Assign results back to servers
    for i, server in enumerate(servers_group1 + servers_group2 + servers_group3):
        server.append(results[i*2])    # BMC status
        server.append(results[i*2+1])  # Kubelet status

    return render_template('index.html', servers_group1=servers_group1, servers_group2=servers_group2, servers_group3=servers_group3)

if __name__ == '__main__':
    db.create_all()  # Create tables in PostgreSQL
    app.run(debug=True)
