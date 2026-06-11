<template>
  <div class="max-w-5xl mx-auto" v-loading="loading">
    <el-page-header
      class="mb-6"
      content="返回项目列表"
      @back="$router.push('/')"
    />

    <template v-if="project">
      <div class="bg-white rounded-xl overflow-hidden card-shadow mb-6">
        <div class="relative h-80 bg-gradient-to-br from-gray-100 to-gray-200">
          <img
            v-if="project.cover_image"
            :src="project.cover_image"
            :alt="project.title"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-love-100 to-love-50">
            <el-icon class="text-9xl text-love opacity-60"><Collection /></el-icon>
          </div>
          <div class="absolute top-4 left-4 flex gap-2">
            <el-tag :type="statusTagType(project.status)" size="large" effect="dark">
              {{ project.status_display }}
            </el-tag>
            <el-tag type="warning" size="large">
              {{ project.category_display }}
            </el-tag>
          </div>
        </div>
      </div>

      <div v-if="project.status === 'rejected' && project.reject_reason" class="bg-red-50 border border-red-200 rounded-xl p-5 mb-6">
        <div class="flex items-start">
          <el-icon class="text-red-500 text-2xl mr-3 mt-0.5"><WarningFilled /></el-icon>
          <div>
            <h4 class="text-red-700 font-bold mb-1">项目审核未通过</h4>
            <p class="text-red-600">拒绝原因：{{ project.reject_reason }}</p>
          </div>
        </div>
      </div>

      <div v-if="project.status === 'pending'" class="bg-yellow-50 border border-yellow-200 rounded-xl p-5 mb-6">
        <div class="flex items-start">
          <el-icon class="text-yellow-500 text-2xl mr-3 mt-0.5"><Clock /></el-icon>
          <div>
            <h4 class="text-yellow-700 font-bold mb-1">项目审核中</h4>
            <p class="text-yellow-600">您的项目正在等待平台审核员审核，审核通过后将在公开展示</p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 space-y-6">
          <div class="bg-white rounded-xl p-6 card-shadow">
            <h1 class="text-2xl font-bold text-gray-800 mb-4">{{ project.title }}</h1>
            <div class="flex items-center gap-6 text-sm text-gray-500 mb-6">
              <div class="flex items-center">
                <el-avatar :size="28" class="bg-love mr-2">
                  {{ project.initiator.username?.charAt(0).toUpperCase() }}
                </el-avatar>
                <span>{{ project.initiator.username }}</span>
              </div>
              <div class="flex items-center">
                <el-icon class="mr-1"><Calendar /></el-icon>
                截止：{{ formatDate(project.deadline) }}
              </div>
              <div class="flex items-center">
                <el-icon class="mr-1"><Timer /></el-icon>
                {{ formatDateTime(project.created_at) }}
              </div>
            </div>

            <div class="bg-gray-50 rounded-lg p-4 mb-6">
              <h4 class="text-gray-700 font-semibold mb-2">项目简介</h4>
              <p class="text-gray-600 leading-relaxed">{{ project.description }}</p>
            </div>

            <div v-if="project.detail_content">
              <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center">
                <el-icon class="text-love mr-2"><Document /></el-icon>
                详细内容
              </h3>
              <div class="text-gray-600 leading-relaxed whitespace-pre-wrap">
                {{ project.detail_content }}
              </div>
            </div>
          </div>

          <div class="bg-white rounded-xl p-6 card-shadow">
            <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center">
              <el-icon class="text-love mr-2"><Money /></el-icon>
              资金用途分类预算表
            </h3>
            <p class="text-gray-500 text-sm mb-4">预算总金额：<span class="text-love font-bold">¥{{ formatNumber(project.budget_total || 0) }}</span></p>

            <el-table :data="project.budgets" border stripe style="width: 100%">
              <el-table-column type="index" label="序号" width="70" align="center" />
              <el-table-column prop="category" label="用途分类" min-width="140" />
              <el-table-column prop="description" label="用途说明" min-width="200" />
              <el-table-column label="单价（元）" width="120" align="right">
                <template #default="{ row }">
                  ¥{{ formatNumber(row.amount) }}
                </template>
              </el-table-column>
              <el-table-column prop="quantity" label="数量" width="80" align="center" />
              <el-table-column prop="unit" label="单位" width="80" align="center" />
              <el-table-column label="小计（元）" width="140" align="right">
                <template #default="{ row }">
                  <span class="font-semibold text-love">¥{{ formatNumber(row.subtotal) }}</span>
                </template>
              </el-table-column>
            </el-table>

            <div class="mt-4 flex justify-end">
              <div class="bg-love-50 px-6 py-3 rounded-lg">
                <span class="text-gray-600 mr-4">预算合计：</span>
                <span class="text-2xl font-bold text-love">¥{{ formatNumber(project.budget_total || 0) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-white rounded-xl p-6 card-shadow sticky top-6">
            <h3 class="text-lg font-bold text-gray-800 mb-4">筹款进度</h3>

            <div class="mb-4">
              <div class="flex justify-between items-end mb-2">
                <div>
                  <span class="text-3xl font-bold text-love">¥{{ formatNumber(project.current_amount) }}</span>
                  <span class="text-gray-400 text-sm ml-1">已筹</span>
                </div>
                <span class="text-2xl font-bold text-gray-800">{{ project.progress_percentage }}%</span>
              </div>
              <el-progress
                :percentage="project.progress_percentage"
                :stroke-width="12"
                :show-text="false"
                color="#e11d48"
              />
            </div>

            <el-divider />

            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-gray-500">目标金额</span>
                <span class="font-semibold text-gray-800">¥{{ formatNumber(project.target_amount) }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-500">剩余金额</span>
                <span class="font-semibold text-gray-800">¥{{ formatNumber(remainingAmount) }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-500">截止日期</span>
                <span class="font-semibold text-gray-800">{{ formatDate(project.deadline) }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-500">剩余天数</span>
                <span
                  class="font-semibold"
                  :class="remainingDays <= 7 ? 'text-red-500' : 'text-gray-800'"
                >
                  {{ remainingDaysText }}
                </span>
              </div>
            </div>

            <el-button
              v-if="project.status === 'funding'"
              type="primary"
              size="large"
              class="w-full mt-6 h-14 !bg-love !border-love text-lg hover:!bg-love-dark"
              @click="openDonationDialog"
            >
              <el-icon class="mr-2 text-xl"><Cherry /></el-icon>
              立即捐赠
            </el-button>

            <el-button
              v-else-if="project.status === 'completed'"
              type="info"
              size="large"
              class="w-full mt-6 h-14"
              disabled
            >
              <el-icon class="mr-2 text-xl"><CircleCheck /></el-icon>
              项目已完成
            </el-button>

            <el-button
              v-else-if="project.status === 'pending'"
              type="warning"
              size="large"
              class="w-full mt-6 h-14"
              disabled
            >
              <el-icon class="mr-2 text-xl"><Clock /></el-icon>
              审核中，暂不可捐赠
            </el-button>

            <el-button
              v-else-if="project.status === 'rejected'"
              type="danger"
              size="large"
              class="w-full mt-6 h-14"
              disabled
            >
              <el-icon class="mr-2 text-xl"><CircleClose /></el-icon>
              项目未通过审核
            </el-button>
          </div>

          <div class="bg-white rounded-xl p-6 card-shadow">
            <h3 class="text-lg font-bold text-gray-800 mb-4">项目发起方</h3>
            <div class="flex items-center mb-4">
              <el-avatar :size="56" class="bg-love">
                {{ project.initiator.username?.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="ml-4">
                <p class="font-semibold text-gray-800">{{ project.initiator.username }}</p>
                <p class="text-gray-500 text-sm">{{ project.initiator.email }}</p>
              </div>
            </div>
            <el-tag type="success" effect="light">已实名认证</el-tag>
          </div>
        </div>
      </div>
    </template>

    <el-empty v-else-if="!loading" description="项目不存在或暂无权限查看" />

    <el-dialog
      v-model="donationDialogVisible"
      title="捐赠支持"
      width="500px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="donationFormRef"
        :model="donationForm"
        :rules="donationRules"
        label-width="100px"
        label-position="top"
      >
        <el-form-item label="捐赠金额（元）" prop="amount">
          <el-input-number
            v-model="donationForm.amount"
            :min="1"
            :max="remainingAmount"
            :precision="2"
            :step="10"
            controls-position="right"
            class="w-full"
            size="large"
          />
        </el-form-item>
        <div class="flex gap-2 mb-4">
          <el-button
            v-for="preset in presetAmounts"
            :key="preset"
            :type="donationForm.amount === preset ? 'primary' : 'default'"
            size="small"
            @click="donationForm.amount = preset"
          >
            ¥{{ preset }}
          </el-button>
        </div>
        <el-form-item label="留言（选填）" prop="message">
          <el-input
            v-model="donationForm.message"
            type="textarea"
            :rows="3"
            maxlength="200"
            show-word-limit
            placeholder="写下您的祝福或鼓励..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="donationDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="donationSubmitting"
          class="!bg-love !border-love hover:!bg-love-dark"
          @click="submitDonation"
        >
          确认捐赠 ¥{{ formatNumber(donationForm.amount) }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProjectDetail, createDonation, simulatePayment } from '@/api/projects'
import { useUserStore } from '@/stores/user'
import type { Project, DonationCreateForm } from '@/types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Collection, WarningFilled, Clock, Calendar, Timer, Document, Money,
  Cherry, CircleCheck, CircleClose
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const project = ref<Project | null>(null)

const donationDialogVisible = ref(false)
const donationSubmitting = ref(false)
const donationFormRef = ref<FormInstance>()
const donationForm = reactive<DonationCreateForm>({
  project: 0,
  amount: 50,
  message: '',
})

const presetAmounts = [10, 50, 100, 500]

const donationRules: FormRules = {
  amount: [
    { required: true, message: '请输入捐赠金额', trigger: 'blur' },
  ],
}

const remainingAmount = computed(() => {
  if (!project.value) return 0
  const target = parseFloat(String(project.value.target_amount))
  const current = parseFloat(String(project.value.current_amount))
  return Math.max(0, target - current)
})

const remainingDays = computed(() => {
  if (!project.value) return 0
  const deadline = new Date(project.value.deadline)
  const now = new Date()
  return Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
})

const remainingDaysText = computed(() => {
  if (remainingDays.value < 0) return '已截止'
  if (remainingDays.value === 0) return '今天截止'
  return `${remainingDays.value} 天`
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

const openDonationDialog = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再进行捐赠')
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  if (!project.value) return
  donationForm.project = project.value.id
  donationForm.amount = 50
  donationForm.message = ''
  donationDialogVisible.value = true
}

const submitDonation = async () => {
  if (!donationFormRef.value) return
  await donationFormRef.value.validate()

  donationSubmitting.value = true
  try {
    const res = await createDonation({
      project: donationForm.project,
      amount: donationForm.amount,
      message: donationForm.message || undefined,
    })
    donationDialogVisible.value = false

    const donation = res.donation
    const payRes = await simulatePayment(donation.id)
    if (payRes.status === 'paid') {
      ElMessage.success('支付成功，感谢您的捐赠！')
    } else {
      ElMessage.warning('支付未成功，请稍后重试')
    }
    fetchDetail()
  } catch (error) {
    console.error('Donation error:', error)
  } finally {
    donationSubmitting.value = false
  }
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const id = parseInt(route.params.id as string)
    const res = await getProjectDetail(id)
    project.value = res
  } catch (error) {
    console.error('Fetch project detail error:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>
