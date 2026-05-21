<script setup lang="ts">
/**
 * 聊天页面
 * 提供智能数据助手的对话交互界面
 * 设计风格：深色主题 + Apple 极简美学
 */
import { ref, watch, nextTick } from 'vue'
import { useChatStore, type ChatMessage } from '@/stores/chat'

const store = useChatStore()

/* 输入框文本 */
const inputText = ref('')

/* 消息列表容器 DOM 引用 */
const messagesContainer = ref<HTMLElement | null>(null)

/* 自动滚动到消息列表底部 */
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 监听消息数量变化，自动滚动到底部
watch(() => store.messages.length, () => {
  scrollToBottom()
})

/* 发送消息 */
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || store.isLoading) return

  inputText.value = ''
  await store.sendMessage(text)
}

/* 键盘事件：Enter 发送，Shift+Enter 换行 */
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}

/* 复制 SQL 文本到剪贴板 */
async function copySQL(sql: string) {
  try {
    await navigator.clipboard.writeText(sql)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = sql
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
}

/* 根据消息类型返回对应的 CSS 类名 */
function messageClass(msg: ChatMessage): Record<string, boolean> {
  return {
    'message-user': msg.role === 'user',
    'message-status': msg.type === 'status',
    'message-error': msg.type === 'error',
    'message-assistant': msg.role === 'assistant' && msg.type !== 'error',
  }
}
</script>

<template>
  <div class="chat-container">
    <!-- 消息列表区域 -->
    <div ref="messagesContainer" class="chat-messages" :class="{ 'is-empty': store.messages.length === 0 }">
      <!-- 空状态提示 -->
      <div v-if="store.messages.length === 0" class="chat-empty">
        <div class="empty-illustration">
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
            <rect x="4" y="4" width="72" height="72" rx="16" fill="url(#emptyGradient)" opacity="0.1"/>
            <rect x="4" y="4" width="72" height="72" rx="16" stroke="url(#emptyGradient)" stroke-width="2"/>
            <path d="M24 32h32M24 40h24M24 48h28" stroke="#6366f1" stroke-width="2" stroke-linecap="round"/>
            <circle cx="56" cy="52" r="12" fill="#18181b" stroke="#6366f1" stroke-width="2"/>
            <path d="M56 48v8M52 52h8" stroke="#6366f1" stroke-width="2" stroke-linecap="round"/>
            <defs>
              <linearGradient id="emptyGradient" x1="4" y1="4" x2="76" y2="76">
                <stop stop-color="#6366f1"/>
                <stop offset="1" stop-color="#818cf8"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h3 class="empty-title">开始您的数据分析之旅</h3>
        <p class="empty-text">用自然语言描述您的数据需求，AI 将为您查询、分析并可视化</p>
        <div class="empty-suggestions">
          <button class="suggestion-chip" @click="inputText = '查询本月销售额Top10产品'">
            查询本月销售额Top10产品
          </button>
          <button class="suggestion-chip" @click="inputText = '分析用户增长趋势'">
            分析用户增长趋势
          </button>
          <button class="suggestion-chip" @click="inputText = '查看各地区营收占比'">
            查看各地区营收占比
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="msg in store.messages"
        :key="msg.id"
        class="message-item"
        :class="messageClass(msg)"
      >
        <!-- 用户消息：右对齐渐变气泡 -->
        <template v-if="msg.role === 'user' && msg.type === 'text'">
          <div class="message-bubble message-bubble--user">
            {{ msg.content }}
          </div>
        </template>

        <!-- 系统状态消息：居中渐变文字 -->
        <template v-else-if="msg.type === 'status'">
          <div class="message-status-text">
            <span class="status-dot"></span>
            {{ msg.content }}
          </div>
        </template>

        <!-- SQL 消息：深色代码块 -->
        <template v-else-if="msg.type === 'sql'">
          <div class="message-sql">
            <div class="sql-header">
              <div class="sql-label">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="16 18 22 12 16 6"/>
                  <polyline points="8 6 2 12 8 18"/>
                </svg>
                SQL 查询
              </div>
              <button class="sql-copy-btn" @click="copySQL(msg.sql || '')">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                复制
              </button>
            </div>
            <pre class="sql-code"><code>{{ msg.sql }}</code></pre>
          </div>
        </template>

        <!-- 结果消息：表格展示 -->
        <template v-else-if="msg.type === 'result'">
          <div class="message-result">
            <div class="result-header">
              <div class="result-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <line x1="3" y1="9" x2="21" y2="9"/>
                  <line x1="3" y1="15" x2="21" y2="15"/>
                  <line x1="9" y1="3" x2="9" y2="21"/>
                  <line x1="15" y1="3" x2="15" y2="21"/>
                </svg>
                查询结果
              </div>
              <span class="result-count" v-if="msg.data">
                {{ msg.data.length }} 条记录
              </span>
            </div>
            <div class="result-table-wrapper">
              <el-table
                :data="msg.data || []"
                border
                stripe
                size="small"
                max-height="360"
                style="width: 100%"
                :header-cell-style="{ background: '#27272a', color: '#fafafa', borderColor: '#3f3f46' }"
                :cell-style="{ background: '#18181b', color: '#a1a1aa', borderColor: '#3f3f46' }"
              >
                <el-table-column
                  v-for="col in msg.columns"
                  :key="col"
                  :prop="col"
                  :label="col"
                  min-width="120"
                  show-overflow-tooltip
                />
              </el-table>
            </div>
          </div>
        </template>

        <!-- 错误消息：红色提示 -->
        <template v-else-if="msg.type === 'error'">
          <div class="message-error-text">
            <span class="error-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </span>
            {{ msg.content }}
          </div>
        </template>

        <!-- 助手普通文本消息 -->
        <template v-else-if="msg.role === 'assistant'">
          <div class="message-bubble message-bubble--assistant">
            {{ msg.content }}
          </div>
        </template>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <footer class="chat-input-area">
      <div class="input-wrapper">
        <div class="input-container">
          <textarea
            v-model="inputText"
            class="input-field"
            placeholder="输入您的问题，按 Enter 发送..."
            :disabled="store.isLoading"
            rows="1"
            @keydown="handleKeydown"
          ></textarea>
          <button
            class="send-btn"
            :disabled="!inputText.trim() || store.isLoading"
            :class="{ 'is-loading': store.isLoading }"
            @click="handleSend"
          >
            <svg v-if="!store.isLoading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
            <span v-else class="loading-spinner"></span>
          </button>
        </div>
        <p class="input-hint">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Shift + Enter 换行 · 支持自然语言查询
        </p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* === 整体布局 === */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: calc(100vh - 64px);
  background-color: var(--color-bg);
}

