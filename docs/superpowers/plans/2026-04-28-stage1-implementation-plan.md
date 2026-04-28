# 阶段1: 基础架构与 Agent 核心

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建项目骨架，实现 LangGraph Agent 框架，包含后端 FastAPI、前端 Vue 3、数据库连接层和基础配置管理

**Architecture:**
- 后端：FastAPI 应用 + LangGraph 状态图框架
- 前端：Vue 3 单页应用 + Vite 构建 + Element Plus UI 组件库
- 数据库：SQLAlchemy + MySQL 驱动
- 部署：Docker Compose 定义后端、前端容器

**Tech Stack:**
- Python 3.11+, FastAPI, LangGraph, SQLAlchemy, Pydantic, Docker
- Vue 3, Vite, Element Plus, Axios, Pinia

---

## 阶段1实现计划

### Task 1: 后端项目初始化

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`
- Create: `backend/.env.example`
- Create: `backend/config/__init__.py`
- Create: `backend/config/settings.py`
- Create: `backend/utils/__init__.py`
- Create: `backend/utils/logger.py`
- Create: `backend/main.py`
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`

**依赖项:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
pymysql==1.1.0
aiomysql==0.2.0
langgraph==0.0.23
langchain==0.1.0
langchain-openai==0.0.2
python-dotenv==1.0.0
python-multipart==0.0.6
```

**步骤:**

- [ ] **Step 1: 创建 requirements.txt**

Create file: `backend/requirements.txt` with the dependencies listed above

- [ ] **Step 2: 创建 .env.example**

Create file: `backend/.env.example`
```env
# Database
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=hermes

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM (for Phase 2)
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

- [ ] **Step 3: 创建 utils/logger.py**

Create file: `backend/utils/logger.py`
```python
import logging
import sys
from pathlib import Path

def setup_logger(name: str = "hermes", level: int = logging.INFO) -> logging.Logger:
    """配置日志系统"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # 控制台 handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_format)

        # 文件 handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setLevel(level)
        file_handler.setFormatter(console_format)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
```

- [ ] **Step 4: 创建 config/settings.py**

Create file: `backend/config/settings.py`
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "mysql"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "hermes"

    # FastAPI
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530

    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

- [ ] **Step 5: 创建 backend/__init__.py**

Create file: `backend/__init__.py`

- [ ] **Step 6: 创建 config/__init__.py**

Create file: `backend/config/__init__.py`

- [ ] **Step 7: 创建 utils/__init__.py**

Create file: `backend/utils/__init__.py`

- [ ] **Step 8: 创建 main.py**

Create file: `backend/main.py`
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import settings
from .utils import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Hermes TTS Agent backend...")
    yield
    logger.info("Shutting down Hermes TTS Agent backend...")

app = FastAPI(
    title="Hermes Text-to-SQL Agent",
    description="Natural language to SQL conversion assistant",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "name": "Hermes Text-to-SQL Agent",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=True
    )
```

- [ ] **Step 9: 创建 Dockerfile**

Create file: `backend/Dockerfile`
```python
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 10: 创建 docker-compose.yml**

Create file: `docker-compose.yml`
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: hermes-mysql
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: hermes
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: hermes-backend
    ports:
      - "8000:8000"
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: root
      DB_PASSWORD: root
      DB_NAME: hermes
    depends_on:
      mysql:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./logs:/app/logs

volumes:
  mysql_data:
```

- [ ] **Step 11: 初始化 git**

```bash
git init
git add .
git commit -m "feat(backend): initialize backend project structure"
```

---

### Task 2: 前端项目初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/api/chat.ts`
- Create: `frontend/src/stores/chat.ts`
- Create: `frontend/src/components/HelloWorld.vue`
- Create: `frontend/Dockerfile`
- Create: `frontend/.env.example`

**步骤:**

- [ ] **Step 1: 创建 package.json**

Create file: `frontend/package.json`
```json
{
  "name": "hermes-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.3.4",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.0",
    "element-plus": "^2.4.2",
    "@element-plus/icons-vue": "^2.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.4.0",
    "typescript": "^5.2.2",
    "vite": "^4.5.0",
    "vue-tsc": "^1.8.5"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

Create file: `frontend/vite.config.ts`
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建 tsconfig.json**

Create file: `frontend/tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: 创建 tsconfig.node.json**

