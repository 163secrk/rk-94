<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm border-b border-gray-100">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center space-x-3 cursor-pointer" @click="$router.push('/')">
            <div class="text-love text-3xl love-heart">
              <span class="inline-block">❤️</span>
            </div>
            <div>
              <h1 class="text-xl font-bold text-gray-800">爱心汇</h1>
              <p class="text-xs text-gray-500">LoveHub 捐赠管理平台</p>
            </div>
          </div>

          <nav class="hidden md:flex items-center space-x-8">
            <router-link
              v-for="item in menuItems"
              :key="item.path"
              :to="item.path"
              class="text-gray-600 hover:text-love transition-colors duration-200 font-medium"
              :class="{ 'text-love': $route.path === item.path || $route.path.startsWith(item.path + '/') }"
            >
              <el-icon class="mr-1"><component :is="item.icon" /></el-icon>
              {{ item.name }}
            </router-link>
          </nav>

          <div class="flex items-center space-x-4">
            <el-dropdown @command="handleCommand">
              <div class="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 px-3 py-2 rounded-lg transition-colors">
                <el-avatar :size="32" class="bg-love">
                  {{ userStore.userInfo?.username?.charAt(0).toUpperCase() }}
                </el-avatar>
                <div class="hidden sm:block">
                  <p class="text-sm font-medium text-gray-700">{{ userStore.userInfo?.username }}</p>
                  <p class="text-xs text-gray-500">{{ userStore.userInfo?.role_display }}</p>
                </div>
                <el-icon class="text-gray-400"><CaretBottom /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人中心
                  </el-dropdown-item>
                  <el-dropdown-item command="verification" v-if="userStore.isDonor">
                    <el-icon><DocumentChecked /></el-icon>
                    实名认证
                    <el-tag v-if="userStore.isVerified" type="success" size="small" class="ml-2">已认证</el-tag>
                    <el-tag v-else type="warning" size="small" class="ml-2">未认证</el-tag>
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <footer class="bg-white border-t border-gray-100 mt-auto">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div class="flex items-center space-x-2 mb-4 md:mb-0">
            <span class="text-love text-xl">❤️</span>
            <span class="text-gray-600 font-medium">爱心汇 LoveHub</span>
          </div>
          <p class="text-gray-500 text-sm">© 2024 爱心汇捐赠管理平台. 让爱心传递更远</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  CaretBottom, User, DocumentChecked, SwitchButton,
  HomeFilled, UserFilled, CirclePlusFilled, FolderOpened, CircleCheckFilled,
  Money, Goods
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const menuItems = computed(() => {
  const items = [
    { path: '/', name: '公益项目', icon: 'HomeFilled' },
    { path: '/dashboard', name: '个人中心', icon: 'UserFilled' },
    { path: '/verification', name: '实名认证', icon: 'DocumentChecked' },
    { path: '/expenditures', name: '支出记录', icon: 'Money' },
  ]
  if (userStore.isInitiator) {
    items.splice(1, 0, { path: '/projects/create', name: '发起项目', icon: 'CirclePlusFilled' })
    items.splice(2, 0, { path: '/projects/my', name: '我的项目', icon: 'FolderOpened' })
  }
  if (userStore.isAuditor) {
    items.splice(1, 0, { path: '/projects/audit', name: '项目审核', icon: 'CircleCheckFilled' })
    items.splice(2, 0, { path: '/verification/audit', name: '认证审核', icon: 'DocumentChecked' })
    items.splice(3, 0, { path: '/expenditures/create', name: '登记支出', icon: 'Goods' })
  }
  return items
})

const handleCommand = (command: string) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(() => {
      userStore.logout()
    }).catch(() => {})
  } else if (command === 'verification') {
    router.push('/verification')
  } else if (command === 'profile') {
    router.push('/dashboard')
  }
}

onMounted(async () => {
  try {
    await userStore.fetchUserInfo()
  } catch {
    // fetchUserInfo 内部已处理错误
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
