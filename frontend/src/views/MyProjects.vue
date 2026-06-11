<template>
  <div class="max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-800 flex items-center">
          <el-icon class="text-love mr-2"><FolderOpened /></el-icon>
          我的项目
        </h2>
        <p class="text-gray-500 mt-1">管理您发起的所有公益项目</p>
      </div>
      <el-button
        v-if="userStore.isInitiator"
        type="primary"
        size="large"
        class="!bg-love !border-love"
        @click="$router.push('/projects/create')"
      >
        <el-icon class="mr-1"><Plus /></el-icon>
        发起新项目
      </el-button>
    </div>

    <div class="bg-white rounded-xl p-4 card-shadow mb-6">
      <div class="flex flex-wrap items-center gap-4">
        <span class="text-gray-600 font-medium">状态筛选：</span>
        <el-radio-group v-model="activeStatus" size="default">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button
            v-for="s in PROJECT_STATUS_OPTIONS"
            :key="s.value"
            :value="s.value"
          >
            {{ s.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div v-loading="loading" class="min-h-[400px]">
      <el-empty
        v-if="filteredProjects.length === 0 && !loading"
        description="您还没有发起任何项目"
      >
        <el-button
          v-if="userStore.isInitiator"
          type="primary"
          class="!bg-love !border-love"
          @click="$router.push('/projects/create')"
        >
          <el-icon class="mr-1"><Plus /></el-icon>
          立即发起
        </el-button>
      </el-empty>

      <el-table
        v-else
        :data="filteredProjects"
        border
        stripe
        style="width: 100%"
        class="card-shadow rounded-xl overflow-hidden"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column label="项目信息" min-width="280">
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
              <div class="min-w-0">
                <p
                  class="font-semibold text-gray-800 truncate cursor-pointer hover:text-love transition-colors"
                  @click="goToDetail(row.id)"
                >
                  {{ row.title }}
                </p>
                <div class="flex items-center gap-2 mt-1">
                  <el-tag size="small" type="warning">{{ row.category_display }}</el-tag>
                  <span class="text-xs text-gray-400">{{ formatDateTime(row.created_at) }}</span>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="筹款进度" min-width="200">
          <template #default="{ row }">
            <div class="py-1">
              <div class="flex justify-between text-xs mb-1">
                <span>
                  <span class="text-love font-bold">¥{{ formatNumber(row.current_amount) }}</span>
                  <span class="text-gray-400"> / ¥{{ formatNumber(row.target_amount) }}</span>
                </span>
                <span class="text-love font-semibold">{{ row.progress_percentage }}%</span>
              </div>
              <el-progress
                :percentage="row.progress_percentage"
                :stroke-width="8"
                :show-text="false"
                color="#e11d48"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="dark">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="截止日期" width="140" align="center">
          <template #default="{ row }">
            {{ formatDate(row.deadline) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="default"
              @click="goToDetail(row.id)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无数据" />
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getMyProjects } from '@/api/projects'
import type { Project } from '@/types'
import { PROJECT_STATUS_OPTIONS } from '@/types'
import { FolderOpened, Plus, Collection } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const projects = ref<Project[]>([])
const activeStatus = ref('')

const filteredProjects = computed(() => {
  if (!activeStatus.value) return projects.value
  return projects.value.filter(p => p.status === activeStatus.value)
})

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await getMyProjects()
    projects.value = res
  } catch (error) {
    console.error('Fetch my projects error:', error)
  } finally {
    loading.value = false
  }
}

const statusTagType = (status: string) => {
  switch (status) {
    case 'funding': return 'success'
    case 'completed': return 'info'
    case 'approved': return 'primary'
    case 'rejected': return 'danger'
    default: return 'warning'
  }
}

const goToDetail = (id: number) => {
  router.push(`/projects/${id}`)
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
