#!/bin/bash
set -e

apt-get update
apt-get install -y python3-pip
python3 -m pip install -r /app/requirements.txt

bash /app/start-services.sh

tail -f /dev/null