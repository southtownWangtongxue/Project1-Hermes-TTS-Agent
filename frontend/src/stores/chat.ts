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
