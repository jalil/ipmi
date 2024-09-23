from flask import Flask, render_template, request, redirect, url_for
import subprocess

app = Flask(__name__)

def load_servers(file_path):
    servers = []
    with open(file_path, 'r') as file:
        for line in file.readlines():
            try:
                server_name, ip = line.strip().split(',')
                servers.append((server_name, ip))
            except ValueError:
                print(f"Skipping malformed line in {file_path}: {line.strip()}")
    return servers

def get_server_status(ip):
    try:
        result = subprocess.run(
            ['ipmitool', '-I', 'lanplus', '-H', ip, '-U', 'username', '-P', 'password', 'power', 'status'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "Error getting status"
    except Exception as e:
        return f"Command not available: {e}"

def power_cycle_server(ip, reason):
    try:
        subprocess.run(
            ['ipmitool', '-I', 'lanplus', '-H', ip, '-U', 'username', '-P', 'password', 'power', 'cycle'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Log the reason for power cycle
        with open("power_cycle_logs.txt", "a") as log_file:
            log_file.write(f"Power cycle initiated for {ip}. Reason: {reason}\n")
        return "Power cycle initiated"
    except Exception as e:
        return f"Failed to power cycle: {e}"

@app.route('/')
def index():
    servers1 = load_servers('servers1.txt')
    servers2 = load_servers('servers2.txt')
    servers3 = load_servers('servers3.txt')
    servers1_status = [(server_name, ip, get_server_status(ip)) for server_name, ip in servers1]
    servers2_status = [(server_name, ip, get_server_status(ip)) for server_name, ip in servers2]
    servers3_status = [(server_name, ip, get_server_status(ip)) for server_name, ip in servers3]

    return render_template('index.html', servers1=servers1_status, servers2=servers2_status, servers3=servers3_status)

@app.route('/power_cycle/<ip>', methods=['POST'])
def power_cycle(ip):
    reason = request.form.get('reason')
    status = power_cycle_server(ip, reason)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

