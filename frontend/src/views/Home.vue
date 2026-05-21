<script setup lang="ts">
/**
 * 首页视图
 * 展示项目名称、简介以及进入聊天页的入口
 * 设计风格：Apple 极简美学 + 深色科技感
 */
import { useRouter } from 'vue-router'

const router = useRouter()

/* 跳转到聊天页面 */
function goToChat() {
  router.push('/chat')
}

/* 功能特性数据 */
const features = [
  {
    icon: 'chat',
    title: '自然语言交互',
    description: '使用日常语言描述您的数据分析需求，无需编写代码即可完成复杂查询。',
    gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
  },
  {
    icon: 'chart',
    title: '智能图表生成',
    description: '自动为您生成直观的数据可视化图表，支持折线图、饼图、柱状图等多种形式。',
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%)',
  },
  {
    icon: 'shield',
    title: '企业级安全',
    description: '高危 SQL 自动审批，数据脱敏保护，确保您的业务数据安全无忧。',
    gradient: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
  },
  {
    icon: 'database',
    title: '多数据源支持',
    description: '支持 MySQL、PostgreSQL、Oracle、SQL Server 等多种主流数据库。',
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)',
  },
]
</script>

<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          AI-powered Data Analytics
        </div>
        
        <h1 class="hero-title">
          用自然语言<br/>
          <span class="title-gradient">探索数据洞察</span>
        </h1>
        
        <p class="hero-description">
          DataAgent Pro 是一款智能数据分析助手，基于大语言模型，
          <br class="desktop-only"/>
          让非技术用户也能轻松完成复杂的数据查询与分析。
        </p>
        
        <div class="hero-actions">
          <button class="btn-primary" @click="goToChat">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            开始对话
          </button>
          <button class="btn-secondary">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            观看演示
          </button>
        </div>
      </div>
      
      <!-- Hero Visual -->
      <div class="hero-visual">
        <div class="visual-card">
          <div class="visual-header">
            <div class="visual-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
          <div class="visual-content">
            <div class="visual-query">
              <div class="query-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.35-4.35"/>
                </svg>
              </div>
              <span>"查询本月销售额前10的产品"</span>
            </div>
            <div class="visual-response">
              <div class="response-line" style="width: 60%"></div>
              <div class="response-line" style="width: 80%"></div>
              <div class="response-line" style="width: 45%"></div>
            </div>
            <div class="visual-chart">
              <div class="chart-bar" style="height: 60%"></div>
              <div class="chart-bar" style="height: 85%"></div>
              <div class="chart-bar" style="height: 45%"></div>
              <div class="chart-bar" style="height: 70%"></div>
              <div class="chart-bar" style="height: 95%"></div>
            </div>
          </div>
        </div>
        
        <!-- Floating Elements -->
        <div class="floating-element element-1">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <div class="floating-element element-2">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <h2 class="section-title">为什么选择 DataAgent Pro</h2>
        <p class="section-description">
          专为业务人员设计的智能数据分析平台，让数据探索变得简单
        </p>
      </div>
      
      <div class="features-grid">
        <div
          v-for="feature in features"
          :key="feature.title"
          class="feature-card"
        >
          <div class="feature-icon" :style="{ background: feature.gradient }">
            <svg v-if="feature.icon === 'chat'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <svg v-else-if="feature.icon === 'chart'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"/>
              <line x1="12" y1="20" x2="12" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            <svg v-else-if="feature.icon === 'shield'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <svg v-else-if="feature.icon === 'database'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
              <ellipse cx="12" cy="5" rx="9" ry="3"/>
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
            </svg>
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-description">{{ feature.description }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100%;
  padding: var(--space-12) var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
}

/* === Hero Section === */
.hero-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-16);
  align-items: center;
  padding: var(--space-12) 0;
}

.hero-content {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background-color: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-primary-light);
  margin-bottom: var(--space-6);
}

.badge-dot {
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(0.9);
  }
}

.hero-title {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
  margin-bottom: var(--space-6);
}

.title-gradient {
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 50%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-description {
  font-size: 18px;
  line-height: 1.7;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-8);
}

.desktop-only {
  display: none;
}

@media (min-width: 768px) {
  .desktop-only {
    display: inline;
  }
}

.hero-actions {
  display: flex;
  gap: var(--space-4);
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  border: none;
  border-radius: var(--radius-lg);
  font-size: 15px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background-color: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary:hover {
  background-color: var(--color-surface);
  border-color: var(--color-border-light);
  color: var(--color-text-primary);
}

/* === Hero Visual === */
.hero-visual {
  position: relative;
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

.visual-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.visual-header {
  padding: var(--space-3) var(--space-4);
  background-color: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--color-border);
}

.visual-dots {
  display: flex;
  gap: var(--space-2);
}

.visual-dots span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--color-border);
}

.visual-dots span:first-child {
  background-color: #ef4444;
}

.visual-dots span:nth-child(2) {
  background-color: #f59e0b;
}

.visual-dots span:nth-child(3) {
  background-color: #22c55e;
}

.visual-content {
  padding: var(--space-6);
}

.visual-query {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background-color: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
}

.query-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary-light);
}

.visual-query span {
  font-size: 14px;
  color: var(--color-text-primary);
}

.visual-response {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
}

.response-line {
  height: 12px;
  background: linear-gradient(90deg, var(--color-border) 0%, transparent 100%);
  border-radius: var(--radius-sm);
}

.visual-chart {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  height: 120px;
}

.chart-bar {
  flex: 1;
  background: linear-gradient(180deg, #6366f1 0%, #4f46e5 100%);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: all var(--transition-normal);
}

.chart-bar:hover {
  background: linear-gradient(180deg, #818cf8 0%, #6366f1 100%);
}

/* === Floating Elements === */
.floating-element {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  animation: float 3s ease-in-out infinite;
}

.element-1 {
  top: -20px;
  right: -20px;
  animation-delay: 0s;
}

.element-2 {
  bottom: 40px;
  left: -30px;
  animation-delay: 1s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* === Features Section === */
.features-section {
  padding: var(--space-16) 0;
}

.section-header {
  text-align: center;
  margin-bottom: var(--space-12);
}

.section-title {
  font-size: 36px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

.section-description {
  font-size: 16px;
  color: var(--color-text-secondary);
  max-width: 500px;
  margin: 0 auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-6);
}

.feature-card {
  padding: var(--space-6);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  transition: all var(--transition-normal);
}

.feature-card:hover {
  border-color: var(--color-border-light);
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-4);
}

.feature-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.feature-description {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

/* === Responsive === */
@media (max-width: 1024px) {
  .hero-section {
    grid-template-columns: 1fr;
    gap: var(--space-12);
    text-align: center;
  }
  
  .hero-title {
    font-size: 42px;
  }
  
  .hero-actions {
    justify-content: center;
  }
  
  .hero-visual {
    max-width: 500px;
    margin: 0 auto;
  }
  
  .floating-element {
    display: none;
  }
}

@media (max-width: 768px) {
  .home-page {
    padding: var(--space-8) var(--space-4);
  }
  
  .hero-title {
    font-size: 32px;
  }
  
  .hero-description {
    font-size: 16px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .section-title {
    font-size: 28px;
  }
}
</style>
