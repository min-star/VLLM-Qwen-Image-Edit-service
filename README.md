整体是一个 **「异步任务 + GPU 推理解耦」** 的经典架构。

---

## Client

- 发起 **HTTP 请求**
- 请求内容为推理任务（如 prompt / image / 参数等）

---

## API Server（FastAPI）

- 接收来自 Client 的请求  
- 生成唯一的 `task_id`
- 将任务写入 **Redis 队列**
  - 队列名：`task:queue`
- **立即返回 `task_id`**
  - 请求不阻塞
  - 推理过程完全异步

---

## Redis Queue

- 作为 **任务缓冲 & 解耦组件**
- 职责包括：
  - 缓冲突发请求
  - 解耦 API Server 与 Worker
- Worker 通过 **抢占 / 轮询** 的方式从队列中获取任务

---

## Worker（不绑定 GPU）

- Worker **不直接使用 GPU**
- 只负责任务调度与结果管理：
  - 从 Redis 队列中拉取任务
  - 调用下游推理服务
  - 接收推理结果
  - 将结果写回 Redis / 数据库 / 对象存储
- 设计原则：
  - 不感知 GPU
  - 不关心具体模型实例
  - 可无限横向扩展

---

## Load Balancer（Nginx / Router）

- 接收来自 Worker 的推理请求
- 将请求 **分发到不同的 vLLM 实例**
- 实现：
  - GPU 层负载均衡
  - 多 GPU 并行利用
  - 统一推理入口

---

## vLLM 实例

- 每个 vLLM 实例：
  - 绑定 **1 张 GPU**
  - 独立运行一个模型服务
- 职责：
  - 执行真正的模型推理
  - 将推理结果返回给 Worker
- GPU 资源只存在于该层，与上游完全解耦

# 环境安装

## 1️⃣ 安装VLLM，VLLM omni

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install vllm==0.12.0 --torch-backend=auto
git clone https://github.com/vllm-project/vllm-omni.git
cd vllm-omni
uv pip install -e .
```


# 工程运行流程

## 1️⃣ 启动 Redis

- 启动 Redis 服务
- 安装 Redis
  - sudo apt install -y redis-server
- 启动命令：
  - redis-server --port 6380

## 2️⃣ 启动 vLLM（GPU）

- 启动 GPU 推理服务
- 每张 GPU 启动一个 vLLM 实例
- 启动命令：
  - bash vllm/start_all.sh

## 3️⃣ 启动 Nginx

- 启动推理请求负载均衡
- 作为 Worker 到 vLLM 的统一入口
- 安装 nginx
  - sudo apt install -y nginx
- 启动命令：
  - nginx -c nginx/nginx.conf(配置文件要使用绝对路径)

## 4️⃣ 启动 Worker（可多个）

- Worker 不绑定 GPU
- 可启动多个实例以提升并发能力
- 启动命令：
  - sudo chmod +x worker/start_workers.sh
  - bash start_workers.sh

## 5️⃣ 启动 API Server

- 对外提供 HTTP 接口
- 接收客户端请求并提交异步任务
- 启动命令：
  - uvicorn api.app:app --port 8000

# 测试

- bash test.sh