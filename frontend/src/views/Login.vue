<template>
  <div class="min-h-screen gradient-bg flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-white rounded-full shadow-lg mb-4">
          <span class="text-love text-4xl love-heart inline-block">❤️</span>
        </div>
        <h1 class="text-3xl font-bold text-gray-800 mb-2">爱心汇</h1>
        <p class="text-gray-600">LoveHub 捐赠管理平台</p>
      </div>

      <div class="bg-white rounded-2xl card-shadow p-8">
        <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">欢迎回来</h2>

        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            class="w-full !bg-love !border-love hover:!bg-love-dark !mt-2"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>

        <div class="mt-6 text-center">
          <p class="text-gray-600">
            还没有账号？
            <router-link to="/register" class="text-love hover:text-love-dark font-medium">
              立即注册
            </router-link>
          </p>
        </div>

        <el-divider content-position="center">
          <span class="text-gray-400 text-sm">测试账号</span>
        </el-divider>

        <div class="space-y-2 text-sm text-gray-500">
          <p><span class="font-medium">审核员：</span> admin / admin123456</p>
          <p class="text-xs text-gray-400">注册时可选择捐赠人或项目发起方角色</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const userStore = useUserStore()
const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const loginRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  try {
    const valid = await loginFormRef.value.validate()
    if (!valid) return
    loading.value = true
    await userStore.login(loginForm)
  } catch (error) {
    console.error('Login failed:', error)
  } finally {
    loading.value = false
  }
}
</script>
