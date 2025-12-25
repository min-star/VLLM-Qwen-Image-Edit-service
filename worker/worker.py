import redis
import json
import uuid
import time
import asyncio
import httpx
import base64
from PIL import Image
from io import BytesIO

REDIS_URL = "redis://127.0.0.1:6380/0"
VLLM_URL = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "Qwen-Image-Edit-2509"
OUT_DIR = "outputs"

rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def pil_to_b64(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

async def run():
    async with httpx.AsyncClient(timeout=300) as client:
        while True:
            _, raw = rds.blpop("task:queue")
            task = json.loads(raw)
            task_id = task["task_id"]

            rds.hset(f"task:{task_id}", "status", "RUNNING")

            payload = {
                "model": MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": task["prompt"]},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{task['image']}"
                            }
                        }
                    ]
                }]
            }

            try:
                resp = await client.post(VLLM_URL, json=payload)
                msg = resp.json()["choices"][0]["message"]

                for c in msg["content"]:
                    if c["type"] == "image_url":
                        data = c["image_url"]["url"].split(",")[1]
                        img = Image.open(BytesIO(base64.b64decode(data)))
                        path = f"{OUT_DIR}/{task_id}.png"
                        img.save(path)

                        rds.hset(f"task:{task_id}", mapping={
                            "status": "DONE",
                            "result": path
                        })
            except Exception as e:
                rds.hset(f"task:{task_id}", mapping={
                    "status": "ERROR",
                    "error": str(e)
                })

asyncio.run(run())
