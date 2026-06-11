<template>
  <div class="min-h-screen gradient-bg flex items-center justify-center p-4 py-8">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-white rounded-full shadow-lg mb-4">
          <span class="text-love text-4xl love-heart inline-block">❤️</span>
        </div>
        <h1 class="text-3xl font-bold text-gray-800 mb-2">爱心汇</h1>
        <p class="text-gray-600">LoveHub 捐赠管理平台</p>
      </div>

      <div class="bg-white rounded-2xl card-shadow p-8">
        <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">创建账号</h2>

        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          label-position="top"
          @submit.prevent="handleRegister"
        >
          <el-form-item label="选择角色" prop="role">
            <el-radio-group v-model="registerForm.role" class="w-full">
              <el-radio-button value="donor" class="w-1/3 text-center">
                <el-icon class="mr-1"><UserFilled /></el-icon>
                捐赠人
              </el-radio-button>
              <el-radio-button value="initiator" class="w-1/3 text-center">
                <el-icon class="mr-1"><OfficeBuilding /></el-icon>
                发起方
              </el-radio-button>
              <el-radio-button value="auditor" class="w-1/3 text-center">
                <el-icon class="mr-1"><Avatar /></el-icon>
                审核员
              </el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱"
              size="large"
              :prefix-icon="Message"
            />
          </el-form-item>

          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="registerForm.phone"
              placeholder="请输入手机号"
              size="large"
              :prefix-icon="Phone"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码（至少6位）"
              size="large"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="registerForm.confirm_password"
              type="password"
              placeholder="请再次输入密码"
              size="large"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            class="w-full !bg-love !border-love hover:!bg-love-dark !mt-2"
            :loading="loading"
            @click="handleRegister"
          >
            注 册
          </el-button>
        </el-form>

        <div class="mt-6 text-center">
          <p class="text-gray-600">
            已有账号？
            <router-link to="/login" class="text-love hover:text-love-dark font-medium">
              立即登录
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock, Message, Phone, UserFilled, OfficeBuilding, Avatar } from '@element-plus/icons-vue'

const userStore = useUserStore()
const registerFormRef = ref<FormInstance>()
const loading = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm_password: '',
  role: 'donor' as 'donor' | 'initiator' | 'auditor',
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次密码输入不一致'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  try {
    const valid = await registerFormRef.value.validate()
    if (!valid) return
    loading.value = true
    await userStore.register(registerForm)
  } catch (error) {
    console.error('Register failed:', error)
  } finally {
    loading.value = false
  }
}
</script>
