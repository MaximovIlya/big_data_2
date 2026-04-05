#!/bin/bash
set -e

echo "Installing Python dependencies..."
apt-get update
apt-get install -y python3-pip
python3 -m pip install -r /app/requirements.txt

echo "Waiting for Cassandra container..."
sleep 15

echo "Storing index from HDFS into Cassandra..."
python3 /app/app.py

echo "Done."