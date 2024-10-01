from flask import Flask, render_template, request, jsonify
import subprocess
from concurrent.futures import ThreadPoolExecutor
import paramiko

app = Flask(__name__)

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
def power_cycle_server(bmc_ip, reason=None):
    try:
        if reason:
            print(f"Power cycling server with BMC IP {bmc_ip}. Reason: {reason}")
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

# Route to power cycle the server and provide a reason
@app.route('/power_cycle/<bmc_ip>', methods=['POST'])
def power_cycle(bmc_ip):
    reason = request.form.get('reason')
    print(f"Power cycling server with BMC IP: {bmc_ip}. Reason: {reason}")
    result = power_cycle_server(bmc_ip, reason)
    return jsonify({'result': result, 'reason': reason})

# Homepage route that loads and displays the server statuses
@app.route('/')
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

