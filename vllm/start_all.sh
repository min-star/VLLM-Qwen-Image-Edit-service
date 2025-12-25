#!/usr/bin/env bash

MODEL_PATH="/home/maintain/.cache/modelscope/hub/models/Qwen/Qwen-Image-Edit-2509"
BASE_PORT=8090

for GPU in 0 1 2 3
do
  PORT=$((BASE_PORT + GPU))

  CUDA_VISIBLE_DEVICES=$GPU \
  vllm serve $MODEL_PATH \
    --omni \
    --port $PORT \
    --cache-backend cache_dit &

  echo "🚀 GPU $GPU -> http://127.0.0.1:$PORT"
done

wait
