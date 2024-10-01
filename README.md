Flask Server Management Dashboard
This Flask-based web application provides a dashboard for managing servers using IPMI for BMC status checks and power cycling. It also allows monitoring the status of Kubernetes' kubelet service on each server. The application includes basic authentication, logging of power cycle actions with reasons, and saves this information into an SQLite database.

Features
BMC Status Check: Check the power status of servers via IPMI (on, off, or unknown).
Kubelet Status Check: Check the status of the kubelet service on Kubernetes nodes.
Power Cycle: Perform a power cycle on a server using IPMI, with a reason for the action.
Authentication: Basic authentication (username: admin, password: admin) to restrict access to the dashboard.
Logging: Logs power cycle actions (including the username and reason) to an SQLite database.
Prerequisites
Make sure you have the following installed:

Python 3.7 or higher
Flask
SQLAlchemy
Paramiko (for SSH communication)
ipmitool (for IPMI-based BMC management)
SQLite (or another SQL database)

