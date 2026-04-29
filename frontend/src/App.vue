<script setup lang="ts">
/**
 * App 根组件
 * 采用全屏 Flex 布局：顶部标题栏（含导航链接）+ 中间内容区（路由页面）
 * 聊天页面会撑满整个内容区域
 */
import { useRoute } from 'vue-router'

const route = useRoute()

/* 构建导航项，active 根据当前路由计算 */
interface NavItem {
  path: string
  label: string
}

const navItems: NavItem[] = [
  { path: '/', label: '首页' },
  { path: '/chat', label: '智能对话' },
  { path: '/approval', label: '审批管理' },
]
</script>

<template>
  <div class="app-container">
    <!-- 顶部标题栏 -->
    <header class="app-header">
      <h1 class="app-title">DataAgent Pro</h1>
      <nav class="app-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :class="{ active: route.path === item.path }"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </header>

    <!-- 主内容区 -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style>
/* 全局重置：确保全屏高度无留白 */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
  overflow: hidden; /* 禁止外层滚动，由内部路由页面自行管理滚动 */
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0; /* 允许 flex 子元素正确收缩 */
}

.app-header {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 24px;
  background-color: #1a1a2e;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
  z-index: 100;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
  margin-right: 32px;
}

/* ===== 导航栏 ===== */
.app-nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: background-color 0.2s, color 0.2s;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.nav-link.active {
  background-color: rgba(64, 158, 255, 0.25);
  color: #409eff;
}

.app-main {
  flex: 1;
  min-height: 0; /* 关键：允许 flex 子元素收缩到内容以下，使内部滚动生效 */
  background-color: #f5f7fa;
}
</style>
