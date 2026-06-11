<template>
  <div class="space-y-6">
    <div class="bg-gradient-to-r from-love to-love-dark rounded-2xl p-8 text-white">
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <h1 class="text-3xl font-bold mb-2">公益项目广场 💕</h1>
          <p class="text-love-100">汇聚爱心，传递温暖，让每一份善意都有迹可循</p>
        </div>
        <div class="flex items-center gap-3">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索项目名称..."
            class="w-64"
            :prefix-icon="Search"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
          <el-button
            v-if="userStore.isInitiator"
            type="primary"
            size="large"
            class="!bg-white !text-love hover:!bg-love-50"
            @click="$router.push('/projects/create')"
          >
            <el-icon class="mr-1"><Plus /></el-icon>
            发起项目
          </el-button>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl p-4 card-shadow">
      <div class="flex flex-wrap items-center gap-3">
        <span class="text-gray-600 font-medium">分类：</span>
        <el-radio-group v-model="activeCategory" size="default" @change="handleCategoryChange">
          <el-radio-button value="">
            全部
          </el-radio-button>
          <el-radio-button
            v-for="cat in PROJECT_CATEGORY_OPTIONS"
            :key="cat.value"
            :value="cat.value"
          >
            {{ cat.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div v-loading="loading" class="min-h-[400px]">
      <div v-if="filteredProjects.length === 0 && !loading" class="bg-white rounded-xl p-16 card-shadow text-center">
        <el-icon class="text-8xl text-gray-300 mb-4"><Box /></el-icon>
        <p class="text-gray-500 text-lg">暂无公益项目</p>
        <el-button
          v-if="userStore.isInitiator"
          type="primary"
          size="large"
          class="mt-4 !bg-love !border-love"
          @click="$router.push('/projects/create')"
        >
          <el-icon class="mr-1"><Plus /></el-icon>
          成为第一个发起者
        </el-button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="project in filteredProjects"
          :key="project.id"
          class="bg-white rounded-xl overflow-hidden card-shadow hover:shadow-xl transition-all duration-300 cursor-pointer group"
          @click="goToDetail(project.id)"
        >
          <div class="relative h-48 bg-gradient-to-br from-gray-100 to-gray-200 overflow-hidden">
            <img
              v-if="project.cover_image"
              :src="project.cover_image"
              :alt="project.title"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
            <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-love-100 to-love-50">
              <el-icon class="text-7xl text-love opacity-60"><Collection /></el-icon>
            </div>
            <div class="absolute top-3 left-3">
              <el-tag :type="statusTagType(project.status)" size="large" effect="dark">
                {{ project.status_display }}
              </el-tag>
            </div>
            <div class="absolute top-3 right-3">
              <el-tag type="warning" size="large">
                {{ project.category_display }}
              </el-tag>
            </div>
          </div>

          <div class="p-5">
            <h3 class="text-lg font-bold text-gray-800 mb-2 line-clamp-1 group-hover:text-love transition-colors">
              {{ project.title }}
            </h3>
            <p class="text-gray-500 text-sm mb-4 line-clamp-2 h-10">
              {{ project.description }}
            </p>

            <div class="mb-3">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-500">筹款进度</span>
                <span class="text-love font-bold">{{ project.progress_percentage }}%</span>
              </div>
              <el-progress
                :percentage="project.progress_percentage"
                :stroke-width="8"
                :show-text="false"
                color="#e11d48"
              />
            </div>

            <div class="flex justify-between items-center text-sm">
              <div class="text-gray-600">
                <span class="text-love font-bold text-lg">¥{{ formatNumber(project.current_amount) }}</span>
                <span class="text-gray-400"> / ¥{{ formatNumber(project.target_amount) }}</span>
              </div>
            </div>

            <div class="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
              <div class="flex items-center">
                <el-icon class="mr-1"><User /></el-icon>
                {{ project.initiator.username }}
              </div>
              <div class="flex items-center">
                <el-icon class="mr-1"><Clock /></el-icon>
                {{ formatDeadline(project.deadline) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getPublicProjects } from '@/api/projects'
import type { Project } from '@/types'
import { PROJECT_CATEGORY_OPTIONS } from '@/types'
import { Search, Plus, Box, Collection, User, Clock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const projects = ref<Project[]>([])
const activeCategory = ref('')
const searchKeyword = ref('')

const filteredProjects = computed(() => {
  let result = projects.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(p =>
      p.title.toLowerCase().includes(keyword) ||
      p.description.toLowerCase().includes(keyword)
    )
  }
  return result
})

const fetchProjects = async (category?: string) => {
  loading.value = true
  try {
    const res = await getPublicProjects(category || undefined)
    projects.value = res
  } catch (error) {
    console.error('Fetch projects error:', error)
  } finally {
    loading.value = false
  }
}

const handleCategoryChange = () => {
  fetchProjects(activeCategory.value)
}

const handleSearch = () => {
  fetchProjects(activeCategory.value)
}

const statusTagType = (status: string) => {
  switch (status) {
    case 'funding': return 'success'
    case 'completed': return 'info'
    case 'approved': return 'primary'
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

const formatDeadline = (dateStr: string) => {
  const deadline = new Date(dateStr)
  const now = new Date()
  const diff = deadline.getTime() - now.getTime()
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24))
  if (days < 0) return '已截止'
  if (days === 0) return '今天截止'
  return `剩余${days}天`
}

onMounted(() => {
  fetchProjects()
})
</script>
