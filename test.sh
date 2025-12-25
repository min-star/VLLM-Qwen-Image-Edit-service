for i in {1..4}; do
  curl -X POST http://127.0.0.1:8000/submit \
    -F "image=@/mnt1/msf/vllm-omni-main/examples/offline_inference/image_to_image/qwen-bear.png" \
    -F "prompt=将熊随即变成一只动物 $i" &
done
