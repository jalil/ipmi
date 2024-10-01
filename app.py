from flask import Flask, render_template, request, jsonify, redirect, url_for, g
import subprocess
from concurrent.futures import ThreadPoolExecutor
import paramiko
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from flask import request, Response

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///power_cycles.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define a model for storing power cycle actions
class PowerCycleAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bmc_ip = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(50), nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()

# Basic Auth decorator
def check_auth(username, password):
    return username == 'admin' and password == 'admin'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your login!\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        g.username = auth.username  # Store the authenticated user's username in `g`
        return f(*args, **kwargs)
    return decorated

# Load servers from the server list files (one for each group)
def load_servers(file_path):
    with open(file_path) as file:
        servers = [line.strip().split(',')[:3] for line in file]
    return servers

# Function to get the BMC status using ipmitool
def get_bmc_status(bmc_ip):
    try:
        result = subprocess.run(['ipmitool', '-I', 'lanplus', '-H', bmc_ip, '-U', 'admin', '-P', 'password', 'chassis', 'power', 'status'], capture_output=True, text=True)
        if 'on' in result.stdout.lower():
            return 'On'
        elif 'off' in result.stdout.lower():
            return 'Off'
        else:
            return 'Unknown'
    except Exception as e:
        return f'Error: {e}'

# Function to check if kubelet is running on a given Kubernetes IP
def check_kubelet_status(kube_ip):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(kube_ip, username='user', password='password')
        stdin, stdout, stderr = ssh.exec_command('systemctl is-active kubelet')
        kubelet_status = stdout.read().decode().strip()
        ssh.close()
        return "Active" if kubelet_status == "active" else "Inactive"
    except Exception as e:
        return f'Error: {e}'

# Function to power cycle the server
def power_cycle_server(bmc_ip):
    try:
        subprocess.run(['ipmitool', '-I', 'lanplus', '-H', bmc_ip, '-U', 'admin', '-P', 'password', 'chassis', 'power', 'cycle'], capture_output=True, text=True)
        return "Power cycle initiated"
    except Exception as e:
        return f'Error: {e}'

# Route to fetch BMC status dynamically
@app.route('/check_bmc_status/<bmc_ip>', methods=['POST'])
def check_bmc_status_route(bmc_ip):
    status = get_bmc_status(bmc_ip)
    return jsonify({'status': status})

# Route to check Kubelet status dynamically
@app.route('/check_kubelet_status/<kube_ip>', methods=['POST'])
def check_kubelet_status_route(kube_ip):
    status = check_kubelet_status(kube_ip)
    return jsonify({'status': status})

# Route to power cycle the server and provide a reason, saving to the database
@app.route('/power_cycle/<bmc_ip>', methods=['POST'])
@requires_auth
def power_cycle(bmc_ip):
    reason = request.form.get('reason')  # Get reason from the form
    username = g.username  # Get the authenticated username from `g`

    # Save the reason and username to the SQLite database
    new_action = PowerCycleAction(bmc_ip=bmc_ip, reason=reason, username=username)
    db.session.add(new_action)
    db.session.commit()

    result = power_cycle_server(bmc_ip)  # Power cycle the server
    return jsonify({'result': result, 'reason': reason, 'username': username})

# Homepage route that loads and displays the server statuses
@app.route('/')
@requires_auth
def index():
    servers_group1 = load_servers('servers_group1.txt')
    servers_group2 = load_servers('servers_group2.txt')
    servers_group3 = load_servers('servers_group3.txt')

    with ThreadPoolExecutor() as executor:
        for server in servers_group1 + servers_group2 + servers_group3:
            server_name, bmc_ip, kube_ip = server
            server.append(executor.submit(get_bmc_status, bmc_ip).result())
            server.append(executor.submit(check_kubelet_status, kube_ip).result())

    return render_template('index.html', servers_group1=servers_group1, servers_group2=servers_group2, servers_group3=servers_group3)

if __name__ == '__main__':
    app.run(debug=True)