Create file: `frontend/tsconfig.node.json`
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 5: 创建 index.html**

Create file: `frontend/index.html`
```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Hermes - Text-to-SQL Agent</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 6: 创建 src/main.ts**

Create file: `frontend/src/main.ts`
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from './router'
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)

app.mount('#app')
```

- [ ] **Step 7: 创建 src/App.vue**

Create file: `frontend/src/App.vue`
```vue
<script setup lang="ts">
import { RouterView } from 'vue-router'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// 配置 Element Plus 中文语言
const locale = zhCn
</script>

<template>
  <ElConfigProvider :locale="locale">
    <RouterView />
  </ElConfigProvider>
</template>

<style>
#app {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
```

- [ ] **Step 8: 创建 src/router/index.ts**

Create file: `frontend/src/router/index.ts`
```typescript
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    }
  ]
})

export default router
```

- [ ] **Step 9: 创建 src/views/HomeView.vue**

Create file: `frontend/src/views/HomeView.vue`
```vue
<template>
  <div class="home">
    <el-container>
      <el-header>
        <h1>Hermes - Text-to-SQL Agent</h1>
      </el-header>
      <el-main>
        <el-card>
          <p>阶段 1: 基础架构与 Agent 核心</p>
          <p>后端 FastAPI + 前端 Vue 3 + 数据库连接层</p>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
}
</style>
```

- [ ] **Step 10: 创建 src/api/chat.ts**

Create file: `frontend/src/api/chat.ts`
```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

export interface ChatRequest {
  session_id: string
  message: string
  user_id: string
}

export interface ChatResponse {
  reply: string
  sql?: string
  data?: any
  chart?: any
  references?: string[]
}

export const chatApi = {
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post('/chat', request)
    return response.data
  }
}
```

- [ ] **Step 11: 创建 src/stores/chat.ts**

Create file: `frontend/src/stores/chat.ts`
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi, type ChatRequest, type ChatResponse } from '../api/chat'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Array<{ role: 'user' | 'assistant'; content: string }>>([])
  const isLoading = ref(false)

  async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
    isLoading.value = true
    try {
      const response = await chatApi.chat(request)

      // 添加用户消息
      messages.value.push({
        role: 'user',
        content: request.message
      })

      // 添加助手消息
      messages.value.push({
        role: 'assistant',
        content: response.reply
      })

      return response
    } finally {
      isLoading.value = false
    }
  }

  return {
    messages,
    isLoading,
    sendMessage
  }
})
```

- [ ] **Step 12: 创建 src/components/HelloWorld.vue**

Create file: `frontend/src/components/HelloWorld.vue`
```vue
<template>
  <h1>Hello World</h1>
  <p>阶段 1 前端项目初始化完成</p>
</template>
```

- [ ] **Step 13: 创建 src/api/index.ts**

Create file: `frontend/src/api/index.ts`
```typescript
export * from './chat'
```

- [ ] **Step 14: 创建 frontend/src/stores/index.ts**

Create file: `frontend/src/stores/index.ts`
```typescript
export * from './chat'
```

- [ ] **Step 15: 创建 frontend/Dockerfile**

Create file: `frontend/Dockerfile`
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 16: 创建 frontend/nginx.conf**

Create file: `frontend/nginx.conf`
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 17: 创建 frontend/.env.example**

Create file: `frontend/.env.example`
```env
VITE_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 18: 更新 docker-compose.yml 添加前端服务**

Edit file: `docker-compose.yml`
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: hermes-mysql
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: hermes
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: hermes-backend
    ports:
      - "8000:8000"
    environment:
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: root
      DB_PASSWORD: root
      DB_NAME: hermes
    depends_on:
      mysql:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./logs:/app/logs

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: hermes-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro

volumes:
  mysql_data:
```

- [ ] **Step 19: 创建 frontend/.gitignore**

Create file: `frontend/.gitignore`
```
dist
.DS_Store
*.log
node_modules
.env.local
```

- [ ] **Step 20: 初始化 git**

```bash
git init
git add .
git commit -m "feat(frontend): initialize frontend project structure"
```

---

### Task 3: 数据库连接层实现

**Files:**
- Create: `backend/models/__init__.py`
- Create: `backend/models/database.py`
- Create: `backend/models/schemas.py`
- Create: `scripts/init_db.sql`

**步骤:**

- [ ] **Step 1: 创建 models/__init__.py**

Create file: `backend/models/__init__.py`
```python
from .database import engine, SessionLocal
from .schemas import SessionCreate, UserCreate, ApprovalRequestCreate, ApprovalStatus

