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
