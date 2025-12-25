from fastapi import FastAPI, UploadFile, File, Form
import redis, uuid, json, time
from PIL import Image
from io import BytesIO
import base64

app = FastAPI()
rds = redis.Redis.from_url("redis://127.0.0.1:6380/0", decode_responses=True)

def img_to_b64(file):
    img = Image.open(BytesIO(file)).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

@app.post("/submit")
async def submit(image: UploadFile = File(...), prompt: str = Form(...)):
    task_id = str(uuid.uuid4())
    img_b64 = img_to_b64(await image.read())

    task = {
        "task_id": task_id,
        "image": img_b64,
        "prompt": prompt,
    }

    rds.hset(f"task:{task_id}", mapping={
        "status": "PENDING",
        "created": time.time()
    })
    rds.rpush("task:queue", json.dumps(task))

    return {"task_id": task_id}

@app.get("/task/{task_id}")
def query(task_id: str):
    return rds.hgetall(f"task:{task_id}")
