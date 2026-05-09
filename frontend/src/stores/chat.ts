import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useSSE } from '@/composables/useSSE'
import { useApprovalStore } from '@/stores/approval'

/* 消息类型定义 */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  type?: 'text' | 'sql' | 'result' | 'chart' | 'analysis' | 'status' | 'error'
  content?: string
  sql?: string
  data?: any[]
  columns?: string[]
  chartConfig?: Record<string, unknown>
}

/* 生成唯一消息 ID */
function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 9)
}

/* 聊天状态管理 Store */
export const useChatStore = defineStore('chat', () => {
  /* SSE 连接管理 */
  const { connect: sseConnect, disconnect: sseDisconnect } = useSSE()

  /* 消息列表 */
  const messages = ref<ChatMessage[]>([])

  /* 是否正在加载（等待后端响应） */
  const isLoading = ref(false)

  /* 发送消息：添加用户消息 -> 调用 SSE -> 处理各类事件 -> 添加对应消息 */
  async function sendMessage(text: string) {
    if (!text.trim() || isLoading.value) return

    // 添加用户消息
    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      type: 'text',
      content: text.trim(),
    }
    messages.value.push(userMsg)

    isLoading.value = true

    // 调用 SSE 流式接口
    await sseConnect(
      '/api/v1/chat/completions',
      {
        messages: [{ role: 'user', content: text.trim() }],
        stream: true,
      },
      {
        /* 状态更新：如"正在分析..." */
        onStatus(content: string) {
          messages.value.push({
            id: generateId(),
            role: 'system',
            type: 'status',
            content,
          })
        },

        /* Schema 信息 */
        onSchema(_content: string) {
          // 表结构信息已在 status 消息中体现，此处不再额外展示
        },

        /* 生成的 SQL 语句 */
        onText(content: string) {
          messages.value.push({
            id: generateId(),
            role: 'assistant',
            type: 'text',
            content: content,
          })
        },
        /* 生成的 SQL 语句 */
        onSQL(content: string) {
          messages.value.push({
            id: generateId(),
            role: 'assistant',
            type: 'sql',
            sql: content,
          })
        },

        /* 查询结果数据 */
        onResult(data: any[], columns: string[]) {
          messages.value.push({
            id: generateId(),
            role: 'assistant',
            type: 'result',
            data,
            columns,
          })
        },

        /* 错误信息 */
        onError(error: string) {
          messages.value.push({
            id: generateId(),
            role: 'assistant',
            type: 'error',
            content: error,
          })
          isLoading.value = false
        },

        /* 数据分析洞察 */
        onAnalysis(content: string) {
          messages.value.push({
            id: generateId(),
            role: 'assistant',
            type: 'analysis',
            content,
          })
        },

        /* ECharts 图表配置 */
        onChart(config: Record<string, unknown>) {
          messages.value.push({
            id: generateId(),
            role: 'assistant',
            type: 'chart',
            chartConfig: config,
          })
        },

        /* 高危 SQL 需要审批 */
        onApprovalRequired(threadId: string, question: string, sql: string, reason: string) {
          const approvalStore = useApprovalStore()
          approvalStore.addTask({ threadId, question, sql, reason })
        },

        /* 流结束 */
        onDone() {
          isLoading.value = false
        },
      },
    )
  }

  /* 清空消息列表并断开连接 */
  function clearMessages() {
    sseDisconnect()
    messages.value = []
    isLoading.value = false
  }

  return {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
  }
})
