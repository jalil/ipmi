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


# Flask Server Management Dashboard

This project is a Flask web application that manages and monitors servers, with functionality to check the BMC status using `ipmitool`, check the status of Kubernetes kubelets using `paramiko`, and power cycle servers. The app also stores the power cycle reason and the username in a PostgreSQL database.

## Features

- **BMC Status Check**: Uses `ipmitool` to check the BMC (Baseboard Management Controller) status for servers.
- **Kubelet Status Check**: Uses `paramiko` to SSH into Kubernetes nodes and check the status of the kubelet service.
- **Power Cycle**: Allows the user to power cycle a server with a reason, which is stored in a PostgreSQL database.
- **Authentication**: Basic authentication (`admin:admin`) is required to access the dashboard.
- **Threaded Execution**: Concurrent checks of BMC and Kubernetes status using Python's `ThreadPoolExecutor`.

## Requirements

- Python 3.7+
- Flask
- Paramiko
- Psycopg2 (PostgreSQL client library)
- PostgreSQL
- ipmitool

## Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/flask-server-management.git
    cd flask-server-management
    ```

2. **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set Up PostgreSQL**:
    - Create a PostgreSQL database and user:
        ```sql
        CREATE DATABASE flask_app_db;
        CREATE USER flask_user WITH PASSWORD 'yourpassword';
        GRANT ALL PRIVILEGES ON DATABASE flask_app_db TO flask_user;
        ```
    - Update the `app.py` to include your PostgreSQL connection URI:
        ```python
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://flask_user:yourpassword@localhost/flask_app_db'
        ```

5. **Initialize the Database**:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

6. **Run the Application**:
    ```bash
    flask run
    ```

7. **Access the Web App**:
    - Open your browser and go to `http://127.0.0.1:5000`
    - Use the default credentials to log in:
        - Username: `admin`
        - Password: `admin`

## Project Structure


