
from flask import Flask, render_template, redirect, url_for
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize the Flask app
app = Flask(__name__)

# List of server IP addresses (no server names)
servers = [
    "192.168.1.100",
    "192.168.1.101",
    "192.168.1.102"
]

# Store server statuses
server_statuses = {}

# Function to get power status of a server using ipmitool
def get_server_status(server_ip):
    try:
        # Execute the ipmitool command to get the power status of the server
        command = f"ipmitool -I lanplus -H {server_ip} -U admin -P password chassis power status"
        result = subprocess.check_output(command, shell=True)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return "Command failed"
    except FileNotFoundError:
        return "Command not available"

# Function to power cycle (restart) a server using ipmitool
def power_cycle_server(server_ip):
    try:
        # Execute the ipmitool command to power cycle the server
        command = f"ipmitool -I lanplus -H {server_ip} -U admin -P password chassis power cycle"
        result = subprocess.check_output(command, shell=True)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError:
        return "Command failed"
    except FileNotFoundError:
        return "Command not available"

# Function to update server statuses every minute
def update_server_statuses():
    global server_statuses
    for ip in servers:
        status = get_server_status(ip)
        server_statuses[ip] = status

# Home route to display the server status table
@app.route('/')
def index():
    # Render the HTML template with server data
    return render_template('index.html', server_statuses=server_statuses)

# Route to handle the power cycle action
@app.route('/power_cycle/<ip>')
def power_cycle(ip):
    power_cycle_server(ip)  # Power cycle the selected server
    return redirect(url_for('index'))  # Redirect back to the homepage after the action

# Initialize the scheduler to check the status every minute
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=update_server_statuses, trigger="interval", minutes=1)
    scheduler.start()

# Run the Flask app
if __name__ == '__main__':
    update_server_statuses()  # Initial status update before starting the app
    start_scheduler()  # Start the scheduler
    app.run(debug=True)

