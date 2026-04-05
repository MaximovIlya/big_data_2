#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$APP_DIR/data"
PREPARED_INPUT_DIR="$APP_DIR/prepared_input"

echo "Running prepare_data.py..."
python3 "$APP_DIR/prepare_data.py"

echo "Creating HDFS directories..."
hdfs dfs -mkdir -p /data
hdfs dfs -mkdir -p /input/data

echo "Cleaning old HDFS data..."
hdfs dfs -rm -r -f /data/* || true
hdfs dfs -rm -r -f /input/data/* || true

echo "Uploading text documents to HDFS /data ..."
hdfs dfs -put "$DATA_DIR"/*.txt /data/

echo "Uploading prepared input to HDFS /input/data ..."
hdfs dfs -put "$PREPARED_INPUT_DIR"/part-00000 /input/data/

echo "Checking HDFS folders..."
hdfs dfs -ls /data | head -20
hdfs dfs -ls /input/data

echo "Data preparation finished successfully."