/* === 消息列表区域 === */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  scroll-behavior: smooth;
}

/* 滚动条美化 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background-color: var(--color-border);
  border-radius: var(--radius-full);
}

.chat-messages::-webkit-scrollbar-track {
  background-color: transparent;
}

.chat-messages.is-empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* === 空状态 === */
.chat-empty {
  text-align: center;
  max-width: 480px;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.empty-illustration {
  margin-bottom: var(--space-6);
}

.empty-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.empty-text {
  font-size: 15px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--space-8);
}

.empty-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  justify-content: center;
}

.suggestion-chip {
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.suggestion-chip:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.3);
  color: var(--color-primary-light);
}

/* === 消息项 === */
.message-item {
  margin-bottom: var(--space-5);
  display: flex;
  animation: messageIn 0.3s ease-out;
}

@keyframes messageIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-item:last-child {
  margin-bottom: 0;
}

/* 用户消息：右对齐 */
.message-user {
  justify-content: flex-end;
}

/* 助手消息：左对齐 */
.message-assistant {
  justify-content: flex-start;
}

/* 状态/错误消息：居中 */
.message-status,
.message-error {
  justify-content: center;
}

/* === 消息气泡 === */
.message-bubble {
  max-width: 72%;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-xl);
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 用户气泡：渐变色 */
.message-bubble--user {
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  color: white;
  border-bottom-right-radius: var(--radius-sm);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
}

/* 助手气泡：深色表面 */
.message-bubble--assistant {
  background-color: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: var(--radius-sm);
}

/* === 状态文字 === */
.message-status-text {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: var(--radius-full);
  font-size: 13px;
  color: var(--color-primary-light);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* === SQL 代码块 === */
.message-sql {
  max-width: 88%;
  background: #0d0d0f;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.sql-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: rgba(99, 102, 241, 0.05);
  border-bottom: 1px solid var(--color-border);
}

.sql-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 12px;
  font-weight: 500;
  color: var(--color-primary-light);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.sql-copy-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.sql-copy-btn:hover {
  background: var(--color-surface);
  border-color: var(--color-border-light);
  color: var(--color-text-secondary);
}

.sql-code {
  margin: 0;
  padding: var(--space-4);
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.7;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
  tab-size: 2;
}

/* === 结果表格 === */
.message-result {
  max-width: 92%;
  width: 100%;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.result-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.result-count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.result-table-wrapper {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* === 错误消息 === */
.message-error-text {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-lg);
  font-size: 14px;
  color: #f87171;
  max-width: 82%;
  line-height: 1.5;
}

.error-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* === 底部输入区域 === */
.chat-input-area {
  flex-shrink: 0;
  padding: var(--space-4) var(--space-6) var(--space-6);
  background: linear-gradient(to top, var(--color-bg) 0%, transparent 100%);
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  transition: all var(--transition-fast);
}

.input-container:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.input-field {
  flex: 1;
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: none;
  outline: none;
  font-family: var(--font-sans);
  font-size: 15px;
  color: var(--color-text-primary);
  resize: none;
  line-height: 1.5;
  max-height: 120px;
}

.input-field::placeholder {
  color: var(--color-text-muted);
}

.input-field:disabled {
  opacity: 0.6;
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  border: none;
  border-radius: var(--radius-lg);
  color: white;
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn.is-loading {
  pointer-events: none;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.input-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-3);
  font-size: 12px;
  color: var(--color-text-muted);
}
</style>
