from flask import Flask, render_template, redirect, url_for
import subprocess
import time
from threading import Thread

# Initialize the Flask app
app = Flask(__name__)

# List of server IP addresses
servers = [
    "192.168.1.100",
    "192.168.1.101",
    "192.168.1.102"
]

# Dictionary to store server statuses
server_statuses = {}

# Function to get power status of a server using ipmitool
def get_server_status(server_ip):
    try:
        # Execute the ipmitool command to get the power status of the server
        command = f"ipmitool -I lanplus -H {server_ip} -U admin -P password chassis power status"
        result = subprocess.check_output(command, shell=True)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return "Command not available"

# Function to power cycle (restart) a server using ipmitool
def power_cycle_server(server_ip):
    try:
        # Execute the ipmitool command to power cycle the server
        command = f"ipmitool -I lanplus -H {server_ip} -U admin -P password chassis power cycle"
        result = subprocess.check_output(command, shell=True)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return "Command not available"

# Function to update server statuses every 10 minutes
def update_server_statuses():
    while True:
        for ip in servers:
            server_statuses[ip] = get_server_status(ip)
        time.sleep(10)  # 10 minutes = 600 seconds

# Start a background thread to update the server statuses every 10 minutes
status_thread = Thread(target=update_server_statuses)
status_thread.daemon = True
status_thread.start()

# Home route to display the server status table
@app.route('/')
def index():
    return render_template('index.html', server_statuses=server_statuses)

# Route to handle the power cycle action
@app.route('/power_cycle/<ip>')
def power_cycle(ip):
    power_cycle_server(ip)  # Power cycle the selected server
    return redirect(url_for('index'))  # Redirect back to the homepage after the action

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

