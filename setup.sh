#!/bin/bash

# Exit on error
set -e

# Variables
UPLOAD_DIR="/var/www/files"
APP_FILE="main.py"
PORT=3690

# Step 1: Check for sudo/root permissions
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root. Use sudo or switch to the root user."
   exit 1
fi

# Step 2: Update and install the latest Python and pip
echo "Updating system and installing the latest Python and pip..."
apt update
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3 python3-pip

# Step 3: Check if /var/www/files exists, create if not
if [ ! -d "$UPLOAD_DIR" ]; then
    echo "Creating $UPLOAD_DIR directory..."
    mkdir -p "$UPLOAD_DIR"
    chown $USER:www-data "$UPLOAD_DIR"
    chmod 775 "$UPLOAD_DIR"
else
    echo "Directory $UPLOAD_DIR already exists."
fi

# Step 4: Install Python requirements
echo "Installing Python requirements from requirements.txt..."
pip3 install -r requirements.txt

# Step 5: Start the Flask application
echo "Starting the Flask application..."
python3 $APP_FILE &

# Get the server's IP address
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "File CDN is running!"
echo "Access it at http://$SERVER_IP:$PORT/"
