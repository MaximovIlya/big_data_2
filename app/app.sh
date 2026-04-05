#!/bin/bash
service ssh restart 


bash start-services.sh

apt-get update && apt-get install -y python3-dev build-essential
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

venv-pack -o .venv.tar.gz --force

bash prepare_data.sh


bash index.sh

bash search.sh "query"

echo "Usage: bash search.sh '<your query>'"

tail -f /dev/null