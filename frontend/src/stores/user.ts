import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types'
import { login as apiLogin, logout as apiLogout, getUserInfo, register as apiRegister } from '@/api/auth'
import router from '@/router'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<User | null>(JSON.parse(localStorage.getItem('userInfo') || 'null'))

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const isDonor = computed(() => userInfo.value?.role === 'donor')
  const isInitiator = computed(() => userInfo.value?.role === 'initiator')
  const isAuditor = computed(() => userInfo.value?.role === 'auditor')
  const isVerified = computed(() => userInfo.value?.is_verified || false)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUserInfo = (info: User) => {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  const clearAuth = () => {
    token.value = null
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  const login = async (form: { username: string; password: string }) => {
    try {
      const res = await apiLogin(form)
      setToken(res.access)
      setUserInfo(res.user)
      ElMessage.success('登录成功')
      router.push('/')
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const register = async (form: any) => {
    try {
      await apiRegister(form)
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } catch (error) {
      console.error('Register error:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await apiLogout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
      ElMessage.success('已退出登录')
      router.push('/login')
    }
  }

  const fetchUserInfo = async () => {
    try {
      const res = await getUserInfo()
      setUserInfo(res)
      return res
    } catch (error) {
      console.error('Fetch user info error:', error)
      clearAuth()
      router.push('/login')
      throw error
    }
  }

  const updateVerificationStatus = (verified: boolean) => {
    if (userInfo.value) {
      userInfo.value.is_verified = verified
      localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isDonor,
    isInitiator,
    isAuditor,
    isVerified,
    login,
    register,
    logout,
    fetchUserInfo,
    updateVerificationStatus,
    clearAuth,
  }
})
