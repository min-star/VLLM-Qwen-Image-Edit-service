#!/bin/bash

NUM_WORKERS=3

for ((i=1; i<=NUM_WORKERS; i++)); do
  echo "Starting worker $i"
  python worker/worker.py &
done

wait
