#!/bin/bash
set -e

apt-get update -y
apt-get install -y python3-pip
python3 -m pip install -r /app/requirements.txt

bash /app/start-services.sh
bash /app/prepare_data.sh
bash /app/index.sh
tail -f /dev/null