<script setup lang="ts">
/**
 * 首页视图
 * 展示项目名称、简介以及进入聊天页的入口
 */
import { useRouter } from 'vue-router'

const router = useRouter()

/* 跳转到聊天页面 */
function goToChat() {
  router.push('/chat')
}
</script>

<template>
  <div class="home-page">
    <div class="hero-section">
      <h1 class="hero-title">DataAgent Pro</h1>
      <p class="hero-desc">
        智能数据分析助手 —— 基于大语言模型的对话式数据探索平台。
        通过自然语言对话，轻松完成数据分析、图表生成与洞察发掘。
      </p>
      <el-button type="primary" size="large" @click="goToChat">
        开始对话
      </el-button>
    </div>

    <div class="feature-section">
      <el-row :gutter="24">
        <el-col :span="8">
          <el-card shadow="hover">
            <h3>自然语言交互</h3>
            <p>使用日常语言描述您的数据分析需求，无需编写代码。</p>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <h3>智能图表生成</h3>
            <p>自动为您生成直观的数据可视化图表，洞察一目了然。</p>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <h3>多数据源支持</h3>
            <p>支持 CSV、Excel、数据库等多种数据源的上传与连接。</p>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 60px 24px;
}

.hero-section {
  text-align: center;
  margin-bottom: 64px;
}

.hero-title {
  font-size: 42px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 16px;
}

.hero-desc {
  font-size: 16px;
  color: #606266;
  line-height: 1.8;
  max-width: 600px;
  margin: 0 auto 32px;
}

.feature-section h3 {
  font-size: 18px;
  margin-bottom: 8px;
  color: #303133;
}

.feature-section p {
  font-size: 14px;
  color: #909399;
  line-height: 1.6;
}
</style>
