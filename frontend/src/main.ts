import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// 安装路由
app.use(router)

// 安装状态管理
app.use(createPinia())

// 安装 Element Plus UI 组件库
app.use(ElementPlus)

app.mount('#app')
