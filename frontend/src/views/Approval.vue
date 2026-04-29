<script setup lang="ts">
/**
 * 审批管理页面
 * 展示高危 SQL 审批任务列表，支持通过/驳回操作
 */
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApprovalStore } from '@/stores/approval'
import type { ApprovalTask } from '@/stores/approval'

const store = useApprovalStore()

/* 审批操作加载中标记（key 为 threadId） */
const approvingMap = ref<Record<string, boolean>>({})

/* 格式化时间戳为可读字符串 */
function formatTime(ts: number): string {
  const d = new Date(ts)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

/* 截断过长的用户问题 */
function shortQuestion(q: string): string {
  if (q.length > 40) return q.slice(0, 40) + '...'
  return q
}

/* 截断过长的 SQL 语句 */
function shortSQL(sql: string): string {
  if (sql.length > 80) return sql.slice(0, 80) + '...'
  return sql
}

/* 根据状态返回 el-tag 的 type 值 */
function statusType(status: string): 'warning' | 'success' | 'danger' | 'info' {
  switch (status) {
    case 'pending':
      return 'warning'
    case 'approved':
      return 'success'
    case 'rejected':
      return 'danger'
    default:
      return 'info'
  }
}

/* 根据状态返回中文显示文本 */
function statusText(status: string): string {
  switch (status) {
    case 'pending':
      return '待审批'
    case 'approved':
      return '已通过'
    case 'rejected':
      return '已驳回'
    default:
      return status
  }
}

/* 复制完整 SQL 到剪贴板 */
async function copySQL(sql: string) {
  try {
    await navigator.clipboard.writeText(sql)
    ElMessage.success('SQL 已复制到剪贴板')
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = sql
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('SQL 已复制到剪贴板')
  }
}

/* 执行"通过"审批操作 */
async function doApprove(task: ApprovalTask) {
  ElMessageBox.prompt('请输入审批备注（可选）', '确认通过', {
    confirmButtonText: '确认通过',
    cancelButtonText: '取消',
    type: 'warning',
    inputPlaceholder: '审批备注...',
  }).then(async ({ value }) => {
    approvingMap.value[task.threadId] = true
    try {
      await store.approveTask(task.threadId, value || undefined)
      ElMessage.success(`任务 ${task.threadId} 已通过`)
    } catch {
      ElMessage.error('审批请求失败，请稍后重试')
    } finally {
      approvingMap.value[task.threadId] = false
    }
  }).catch(() => {
    // 用户取消操作，不做任何处理
  })
}

async function doReject(task: ApprovalTask) {
  ElMessageBox.prompt('请输入驳回理由（可选）', '确认驳回', {
    confirmButtonText: '确认驳回',
    cancelButtonText: '取消',
    type: 'error',
    inputPlaceholder: '驳回理由...',
  }).then(async ({ value }) => {
    approvingMap.value[task.threadId] = true
    try {
      await store.rejectTask(task.threadId, value || undefined)
      ElMessage.success(`任务 ${task.threadId} 已驳回`)
    } catch {
      ElMessage.error('驳回请求失败，请稍后重试')
    } finally {
      approvingMap.value[task.threadId] = false
    }
  }).catch(() => {
    // 用户取消操作，不做任何处理
  })
}

/* 清除已完成任务 */
function handleRemove(task: ApprovalTask) {
  store.removeTask(task.threadId)
  ElMessage.success('任务已移除')
}

/* 判断某行是否正在执行审批操作 */
function isApprovingTask(threadId: string): boolean {
  return !!approvingMap.value[threadId]
}
</script>

<template>
  <div class="approval-container">
    <!-- 页面标题 -->
    <header class="approval-header">
      <h2 class="approval-title">高危 SQL 审批管理</h2>
    </header>

    <!-- 任务列表表格 -->
    <div class="approval-table-wrapper">
      <el-table
        :data="store.tasks"
        border
        stripe
        size="default"
        style="width: 100%"
        empty-text="暂无待审批任务"
      >
        <!-- 任务 ID -->
        <el-table-column
          prop="threadId"
          label="任务 ID"
          min-width="140"
          show-overflow-tooltip
        />

        <!-- 用户问题 -->
        <el-table-column
          label="用户问题"
          min-width="180"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ shortQuestion(row.question) }}
          </template>
        </el-table-column>

        <!-- SQL 语句（代码样式展示，过长省略 + 复制按钮） -->
        <el-table-column label="SQL 语句" min-width="260">
          <template #default="{ row }">
            <div class="sql-cell">
              <code class="sql-cell-code">{{ shortSQL(row.sql) }}</code>
              <el-button
                text
                size="small"
                class="sql-copy-btn"
                @click="copySQL(row.sql)"
              >
                复制
              </el-button>
            </div>
          </template>
        </el-table-column>

        <!-- 危险原因 -->
        <el-table-column
          prop="reason"
          label="危险原因"
          min-width="150"
          show-overflow-tooltip
        />

        <!-- 提交时间 -->
        <el-table-column label="提交时间" min-width="160">
          <template #default="{ row }">
            {{ formatTime(row.createdAt) }}
          </template>
        </el-table-column>

        <!-- 状态 -->
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag
              :type="statusType(row.status)"
              size="small"
              disable-transitions
            >
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 操作按钮 -->
        <el-table-column label="操作" min-width="220" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button
                type="success"
                size="small"
                :loading="isApprovingTask(row.threadId)"
                @click="doApprove(row)"
              >
                通过
              </el-button>
              <el-button
                type="danger"
                size="small"
                :loading="isApprovingTask(row.threadId)"
                @click="doReject(row)"
              >
                驳回
              </el-button>
            </template>
            <template v-else>
              <el-button
                type="info"
                size="small"
                plain
                @click="handleRemove(row)"
              >
                移除
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
/* ===== 整体布局 ===== */
.approval-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: calc(100vh - 56px);
  background-color: #f5f7fa;
}

/* ===== 页面标题栏 ===== */
.approval-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  height: 52px;
  padding: 0 20px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.approval-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* ===== 表格容器 ===== */
.approval-table-wrapper {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.approval-table-wrapper::-webkit-scrollbar {
  width: 6px;
}

.approval-table-wrapper::-webkit-scrollbar-thumb {
  background-color: #c0c4cc;
  border-radius: 3px;
}

/* ===== SQL 代码单元格 ===== */
.sql-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sql-cell-code {
  font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
  font-size: 12px;
  color: #303133;
  background-color: #f2f3f5;
  padding: 2px 8px;
  border-radius: 4px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
}

.sql-copy-btn {
  flex-shrink: 0;
  font-size: 12px;
  color: #909399;
}

.sql-copy-btn:hover {
  color: #409eff;
}
</style>
