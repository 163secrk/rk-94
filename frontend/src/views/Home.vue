<template>
  <div class="space-y-8">
    <div class="bg-gradient-to-r from-love to-love-dark rounded-2xl p-8 text-white">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold mb-2">欢迎回来，{{ userStore.userInfo?.username }} 💕</h1>
          <p class="text-love-100 mb-4">
            您的角色：<span class="font-semibold">{{ userStore.userInfo?.role_display }}</span>
          </p>
          <div class="flex items-center space-x-4">
            <el-tag
              :type="userStore.isVerified ? 'success' : 'warning'"
              size="large"
              effect="light"
            >
              <el-icon class="mr-1">
                <component :is="userStore.isVerified ? 'CircleCheck' : 'Warning'" />
              </el-icon>
              {{ userStore.isVerified ? '已实名认证' : '未实名认证' }}
            </el-tag>
            <el-button
              v-if="!userStore.isVerified && userStore.isDonor"
              type="primary"
              size="default"
              class="!bg-white !text-love hover:!bg-love-50"
              @click="$router.push('/verification')"
            >
              立即认证
            </el-button>
          </div>
        </div>
        <div class="hidden md:block text-8xl love-heart opacity-80">
          <span>❤️</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div
        v-for="(stat, index) in stats"
        :key="index"
        class="bg-white rounded-xl p-6 card-shadow hover:shadow-lg transition-shadow duration-300"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-500 text-sm mb-1">{{ stat.label }}</p>
            <p class="text-3xl font-bold text-gray-800">{{ stat.value }}</p>
          </div>
          <div
            class="w-14 h-14 rounded-full flex items-center justify-center text-2xl"
            :class="stat.bgColor"
          >
            <el-icon :class="stat.iconColor">
              <component :is="stat.icon" />
            </el-icon>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-xl p-6 card-shadow">
        <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center">
          <el-icon class="text-love mr-2"><TrendCharts /></el-icon>
          快速操作
        </h3>
        <div class="grid grid-cols-2 gap-4">
          <el-button
            v-for="action in quickActions"
            :key="action.path"
            type="primary"
            size="large"
            class="h-20 !bg-gradient-to-r flex flex-col items-center justify-center space-y-1"
            :class="action.colorClass"
            @click="$router.push(action.path)"
          >
            <el-icon class="text-2xl"><component :is="action.icon" /></el-icon>
            <span>{{ action.name }}</span>
          </el-button>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 card-shadow">
        <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center">
          <el-icon class="text-love mr-2"><InfoFilled /></el-icon>
          系统提示
        </h3>
        <el-timeline>
          <el-timeline-item
            v-for="(tip, index) in tips"
            :key="index"
            :timestamp="tip.time"
            :type="tip.type"
          >
            {{ tip.content }}
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>

    <div v-if="userStore.isDonor" class="bg-white rounded-xl p-6 card-shadow">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-gray-800 flex items-center">
          <el-icon class="text-love mr-2"><Bell /></el-icon>
          我支持的项目最新动向
        </h3>
        <el-button
          type="primary"
          link
          class="!text-love"
          @click="refreshSupportedUpdates"
        >
          <el-icon class="mr-1"><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <div v-loading="updatesLoading" class="min-h-[200px]">
        <el-empty
          v-if="supportedUpdates.length === 0 && !updatesLoading"
          description="暂无项目动向，快去支持一个公益项目吧"
        >
          <el-button
            type="primary"
            class="!bg-love !border-love"
            @click="$router.push('/')"
          >
            浏览项目
          </el-button>
        </el-empty>

        <div v-else class="space-y-4">
          <div
            v-for="update in supportedUpdates"
            :key="update.id"
            class="p-4 bg-gray-50 rounded-xl hover:bg-love-50 transition-colors cursor-pointer"
            @click="goToUpdateDetail(update)"
          >
            <div class="flex items-start gap-4">
              <div
                class="w-14 h-14 rounded-lg overflow-hidden bg-gray-200 flex-shrink-0"
              >
                <img
                  v-if="update.project.cover_image"
                  :src="update.project.cover_image"
                  :alt="update.project.title"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex items-center justify-center bg-love-100">
                  <el-icon class="text-xl text-love opacity-60"><Collection /></el-icon>
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <el-tag size="small" :type="updateTypeTagType(update.update_type)">
                    {{ update.update_type_display }}
                  </el-tag>
                  <span class="text-xs text-gray-400">{{ formatDateTime(update.created_at) }}</span>
                </div>
                <h4 class="font-semibold text-gray-800 truncate mb-1">
                  {{ update.title }}
                </h4>
                <p class="text-sm text-gray-500 line-clamp-2">{{ update.content }}</p>
                <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
                  <span class="text-love font-medium">{{ update.project.title }}</span>
                  <span v-if="update.images_count > 0" class="flex items-center gap-1">
                    <el-icon><Picture /></el-icon>
                    {{ update.images_count }}张图片
                  </span>
                  <span v-if="update.videos_count > 0" class="flex items-center gap-1">
                    <el-icon><VideoCamera /></el-icon>
                    {{ update.videos_count }}个视频
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bg-white rounded-xl p-6 card-shadow">
      <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center">
        <el-icon class="text-love mr-2"><User /></el-icon>
        账户信息
      </h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">
          {{ userStore.userInfo?.username }}
        </el-descriptions-item>
        <el-descriptions-item label="邮箱">
          {{ userStore.userInfo?.email }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag type="primary">{{ userStore.userInfo?.role_display }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="手机号">
          {{ userStore.userInfo?.phone || '未设置' }}
        </el-descriptions-item>
        <el-descriptions-item label="实名认证">
          <el-tag :type="userStore.isVerified ? 'success' : 'warning'">
            {{ userStore.isVerified ? '已认证' : '未认证' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">
          {{ formatDate(userStore.userInfo?.date_joined) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getMySupportedProjectUpdates } from '@/api/projects'
import type { ProjectUpdate } from '@/types'
import {
  CircleCheck, Warning, Wallet, Files, Star,
  TrendCharts, InfoFilled, User, Search, Plus, FolderOpened,
  DocumentChecked, Bell, Refresh, Collection, Picture, VideoCamera
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const updatesLoading = ref(false)
const supportedUpdates = ref<ProjectUpdate[]>([])

const stats = computed(() => [
  {
    label: '累计捐赠',
    value: '¥ 0.00',
    icon: 'Wallet',
    bgColor: 'bg-love-50',
    iconColor: 'text-love',
  },
  {
    label: '参与项目',
    value: supportedUpdates.value.length > 0 ? new Set(supportedUpdates.value.map(u => u.project.id)).size : 0,
    icon: 'Files',
    bgColor: 'bg-blue-50',
    iconColor: 'text-blue-500',
  },
  {
    label: '爱心积分',
    value: 0,
    icon: 'Star',
    bgColor: 'bg-yellow-50',
    iconColor: 'text-yellow-500',
  },
])

const quickActions = computed(() => {
  const actions = [
    {
      name: '浏览项目',
      icon: 'Search',
      path: '/',
      colorClass: 'from-blue-500 to-blue-400 hover:from-blue-600 hover:to-blue-500',
    },
  ]

  if (userStore.isInitiator) {
    actions.splice(1, 0, {
      name: '发起项目',
      icon: 'Plus',
      path: '/projects/create',
      colorClass: 'from-green-500 to-green-400 hover:from-green-600 hover:to-green-500',
    })
    actions.splice(2, 0, {
      name: '我的项目',
      icon: 'FolderOpened',
      path: '/projects/my',
      colorClass: 'from-purple-500 to-purple-400 hover:from-purple-600 hover:to-purple-500',
    })
    actions.splice(3, 0, {
      name: '发布进展',
      icon: 'Bell',
      path: '/projects/updates/create',
      colorClass: 'from-orange-500 to-orange-400 hover:from-orange-600 hover:to-orange-500',
    })
  }

  if (userStore.isAuditor) {
    actions.splice(1, 0, {
      name: '项目审核',
      icon: 'CircleCheck',
      path: '/projects/audit',
      colorClass: 'from-orange-500 to-orange-400 hover:from-orange-600 hover:to-orange-500',
    })
    actions.splice(2, 0, {
      name: '认证审核',
      icon: 'DocumentChecked',
      path: '/verification/audit',
      colorClass: 'from-purple-500 to-purple-400 hover:from-purple-600 hover:to-purple-500',
    })
  }

  actions.push({
    name: '实名认证',
    icon: 'DocumentChecked',
    path: '/verification',
    colorClass: 'from-love to-love-light hover:from-love-dark hover:to-love',
  })

  return actions
})

const tips = [
  {
    time: '系统提示',
    content: '捐赠人完成实名认证后可参与更多公益项目',
    type: 'primary',
  },
  {
    time: '功能预告',
    content: '项目捐赠功能即将上线，敬请期待',
    type: 'success',
  },
  {
    time: '温馨提示',
    content: '请妥善保管您的账户密码，定期更换确保安全',
    type: 'warning',
  },
]

const updateTypeTagType = (type: string) => {
  switch (type) {
    case 'image': return 'success'
    case 'video': return 'warning'
    case 'mixed': return 'danger'
    default: return 'info'
  }
}

const goToUpdateDetail = (update: ProjectUpdate) => {
  if (update.project?.id) {
    router.push(`/projects/${update.project.id}?update=${update.id}`)
  }
}

const refreshSupportedUpdates = async () => {
  updatesLoading.value = true
  try {
    const res = await getMySupportedProjectUpdates()
    supportedUpdates.value = res
  } catch (error) {
    console.error('Fetch supported updates error:', error)
  } finally {
    updatesLoading.value = false
  }
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  if (userStore.isDonor) {
    refreshSupportedUpdates()
  }
})
</script>
