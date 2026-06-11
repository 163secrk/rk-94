<template>
  <div class="max-w-7xl mx-auto">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <el-icon class="text-love mr-2"><CircleCheck /></el-icon>
        项目审核
      </h2>
      <p class="text-gray-500 mt-1">审核平台公益项目，确保项目合规可信</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div
        v-for="stat in stats"
        :key="stat.key"
        class="bg-white rounded-xl p-5 card-shadow cursor-pointer hover:shadow-lg transition-all"
        :class="{ 'ring-2 ring-love': activeStatus === stat.key }"
        @click="activeStatus = stat.key"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm mb-1">{{ stat.label }}</p>
            <p class="text-3xl font-bold" :class="stat.color">{{ stat.count }}</p>
          </div>
          <div
            class="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
            :class="stat.bgColor"
          >
            <el-icon :class="stat.color"><component :is="stat.icon" /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="min-h-[500px]">
      <el-table
        :data="projects"
        border
        stripe
        style="width: 100%"
        class="bg-white card-shadow rounded-xl overflow-hidden"
      >
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="项目信息" min-width="300">
          <template #default="{ row }">
            <div class="flex items-center py-1">
              <div
                class="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 mr-4 flex-shrink-0"
              >
                <img
                  v-if="row.cover_image"
                  :src="row.cover_image"
                  :alt="row.title"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex items-center justify-center bg-love-50">
                  <el-icon class="text-2xl text-love opacity-60"><Collection /></el-icon>
                </div>
              </div>
              <div class="min-w-0 flex-1">
                <p
                  class="font-semibold text-gray-800 truncate cursor-pointer hover:text-love transition-colors"
                  @click="viewDetail(row)"
                >
                  {{ row.title }}
                </p>
                <div class="flex items-center gap-2 mt-1 flex-wrap">
                  <el-tag size="small" type="warning">{{ row.category_display }}</el-tag>
                  <span class="text-xs text-gray-400">目标：¥{{ formatNumber(row.target_amount) }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="发起方" width="160">
          <template #default="{ row }">
            <div class="flex items-center">
              <el-avatar :size="28" class="bg-love mr-2 flex-shrink-0">
                {{ row.initiator.username?.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="truncate">{{ row.initiator.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="筹款目标" width="140" align="right">
          <template #default="{ row }">
            <span class="font-semibold">¥{{ formatNumber(row.target_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="140" align="center">
          <template #default="{ row }">
            {{ formatDate(row.deadline) }}
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="dark">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="default"
              @click="viewDetail(row)"
            >
              查看
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              type="success"
              link
              size="default"
              @click="handleApprove(row)"
            >
              通过
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              type="danger"
              link
              size="default"
              @click="handleReject(row)"
            >
              拒绝
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无数据" />
        </template>
      </el-table>
    </div>

    <el-dialog
      v-model="auditDialogVisible"
      :title="`审核：${currentProject?.title || ''}`"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="currentProject" class="space-y-4">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="项目分类">
            <el-tag type="warning">{{ currentProject.category_display }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="目标金额">
            <span class="text-love font-bold">¥{{ formatNumber(currentProject.target_amount) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="发起方">
            {{ currentProject.initiator.username }}
          </el-descriptions-item>
          <el-descriptions-item label="截止日期">
            {{ formatDate(currentProject.deadline) }}
          </el-descriptions-item>
          <el-descriptions-item label="项目简介" :span="2">
            {{ currentProject.description }}
          </el-descriptions-item>
        </el-descriptions>

        <el-form
          ref="auditFormRef"
          :model="auditForm"
          :rules="auditRules"
          label-position="top"
        >
          <el-form-item label="审核操作">
            <el-radio-group v-model="auditForm.status" size="large">
              <el-radio-button value="approved" class="w-1/2 text-center">
                <el-icon class="mr-1 text-green-500"><CircleCheckFilled /></el-icon>
                通过审核
              </el-radio-button>
              <el-radio-button value="rejected" class="w-1/2 text-center">
                <el-icon class="mr-1 text-red-500"><CircleCloseFilled /></el-icon>
                拒绝通过
              </el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item
            v-if="auditForm.status === 'rejected'"
            label="拒绝原因"
            prop="reject_reason"
          >
            <el-input
              v-model="auditForm.reject_reason"
              type="textarea"
              :rows="4"
              placeholder="请输入拒绝原因（必填）"
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="auditDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          class="!bg-love !border-love"
          :loading="auditLoading"
          @click="submitAudit"
        >
          确认提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getPendingProjects, auditProject } from '@/api/projects'
import type { Project, ProjectAuditForm } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  CircleCheck, Clock, Check, CircleClose, InfoFilled, Collection,
  CircleCheckFilled, CircleCloseFilled
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const projects = ref<Project[]>([])
const activeStatus = ref('pending')
const auditDialogVisible = ref(false)
const auditLoading = ref(false)
const currentProject = ref<Project | null>(null)
const auditFormRef = ref<FormInstance>()

const auditForm = reactive<ProjectAuditForm>({
  status: 'approved',
  reject_reason: '',
})

const auditRules: FormRules = {
  status: [{ required: true, message: '请选择审核操作', trigger: 'change' }],
  reject_reason: [
    {
      validator: (_rule, value, callback) => {
        if (auditForm.status === 'rejected' && !value) {
          callback(new Error('请填写拒绝原因'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const stats = computed(() => {
  const all = projects.value
  return [
    { key: 'pending', label: '待审核', count: all.filter(p => p.status === 'pending').length, color: 'text-yellow-500', bgColor: 'bg-yellow-50', icon: 'Clock' },
    { key: 'funding', label: '募集中', count: all.filter(p => p.status === 'funding').length, color: 'text-green-500', bgColor: 'bg-green-50', icon: 'CircleCheckFilled' },
    { key: 'rejected', label: '已拒绝', count: all.filter(p => p.status === 'rejected').length, color: 'text-red-500', bgColor: 'bg-red-50', icon: 'CircleCloseFilled' },
    { key: 'all', label: '全部', count: all.length, color: 'text-love', bgColor: 'bg-love-50', icon: 'Files' },
  ]
})

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await getPendingProjects(activeStatus.value === 'all' ? 'all' : activeStatus.value)
    projects.value = res
  } catch (error) {
    console.error('Fetch pending projects error:', error)
  } finally {
    loading.value = false
  }
}

watch(activeStatus, () => {
  fetchProjects()
})

const statusTagType = (status: string) => {
  switch (status) {
    case 'funding': return 'success'
    case 'completed': return 'info'
    case 'approved': return 'primary'
    case 'rejected': return 'danger'
    default: return 'warning'
  }
}

const viewDetail = (row: Project) => {
  router.push(`/projects/${row.id}`)
}

const handleApprove = (row: Project) => {
  currentProject.value = row
  auditForm.status = 'approved'
  auditForm.reject_reason = ''
  auditDialogVisible.value = true
}

const handleReject = (row: Project) => {
  currentProject.value = row
  auditForm.status = 'rejected'
  auditForm.reject_reason = ''
  auditDialogVisible.value = true
}

const submitAudit = async () => {
  if (!currentProject.value || !auditFormRef.value) return
  try {
    await auditFormRef.value.validate()
  } catch (error) {
    return
  }

  try {
    auditLoading.value = true
    await auditProject(currentProject.value.id, { ...auditForm })
    ElMessage.success(auditForm.status === 'approved' ? '项目已通过审核' : '项目已拒绝')
    auditDialogVisible.value = false
    await fetchProjects()
  } catch (error: any) {
    console.error('Audit error:', error)
    ElMessage.error(error?.response?.data?.message || '审核操作失败')
  } finally {
    auditLoading.value = false
  }
}

const formatNumber = (num: string | number) => {
  const n = typeof num === 'string' ? parseFloat(num) : num
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchProjects()
})
</script>