__all__ = ['engine', 'SessionLocal', 'SessionCreate', 'UserCreate', 'ApprovalRequestCreate', 'ApprovalStatus']
```

- [ ] **Step 2: 创建 models/database.py**

Create file: `backend/models/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# 创建数据库引擎
engine = create_engine(
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 创建数据库表
def init_db():
    """初始化所有数据库表"""
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 3: 创建 models/schemas.py**

Create file: `backend/models/schemas.py`
```python
from typing import Optional
from pydantic import BaseModel, Field

# Session 相关
class SessionBase(BaseModel):
    session_id: str
    user_id: str
    messages: Optional[list] = []

class SessionCreate(SessionBase):
    pass

class Session(SessionBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True

# User 相关
class UserBase(BaseModel):
    username: str
    full_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True

# Approval Request 相关
class ApprovalRequestBase(BaseModel):
    sql: str
    operation_type: str
    target_table: str
    estimated_rows: int
    risk_level: str
    created_by: str
    status: str = 'pending'

class ApprovalRequestCreate(ApprovalRequestBase):
    pass

class ApprovalRequest(ApprovalRequestBase):
    id: int
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

class ApprovalStatus(str):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
```

- [ ] **Step 4: 创建 scripts/init_db.sql**

Create file: `scripts/init_db.sql`
```sql
-- 创建会话表
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    messages TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建审批请求表
CREATE TABLE IF NOT EXISTS approval_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sql TEXT NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    target_table VARCHAR(255) NOT NULL,
    estimated_rows INT DEFAULT 0,
    risk_level VARCHAR(50) NOT NULL,
    created_by VARCHAR(255) NOT NULL,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP NULL,
    rejection_reason TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员用户
INSERT INTO users (username, full_name) VALUES
('admin', 'System Admin')
ON DUPLICATE KEY UPDATE full_name='System Admin';
```

- [ ] **Step 5: 更新 backend/main.py 添加数据库初始化**

Edit file: `backend/main.py`
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import settings
from .utils import logger
from .models.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Hermes TTS Agent backend...")
    init_db()
    yield
    logger.info("Shutting down Hermes TTS Agent backend...")

app = FastAPI(
    title="Hermes Text-to-SQL Agent",
    description="Natural language to SQL conversion assistant",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "name": "Hermes Text-to-SQL Agent",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/sessions")
async def list_sessions():
    from .models.database import SessionLocal, SessionCreate
    from .models.schemas import Session
    from datetime import datetime

    db = SessionLocal()
    try:
        sessions = []
        # 这里应该从数据库查询会话列表
        # 目前返回空列表
        return {"sessions": sessions}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=True
    )
```

- [ ] **Step 6: 初始化 git**

```bash
git init
git add .
git commit -m "feat(backend): implement database connection layer"
```

---

### Task 4: LangGraph Agent 状态定义

**Files:**
- Create: `backend/agents/state.py`

**步骤:**

- [ ] **Step 1: 创建 agents/__init__.py**

Create file: `backend/agents/__init__.py`

- [ ] **Step 2: 创建 agents/state.py**

Create file: `backend/agents/state.py`
```python
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Agent 状态定义"""
    # 用户输入
    user_query: str
    session_id: str
    user_id: str

    # 意图分类结果
    intent: Literal["query", "approval", "general"]
    is_sensitive_operation: bool = False

    # RAG 检索结果
    rag_context: str = ""

    # SQL 生成结果
    sql: str = ""
    sql_confidence: float = 0.0

    # SQL 验证结果
    is_valid: bool = True
    validation_error: str = ""

    # 审批结果
    approval_status: Literal["pending", "approved", "rejected"] = "pending"
    approval_request_id: str = ""

    # 数据库查询结果
    query_result: list = []
    query_columns: list = []

    # 分析结果
    summary: str = ""
    chart_type: str = ""

    # 历史对话
    messages: Annotated[list, add_messages]
```

- [ ] **Step 3: 初始化 git**

```bash
git init
git add .
git commit -m "feat(agents): define LangGraph agent state"
```

---

### Task 5: 意图路由节点

**Files:**
- Create: `backend/agents/router.py`
- Modify: `backend/main.py`

**步骤:**

- [ ] **Step 1: 创建 router.py**

Create file: `backend/agents/router.py`
```python
from typing import Literal
from .state import AgentState

def route_intent(state: AgentState) -> Literal["query", "approval"]:
    """意图路由：区分查询操作和审批操作"""

    # 检查是否为敏感操作
    sensitive_operations = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]

    for op in sensitive_operations:
        if op in state.sql.upper():
            state.is_sensitive_operation = True
            return "approval"

    return "query"

def route_sensitive_operation(state: AgentState) -> Literal["approver", "query"]:
    """敏感操作路由"""

    if state.is_sensitive_operation:
        return "approver"
    return "query"
```

- [ ] **Step 2: 更新 main.py 添加路由节点定义**

Edit file: `backend/main.py`
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import settings
from .utils import logger
from .models.database import init_db
from .agents.state import AgentState
from .agents.router import route_intent, route_sensitive_operation

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Hermes TTS Agent backend...")
    init_db()
    yield
    logger.info("Shutting down Hermes TTS Agent backend...")

app = FastAPI(
    title="Hermes Text-to-SQL Agent",
    description="Natural language to SQL conversion assistant",
    version="0.1.0",
    lifespan=lifespan
)

# 定义 LangGraph 图结构（阶段1先定义，具体节点稍后实现）
# from langgraph.graph import StateGraph
# workflow = StateGraph(AgentState)
# workflow.add_node("router", route_intent)
# workflow.add_node("query_processor", query_processor_node)
# workflow.add_node("approver", approver_node)
# workflow.set_entry_point("router")
# workflow.add_conditional_edges("router", route_sensitive_operation, {
#     "approver": "approver",
#     "query": "query_processor"
# })
# workflow.add_edge("query_processor", "approver")
# workflow.add_edge("approver", "query_processor")
# app_state = workflow.compile()

@app.get("/")
async def root():
    return {
        "name": "Hermes Text-to-SQL Agent",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/sessions")
async def list_sessions():
    from .models.database import SessionLocal, SessionCreate
    from .models.schemas import Session
    from datetime import datetime

    db = SessionLocal()
    try:
        sessions = []
        # 这里应该从数据库查询会话列表
        # 目前返回空列表
        return {"sessions": sessions}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=True
    )
```

- [ ] **Step 3: 初始化 git**

```bash
git init
git add .
git commit -m "feat(agents): implement intent routing node"
```

---

### Task 6: 阶段1完成验证

**步骤:**

- [ ] **Step 1: 测试后端启动**

```bash
cd backend
python main.py
```

预期输出：
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Hermes TTS Agent backend...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

验证：
- 访问 http://localhost:8000 返回项目信息
- 访问 http://localhost:8000/health 返回健康状态

- [ ] **Step 2: 测试 Docker Compose 启动**

```bash
docker-compose up -d
```

验证：
```bash
docker-compose ps
```

预期输出包含三个容器：hermes-mysql, hermes-backend, hermes-frontend

- [ ] **Step 3: 测试前端访问**

访问 http://localhost 返回 Hermes 前端页面

- [ ] **Step 4: 验证数据库初始化**

```bash
docker exec -it hermes-mysql mysql -uroot -proot -e "USE hermes; SHOW TABLES;"
```

预期输出包含 sessions, users, approval_requests 表

- [ ] **Step 5: 阶段1完成验证**

运行所有任务并验证功能：
```bash
git log --oneline -10
```

预期包含所有阶段1的任务提交

---

## 完成标准

- [ ] 后端项目成功启动，FastAPI 运行在 8000 端口
- [ ] 前端项目成功构建，访问 http://localhost 显示首页
- [ ] Docker Compose 成功启动所有服务
- [ ] 数据库表成功创建（sessions, users, approval_requests）
- [ ] LangGraph Agent 状态定义完成
- [ ] 意图路由节点实现完成

---

## 注意事项

1. **环境要求**：确保已安装 Docker 和 Docker Compose
2. **端口冲突**：确保 3306、8000、80 端口未被占用
3. **数据持久化**：MySQL 数据存储在 Docker volume 中
4. **开发模式**：backend 使用 `--reload` 模式，代码修改自动生效
5. **代码风格**：遵循 PEP 8 规范，使用类型注解
