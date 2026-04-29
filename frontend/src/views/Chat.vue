<script setup lang="ts">
/**
 * 聊天页面
 * 提供智能数据助手的对话交互界面，支持显示文本、SQL、结果表格、错误等多种消息类型
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
    // 降级方案：旧版浏览器
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
    <!-- 顶部标题栏 -->
    <header class="chat-header">
      <h2 class="chat-title">智能数据助手</h2>
      <el-button
        text
        size="small"
        :disabled="store.messages.length === 0"
        @click="store.clearMessages()"
      >
        清空对话
      </el-button>
    </header>

    <!-- 消息列表区域 -->
    <div ref="messagesContainer" class="chat-messages" :class="{ 'is-empty': store.messages.length === 0 }">
      <!-- 空状态提示 -->
      <div v-if="store.messages.length === 0" class="chat-empty">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        <p class="empty-text">输入您的问题，开始数据分析对话</p>
        <p class="empty-hint">支持自然语言查询，例如："查询销售额前10的产品"</p>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="msg in store.messages"
        :key="msg.id"
        class="message-item"
        :class="messageClass(msg)"
      >
        <!-- 用户消息：右对齐蓝色气泡 -->
        <template v-if="msg.role === 'user' && msg.type === 'text'">
          <div class="message-bubble message-bubble--user">
            {{ msg.content }}
          </div>
        </template>

        <!-- 系统状态消息：居中浅色文字 -->
        <template v-else-if="msg.type === 'status'">
          <div class="message-status-text">
            <span class="status-dot" />
            {{ msg.content }}
          </div>
        </template>

        <!-- SQL 消息：深色代码块 -->
        <template v-else-if="msg.type === 'sql'">
          <div class="message-sql">
            <div class="sql-header">
              <span class="sql-label">SQL 查询</span>
              <el-button
                text
                size="small"
                class="sql-copy-btn"
                @click="copySQL(msg.sql || '')"
              >
                复制
              </el-button>
            </div>
            <pre class="sql-code"><code>{{ msg.sql }}</code></pre>
          </div>
        </template>

        <!-- 结果消息：Element Plus 表格展示 -->
        <template v-else-if="msg.type === 'result'">
          <div class="message-result">
            <div class="result-header">
              <span class="result-label">查询结果</span>
              <span class="result-count" v-if="msg.data">
                共 {{ msg.data.length }} 条记录
              </span>
            </div>
            <el-table
              :data="msg.data || []"
              border
              stripe
              size="small"
              max-height="360"
              style="width: 100%"
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
        </template>

        <!-- 错误消息：红色提示 -->
        <template v-else-if="msg.type === 'error'">
          <div class="message-error-text">
            <span class="error-icon">!</span>
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
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="2"
          placeholder="请输入您的问题，按 Enter 发送，Shift+Enter 换行"
          :disabled="store.isLoading"
          resize="none"
          @keydown="handleKeydown"
        />
        <el-button
          type="primary"
          :disabled="!inputText.trim() || store.isLoading"
          :loading="store.isLoading"
          :icon="'Promotion'"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* ===== 整体布局 ===== */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: calc(100vh - 56px); /* 减去 App 顶栏高度 */
  background-color: #f5f7fa;
}

/* ===== 顶部标题栏 ===== */
.chat-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 20px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.chat-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* ===== 消息列表区域 ===== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

/* 滚动条美化 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background-color: #c0c4cc;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-track {
  background-color: transparent;
}

.chat-messages.is-empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ===== 空状态 ===== */
.chat-empty {
  text-align: center;
  color: #909399;
}

.empty-icon {
  color: #c0c4cc;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 8px;
  color: #606266;
}

.empty-hint {
  font-size: 13px;
}

/* ===== 消息项 ===== */
.message-item {
  margin-bottom: 18px;
  display: flex;
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

/* ===== 消息气泡 ===== */
.message-bubble {
  max-width: 72%;
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 用户气泡：蓝色 */
.message-bubble--user {
  background-color: #409eff;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

/* 助手气泡：浅灰白底 */
.message-bubble--assistant {
  background-color: #ffffff;
  color: #303133;
  border: 1px solid #e4e7ed;
  border-bottom-left-radius: 4px;
}

/* ===== 状态文字 ===== */
.message-status-text {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
  padding: 5px 14px;
  background-color: #f2f3f5;
  border-radius: 20px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #409eff;
  animation: pulse 1.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ===== SQL 代码块 ===== */
.message-sql {
  max-width: 88%;
  background-color: #1e1e2e;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
}

.sql-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  background-color: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.sql-label {
  font-size: 12px;
  color: #909399;
  letter-spacing: 0.5px;
}

.sql-copy-btn {
  color: #909399 !important;
  font-size: 12px;
}

.sql-copy-btn:hover {
  color: #cdd6f4 !important;
}

.sql-code {
  margin: 0;
  padding: 12px 14px;
  font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.65;
  color: #cdd6f4;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
  tab-size: 2;
}

/* ===== 结果表格 ===== */
.message-result {
  max-width: 92%;
  width: 100%;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.result-label {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
}

.result-count {
  font-size: 12px;
  color: #909399;
}

/* ===== 错误消息 ===== */
.message-error-text {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #f56c6c;
  padding: 8px 16px;
  background-color: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 8px;
  max-width: 82%;
  line-height: 1.5;
}

.error-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background-color: #f56c6c;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

/* ===== 底部输入区域 ===== */
.chat-input-area {
  flex-shrink: 0;
  padding: 12px 20px 16px;
  background-color: #ffffff;
  border-top: 1px solid #e4e7ed;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.input-wrapper :deep(.el-textarea) {
  flex: 1;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.input-wrapper :deep(.el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2);
}

.input-wrapper .el-button {
  flex-shrink: 0;
  height: 40px;
  border-radius: 8px;
  padding: 0 20px;
}
</style>
