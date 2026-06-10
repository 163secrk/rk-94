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
          <el-icon><HeartFilled /></el-icon>
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
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

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
    value: 0,
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

const quickActions = [
  {
    name: '实名认证',
    icon: 'DocumentChecked',
    path: '/verification',
    colorClass: 'from-love to-love-light hover:from-love-dark hover:to-love',
  },
  {
    name: '浏览项目',
    icon: 'Search',
    path: '/',
    colorClass: 'from-blue-500 to-blue-400 hover:from-blue-600 hover:to-blue-500',
  },
  {
    name: '发起项目',
    icon: 'Plus',
    path: '/',
    colorClass: 'from-green-500 to-green-400 hover:from-green-600 hover:to-green-500',
  },
  {
    name: '个人中心',
    icon: 'User',
    path: '/',
    colorClass: 'from-purple-500 to-purple-400 hover:from-purple-600 hover:to-purple-500',
  },
]

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

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>
