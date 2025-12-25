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