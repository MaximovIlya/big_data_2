#!/bin/bash
set -e

INPUT_PATH=${1:-/input/data}
OUTPUT_PATH=/indexer/pipeline1
STREAMING_JAR=/usr/local/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.1.jar

echo "Removing old output if exists..."
hdfs dfs -rm -r -f "$OUTPUT_PATH" || true

echo "Running Hadoop Streaming job..."
hadoop jar "$STREAMING_JAR" \
  -files /app/mapreduce/mapper1.py,/app/mapreduce/reducer1.py \
  -mapper "python3 mapper1.py" \
  -reducer "python3 reducer1.py" \
  -input "$INPUT_PATH" \
  -output "$OUTPUT_PATH"

echo "Index created successfully at $OUTPUT_PATH"
hdfs dfs -ls "$OUTPUT_PATH"
hdfs dfs -cat "$OUTPUT_PATH"/part-* | head -20