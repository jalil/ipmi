from flask import Flask, render_template, request, redirect, url_for
import subprocess
import paramiko
import csv
import os
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Helper function to read server lists
def read_server_list(filename):
    servers = []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 3:  # Ensure correct number of values in each row
                servers.append({
                    'server_name': row[0],
                    'bmc_server_ip': row[1],
                    'kubernetes_server_ip': row[2]
                })
    return servers

# Function to check BMC status using ipmitool
def get_server_status(server_name, bmc_server_ip):
    try:
        status = subprocess.check_output(
            ["ipmitool", "-I", "lanplus", "-H", bmc_server_ip, "-U", "admin", "-P", "password", "chassis", "power", "status"],
            stderr=subprocess.STDOUT
        ).decode('utf-8')
        return status.strip().replace('Chassis Power is ', '')  # Simplified to 'on' or 'off'
    except subprocess.CalledProcessError:
        return 'Command failed'

# Function to check if kubelet is running on Kubernetes server
def check_kubelet_status(kubernetes_server_ip):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(kubernetes_server_ip, username='root', password='password')

        stdin, stdout, stderr = ssh.exec_command("systemctl is-active kubelet")
        status = stdout.read().decode().strip()
        ssh.close()

        if status == 'active':
            return 'Running'
        else:
            return 'Not running'
    except paramiko.SSHException:
        return 'SSH failed'

# Wrapper function for asynchronous status checks
def check_status(server):
    bmc_status = get_server_status(server['server_name'], server['bmc_server_ip'])
    kubelet_status = check_kubelet_status(server['kubernetes_server_ip'])
    return {
        'server_name': server['server_name'],
        'bmc_server_ip': server['bmc_server_ip'],
        'kubernetes_server_ip': server['kubernetes_server_ip'],
        'bmc_status': bmc_status,
        'kubelet_status': kubelet_status
    }

@app.route('/')
def index():
    # Load server lists
    servers_group1 = read_server_list('servers_group1.txt')
    servers_group2 = read_server_list('servers_group2.txt')

    # Use ThreadPoolExecutor for concurrent status checks
    with ThreadPoolExecutor() as executor:
        group1_statuses = list(executor.map(check_status, servers_group1))
        group2_statuses = list(executor.map(check_status, servers_group2))

    return render_template('index.html', group1_statuses=group1_statuses, group2_statuses=group2_statuses)

# Power cycle function (Example only)
@app.route('/power_cycle/<server_name>/<bmc_server_ip>', methods=['POST'])
def power_cycle(server_name, bmc_server_ip):
    reason = request.form.get('reason')  # Get reason from textarea input
    try:
        subprocess.check_output(
            ["ipmitool", "-I", "lanplus", "-H", bmc_server_ip, "-U", "admin", "-P", "password", "chassis", "power", "cycle"],
            stderr=subprocess.STDOUT
        ).decode('utf-8')
        return redirect(url_for('index'))
    except subprocess.CalledProcessError:
        return "Failed to power cycle", 500

if __name__ == '__main__':
    app.run(debug=True)

