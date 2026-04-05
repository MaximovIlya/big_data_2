#!/bin/bash
set -e

QUERY="$*"

if [ -z "$QUERY" ]; then
  echo "Usage: bash /app/search.sh \"your query here\""
  exit 1
fi

python3 /app/query.py "$QUERY"