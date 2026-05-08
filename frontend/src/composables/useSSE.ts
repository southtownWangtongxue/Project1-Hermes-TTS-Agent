import { ref } from 'vue'

/* SSE 事件回调接口 */
export interface SSEEventCallbacks {
  /* 状态更新：如"正在分析..." */
  onStatus?: (content: string) => void
  /* Schema 信息 */
  onSchema?: (content: string) => void
  /* 生成的 其他信息*/
  onText?: (content: string) => void
  /* 生成的 SQL 语句 */
  onSQL?: (content: string) => void
  /* 查询结果数据 */
  onResult?: (data: any[], columns: string[]) => void
  /* 错误信息 */
  onError?: (error: string) => void
  /* 流正常结束 */
  onDone?: () => void
  /* 高危 SQL 需要审批 */
  onApprovalRequired?: (threadId: string, question: string, sql: string, reason: string) => void
}

/* SSE 事件数据格式（后端推送的 JSON 结构） */
interface SSEEventData {
  type: string
  content?: string
  data?: any[]
  columns?: string[]
  error?: string
  /* approval_required 事件专用字段 */
  thread_id?: string
  question?: string
  sql?: string
  reason?: string
}

/**
 * SSE 流式接收 Composable
 * 使用 fetch + ReadableStream 方式读取后端推送的 SSE 事件流
 */
export function useSSE() {
  /* 是否正在连接 */
  const connecting = ref(false)

  /* AbortController 用于取消请求 */
  let abortController: AbortController | null = null

  /**
   * 建立 SSE 连接并持续读取流数据
   * @param url - SSE 接口地址
   * @param body - 请求体（JSON 对象）
   * @param callbacks - 事件回调集合
   */
  async function connect(
    url: string,
    body: object,
    callbacks: SSEEventCallbacks,
  ): Promise<void> {
    // 中止上一次连接
    disconnect()

    connecting.value = true
    abortController = new AbortController()
    let hasError = false

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`SSE 连接失败: HTTP ${response.status}`)
      }
      if (!response.body) {
        throw new Error('SSE 连接失败: 响应体为空')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      // 持续读取流数据
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // 将新数据追加到缓冲区
        buffer += decoder.decode(value, { stream: true })

        // 按行分割，最后一行可能不完整，保留在 buffer 中
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          // 跳过空行和 SSE 注释行
          if (!trimmed || trimmed.startsWith(':')) continue

          // 解析 "data: {...}" 格式
          if (trimmed.startsWith('data: ')) {
            const jsonStr = trimmed.slice(6).trim()
            if (!jsonStr) continue

            try {
              const event: SSEEventData = JSON.parse(jsonStr)
              dispatchEvent(event, callbacks)
            } catch {
              console.warn('[SSE] JSON 解析失败:', jsonStr)
            }
          }
        }
      }
    } catch (error: unknown) {
      // 用户主动取消（AbortError），不视为错误
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }
      hasError = true
      const errMsg =
        error instanceof Error ? error.message : '未知网络错误'
      callbacks.onError?.(errMsg)
    } finally {
      connecting.value = false
      // 只有非错误、非取消的情况才触发 onDone
      if (!hasError && abortController && !abortController.signal.aborted) {
        callbacks.onDone?.()
      }
      abortController = null
    }
  }

  /**
   * 根据 SSE 事件 type 分发到对应的回调函数
   */
  function dispatchEvent(
    event: SSEEventData,
    callbacks: SSEEventCallbacks,
  ): void {
    switch (event.type) {
      case 'status':
        callbacks.onStatus?.(event.content || '')
        break
      case 'schema':
        callbacks.onSchema?.(event.content || '')
        break
      case 'sql':
        callbacks.onSQL?.(event.content || '')
        break
      case 'text':
        callbacks.onText?.(event.content || '')
        break
      case 'result':
        callbacks.onResult?.(event.data || [], event.columns || [])
        break
      case 'error':
        callbacks.onError?.(event.error || event.content || '未知错误')
        break
      case 'done':
        callbacks.onDone?.()
        break
      case 'approval_required':
        callbacks.onApprovalRequired?.(
          event.thread_id || '',
          event.question || '',
          event.sql || '',
          event.reason || '',
        )
        break
      default:
        console.warn('[SSE] 未知事件类型:', event.type)
    }
  }

  /**
   * 断开 SSE 连接（取消正在进行的请求）
   */
  function disconnect(): void {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    connecting.value = false
  }

  return {
    connecting,
    connect,
    disconnect,
  }
}
