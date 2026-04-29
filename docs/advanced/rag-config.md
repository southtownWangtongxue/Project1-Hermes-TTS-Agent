# RAG 知识库配置

DataAgent Pro 集成 Milvus 向量数据库作为 RAG（检索增强生成）知识库，用于存储和检索业务规范、指标定义、SQL 模板等知识文档，提升 Text-to-SQL 的准确率。

---

## 架构概述

```
┌──────────┐   上传文档    ┌─────────────┐   切片+Embedding   ┌─────────┐
│  管理员   │ ────────────→│  FastAPI     │ ────────────────→ │ Milvus  │
│  (前端)   │              │  /rag/upload │                   │ (向量库) │
└──────────┘              └─────────────┘                   └────┬────┘
                                                                 │
                                                          检索相似文档
                                                                 │
┌──────────┐   用户提问    ┌─────────────┐   拼接上下文      ┌────▼────┐
│  用户     │ ────────────→│  RAG Agent   │ ────────────────→│ LLM     │
│  (前端)   │              │  (后端)      │                   │ (生成)  │
└──────────┘              └─────────────┘                   └─────────┘
```

---

## Milvus 连接配置

在 `.env` 文件中配置 Milvus 连接参数：

```ini
# Milvus 向量数据库
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=dataagent_knowledge

# Embedding 模型配置
EMBEDDING_MODEL_NAME=text2vec-large-chinese
EMBEDDING_DIM=1024
```

### Docker Compose 启动 Milvus

```yaml
# docker-compose.yml 中的 Milvus 配置
services:
  milvus-standalone:
    image: milvusdb/milvus:v2.4.0
    container_name: milvus-standalone
    ports:
      - "19530:19530"
      - "9091:9091"
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    depends_on:
      - etcd
      - minio
```

---

## 文档上传流程

### API 接口

**URL**：`POST /api/v1/rag/upload`

**Content-Type**：`multipart/form-data`

```bash
curl -X POST http://localhost:8000/api/v1/rag/upload \
  -F "file=@sales_metrics.md" \
  -F "category=business_metrics" \
  -F "description=销售指标定义文档"
```

### 处理流程

```
1. 接收上传文件（支持 .txt, .md, .pdf, .csv）
       │
       ▼
2. 解析文档内容，按段落/章节切分
       │
       ▼
3. 调用 Embedding 模型生成向量（text2vec-large-chinese）
       │
       ▼
4. 向量 + 元数据写入 Milvus Collection
       │
       ▼
5. 返回上传结果（切片数量、处理耗时）
```

### 文档类型建议

| 文档类型 | 说明 | 建议格式 |
|---------|------|---------|
| 指标定义 | 业务指标的口径和计算公式 | Markdown |
| SQL 模板 | 典型查询的 SQL 模板和说明 | Markdown |
| 业务规范 | 行业术语、数据字典 | CSV / Markdown |
| 表关系说明 | 多表关联的业务语义 | Markdown |

---

## 检索参数配置

在 `backend/app/rag/retriever.py` 中可调整检索参数：

```python
# 检索配置（可调整参数）
RETRIEVER_CONFIG = {
    "top_k": 5,                # 返回最相似的 5 个文档片段
    "similarity_threshold": 0.7,  # 相似度阈值（低于此值的结果丢弃）
    "search_params": {
        "metric_type": "IP",   # 内积相似度（也可用 L2 或 COSINE）
        "params": {"nprobe": 16}  # 搜索精度（越大越准但越慢）
    }
}
```

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `top_k` | 5 | 每次检索返回的文档片段数量 |
| `similarity_threshold` | 0.7 | 相似度低于此值的片段将被过滤 |
| `metric_type` | IP | 相似度度量方式（IP=内积, L2=欧氏距离, COSINE=余弦） |
| `nprobe` | 16 | 聚类搜索精度，值越大越准但延迟越高 |

---

## 索引类型选择

根据数据规模选择合适的 Milvus 索引：

| 索引类型 | 适用场景 | 特点 |
|---------|---------|------|
| **IVF_FLAT** | 文档量 < 100万 | 精度最高，速度适中 |
| **IVF_SQ8** | 文档量 100万-1000万 | 压缩存储，精度略降 |
| **HNSW** | 文档量任意 | 查询最快，内存占用大 |

在 Milvus 中创建索引：

```python
from pymilvus import Collection, Index

collection = Collection("dataagent_knowledge")
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "IP",
    "params": {"nlist": 1024}
}
collection.create_index("embedding", index_params)
```

---

## 验证 RAG 是否正常工作

```bash
# 通过 API 上传测试文档
curl -X POST http://localhost:8000/api/v1/rag/upload \
  -F "file=@test_knowledge.md" \
  -F "category=test"

# 发起一个对话，观察是否引用了知识库内容
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"query": "根据知识库的规范，销售额的计算口径是什么？"}'
```

如果 RAG 正常工作，在 SSE 事件流中会看到 `stage: "rag_retrieving"` 的状态更新，且生成的 SQL 会体现知识库中的业务规范。

---

## 常见问题

### Milvus 连接失败

检查 Docker 容器状态：

```bash
docker-compose ps milvus-standalone
```

如果容器未启动：

```bash
docker-compose up -d milvus-standalone
```

### 检索结果不相关

1. 检查文档切分粒度是否合适（建议每段 200-500 字）
2. 调整 `similarity_threshold` 阈值
3. 评估 Embedding 模型是否适配中文场景
