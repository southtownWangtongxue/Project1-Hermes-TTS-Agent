# 前端二次开发指南

本文档面向需要二次开发 DataAgent Pro 前端的功能开发者，涵盖项目结构、组件开发、SSE 集成等核心内容。

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.x | 前端框架（Composition API） |
| Vite | 5.x | 构建工具 |
| Element Plus | 2.x | UI 组件库 |
| ECharts | 5.x | 数据可视化 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由管理 |
| TypeScript | 5.x | 类型系统 |

---

## 目录结构

```
frontend/
├── src/
│   ├── api/                    # API 调用封装
│   │   ├── chat.ts             # 对话接口 (SSE 流式)
│   │   ├── approve.ts          # 审批接口
│   │   ├── datasource.ts       # 数据源接口
│   │   └── export.ts           # 文件导出接口
│   ├── components/             # 通用组件
│   │   ├── ChatBox.vue         # 聊天输入/输出组件
│   │   ├── ChatMessage.vue     # 单条消息组件
│   │   ├── ChartRenderer.vue   # ECharts 图表渲染组件
│   │   ├── DataTable.vue       # 数据表格组件
│   │   ├── SqlDisplay.vue      # SQL 展示组件
│   │   └── ApprovalPanel.vue   # 审批管理组件
│   ├── composables/            # 组合式函数
│   │   ├── useSSE.ts           # SSE 事件流处理
│   │   ├── useChat.ts          # 对话逻辑封装
│   │   └── useAuth.ts          # 鉴权逻辑（预留）
│   ├── views/                  # 页面视图
│   │   ├── HomeView.vue        # 首页（对话）
│   │   ├── AdminView.vue       # 审批管理页
│   │   └── HistoryView.vue     # 对话历史页
│   ├── stores/                 # Pinia 状态管理
│   │   ├── chat.ts             # 对话状态
│   │   ├── approval.ts         # 审批状态
│   │   └── user.ts             # 用户状态
│   ├── router/                 # Vue Router 路由配置
│   │   └── index.ts
│   ├── types/                  # TypeScript 类型定义
│   │   └── index.ts
│   ├── App.vue                 # 根组件
│   └── main.ts                 # 应用入口
├── public/                     # 静态资源
├── index.html                  # HTML 入口
├── package.json
├── tsconfig.json
└── vite.config.ts              # Vite 配置
```

---

## 组件开发

### ChatBox 组件

`ChatBox` 是核心对话组件，负责接收用户输入、展示对话流。

```vue
<!-- src/components/ChatBox.vue — 结构示意 -->
<template>
  <div class="chat-box">
    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <ChatMessage
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入你的问题，例如：上个月销售额最高的10个产品"
        @keydown.enter.exact="handleSend"
      />
      <el-button type="primary" @click="handleSend" :loading="isStreaming">
        发送
      </el-button>
    </div>
  </div>
</template>
```

### ChartRenderer 组件

接收 ECharts JSON 配置并渲染图表：

```vue
<!-- src/components/ChartRenderer.vue -->
<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  option: object  // ECharts 配置对象
}>()

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption(props.option)
  }
})

watch(() => props.option, (newOption) => {
  chartInstance?.setOption(newOption, true)  // true = 不合并，完全替换
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>
```

---

## SSE 集成

### useSSE 组合式函数

核心 SSE 事件处理逻辑：

```typescript
// src/composables/useSSE.ts

export interface SSEEvent {
  event: string
  data: any
}

export function useSSE() {
  const isConnected = ref(false)
  const eventHandlers = new Map<string, Set<Function>>()

  function on(eventType: string, handler: Function) {
    if (!eventHandlers.has(eventType)) {
      eventHandlers.set(eventType, new Set())
    }
    eventHandlers.get(eventType)!.add(handler)
  }

  function off(eventType: string, handler: Function) {
    eventHandlers.get(eventType)?.delete(handler)
  }

  async function connect(url: string, body: object) {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(body),
    })

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    isConnected.value = true

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEvent = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          // 触发对应事件处理器
          eventHandlers.get(currentEvent)?.forEach(handler => handler(data))
          eventHandlers.get('*')?.forEach(handler => handler({ event: currentEvent, data }))
        }
      }
    }

    isConnected.value = false
  }

  function disconnect() {
    // 可通过 AbortController 中断 fetch
  }

  return { isConnected, on, off, connect, disconnect }
}
```

### 在 Chat Store 中使用

```typescript
// src/stores/chat.ts

import { defineStore } from 'pinia'
import { useSSE } from '@/composables/useSSE'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const currentSQL = ref('')
  const currentChart = ref(null)
  const { on, connect } = useSSE()

  async function sendMessage(query: string) {
    // 添加用户消息
    messages.value.push({ role: 'user', content: query })

    // 添加助手消息占位
    const assistantMsg: Message = { role: 'assistant', content: '', status: 'streaming' }
    messages.value.push(assistantMsg)

    // 注册事件处理器
    on('status', (data) => {
      assistantMsg.status = data.stage
    })
    on('sql_generation', (data) => {
      currentSQL.value = data.sql
    })
    on('result_data', (data) => {
      assistantMsg.tableData = data
    })
    on('insights', (data) => {
      assistantMsg.content += data.text
    })
    on('chart', (data) => {
      currentChart.value = data.echartsConfig
    })
    on('done', () => {
      assistantMsg.status = 'done'
    })

    // 发起 SSE 连接
    await connect('/api/v1/chat/completions', { query })
  }

  return { messages, currentSQL, currentChart, sendMessage }
})
```

---

## 审批管理页面

```vue
<!-- src/views/AdminView.vue — 示意 -->
<template>
  <div class="admin-page">
    <h2>审批管理</h2>

    <el-table :data="pendingTasks" stripe>
      <el-table-column prop="task_id" label="任务 ID" />
      <el-table-column prop="user" label="申请人" />
      <el-table-column prop="sql" label="SQL 语句">
        <template #default="{ row }">
          <code>{{ row.sql }}</code>
        </template>
      </el-table-column>
      <el-table-column prop="risk_level" label="风险等级">
        <template #default="{ row }">
          <el-tag :type="riskTagType(row.risk_level)">
            {{ row.risk_level }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button type="success" @click="handleApprove(row.task_id)">通过</el-button>
          <el-button type="danger" @click="handleReject(row.task_id)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { approveTask, rejectTask, fetchPendingTasks } from '@/api/approve'

const pendingTasks = ref([])

onMounted(async () => {
  pendingTasks.value = await fetchPendingTasks()
})

async function handleApprove(taskId: string) {
  await approveTask(taskId)
  pendingTasks.value = pendingTasks.value.filter(t => t.task_id !== taskId)
}

async function handleReject(taskId: string) {
  await rejectTask(taskId)
  pendingTasks.value = pendingTasks.value.filter(t => t.task_id !== taskId)
}
</script>
```

---

## Vite 配置

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## 开发建议

1. **TypeScript 严格模式**：所有新增组件建议使用 TypeScript，开启 `strict: true`
2. **组件粒度**：功能组件保持单一职责，可复用的 UI 片段抽离为独立组件
3. **SSE 错误处理**：监听 `error` 事件，向用户展示友好的错误提示
4. **ECharts 按需引入**：避免全量引入 ECharts，按图表类型按需加载以减小包体积
5. **响应式设计**：页面布局应考虑不同屏幕尺寸的适配
