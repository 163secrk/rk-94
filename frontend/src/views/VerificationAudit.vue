<template>
  <div class="max-w-7xl mx-auto">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-800 flex items-center">
        <el-icon class="text-love mr-2"><DocumentChecked /></el-icon>
        实名认证审核
      </h2>
      <p class="text-gray-500 mt-1">审核用户实名认证申请，确保用户信息真实有效</p>
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
        :data="verifications"
        border
        stripe
        style="width: 100%"
        class="bg-white card-shadow rounded-xl overflow-hidden"
      >
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="用户信息" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center py-1">
              <el-avatar :size="40" class="bg-love mr-3 flex-shrink-0">
                {{ row.user?.username?.charAt(0).toUpperCase() }}
              </el-avatar>
              <div class="min-w-0 flex-1">
                <p class="font-semibold text-gray-800 truncate">{{ row.user?.username }}</p>
                <p class="text-xs text-gray-400">{{ row.user?.email }}</p>
                <el-tag size="small" type="primary" class="mt-1">{{ row.user?.role_display }}</el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="认证类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.profile_type === 'personal' ? 'primary' : 'warning'">
              {{ row.profile_type_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="真实姓名" width="150">
          <template #default="{ row }">
            {{ row.real_name }}
          </template>
        </el-table-column>
        <el-table-column label="证件号码" width="200">
          <template #default="{ row }">
            {{ maskIdCard(row.id_card) }}
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.submitted_at) }}
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
      v-model="detailDialogVisible"
      title="实名认证详情"
      width="700px"
    >
      <div v-if="currentVerification" class="space-y-4">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户名">
            {{ currentVerification.user?.username }}
          </el-descriptions-item>
          <el-descriptions-item label="用户角色">
            {{ currentVerification.user?.role_display }}
          </el-descriptions-item>
          <el-descriptions-item label="认证类型">
            <el-tag :type="currentVerification.profile_type === 'personal' ? 'primary' : 'warning'">
              {{ currentVerification.profile_type_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="审核状态">
            <el-tag :type="statusTagType(currentVerification.status)" effect="dark">
              {{ currentVerification.status_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="真实姓名/企业名称" :span="2">
            {{ currentVerification.real_name }}
          </el-descriptions-item>
          <el-descriptions-item label="证件号码" :span="2">
            {{ currentVerification.id_card }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentVerification.profile_type === 'enterprise'" label="企业法人" :span="2">
            {{ currentVerification.enterprise_legal_person }}
          </el-descriptions-item>
          <el-descriptions-item label="提交时间" :span="2">
            {{ formatDateTime(currentVerification.submitted_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentVerification.verified_at" label="审核时间" :span="2">
            {{ formatDateTime(currentVerification.verified_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentVerification.reject_reason" label="拒绝原因" :span="2">
            <span class="text-red-500">{{ currentVerification.reject_reason }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentVerification.profile_type === 'personal'" class="space-y-4">
          <h4 class="font-semibold text-gray-700">证件照片</h4>
          <div class="flex gap-4 flex-wrap">
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-2">身份证正面</p>
              <el-image
                v-if="currentVerification.personal_id_front"
                :src="currentVerification.personal_id_front"
                :preview-src-list="[currentVerification.personal_id_front]"
                fit="cover"
                class="w-48 h-32 rounded-lg border border-gray-200"
              />
              <el-empty v-else description="暂无图片" :image-size="60" class="w-48 h-32" />
            </div>
            <div class="text-center">
              <p class="text-sm text-gray-500 mb-2">身份证反面</p>
              <el-image
                v-if="currentVerification.personal_id_back"
                :src="currentVerification.personal_id_back"
                :preview-src-list="[currentVerification.personal_id_back]"
                fit="cover"
                class="w-48 h-32 rounded-lg border border-gray-200"
              />
              <el-empty v-else description="暂无图片" :image-size="60" class="w-48 h-32" />
            </div>
          </div>
        </div>

        <div v-if="currentVerification.profile_type === 'enterprise'" class="space-y-4">
          <h4 class="font-semibold text-gray-700">企业营业执照</h4>
          <div class="text-center">
            <el-image
              v-if="currentVerification.enterprise_license"
              :src="currentVerification.enterprise_license"
              :preview-src-list="[currentVerification.enterprise_license]"
              fit="contain"
              class="w-64 h-40 rounded-lg border border-gray-200"
            />
            <el-empty v-else description="暂无图片" :image-size="80" class="w-64 h-40" />
          </div>
        </div>
      </div>

      <template #footer>
        <template v-if="currentVerification?.status === 'pending'">
          <el-button @click="detailDialogVisible = false">取消</el-button>
          <el-button type="success" @click="handleApprove(currentVerification!)">
            通过审核
          </el-button>
          <el-button type="danger" @click="handleReject(currentVerification!)">
            拒绝审核
          </el-button>
        </template>
        <template v-else>
          <el-button @click="detailDialogVisible = false">关闭</el-button>
        </template>
      </template>
    </el-dialog>

    <el-dialog
      v-model="auditDialogVisible"
      :title="`审核：${currentVerification?.real_name || ''}`"
      width="500px"
      :close-on-click-modal="false"
    >
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getVerificationList, auditVerification } from '@/api/auth'
import type { VerificationProfile, VerificationAuditForm } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DocumentChecked, Clock, CircleCheckFilled, CircleCloseFilled, InfoFilled,
  User
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const allVerifications = ref<VerificationProfile[]>([])
const verifications = computed(() => {
  if (activeStatus.value === 'all') return allVerifications.value
  return allVerifications.value.filter(p => p.status === activeStatus.value)
})
const activeStatus = ref('all')
const detailDialogVisible = ref(false)
const auditDialogVisible = ref(false)
const auditLoading = ref(false)
const currentVerification = ref<VerificationProfile | null>(null)
const auditFormRef = ref<FormInstance>()

const auditForm = reactive<VerificationAuditForm>({
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
  const all = allVerifications.value
  return [
    { key: 'pending', label: '待审核', count: all.filter(p => p.status === 'pending').length, color: 'text-yellow-500', bgColor: 'bg-yellow-50', icon: 'Clock' },
    { key: 'approved', label: '已通过', count: all.filter(p => p.status === 'approved').length, color: 'text-green-500', bgColor: 'bg-green-50', icon: 'CircleCheckFilled' },
    { key: 'rejected', label: '已拒绝', count: all.filter(p => p.status === 'rejected').length, color: 'text-red-500', bgColor: 'bg-red-50', icon: 'CircleCloseFilled' },
    { key: 'all', label: '全部', count: all.length, color: 'text-love', bgColor: 'bg-love-50', icon: 'DocumentChecked' },
  ]
})

const fetchVerifications = async () => {
  loading.value = true
  try {
    const res = await getVerificationList('all')
    allVerifications.value = res
  } catch (error) {
    console.error('Fetch verification list error:', error)
  } finally {
    loading.value = false
  }
}

const statusTagType = (status: string) => {
  switch (status) {
    case 'approved': return 'success'
    case 'rejected': return 'danger'
    default: return 'warning'
  }
}

const viewDetail = (row: VerificationProfile) => {
  currentVerification.value = row
  detailDialogVisible.value = true
}

const handleApprove = (row: VerificationProfile) => {
  currentVerification.value = row
  auditForm.status = 'approved'
  auditForm.reject_reason = ''
  auditDialogVisible.value = true
}

const handleReject = (row: VerificationProfile) => {
  currentVerification.value = row
  auditForm.status = 'rejected'
  auditForm.reject_reason = ''
  auditDialogVisible.value = true
}

const submitAudit = async () => {
  if (!currentVerification.value || !auditFormRef.value) return
  try {
    await auditFormRef.value.validate()
  } catch (error) {
    return
  }

  try {
    auditLoading.value = true
    await auditVerification(currentVerification.value.id, { ...auditForm })
    ElMessage.success(auditForm.status === 'approved' ? '实名认证已通过审核' : '实名认证已拒绝')
    auditDialogVisible.value = false
    detailDialogVisible.value = false
    await fetchVerifications()
  } catch (error: any) {
    console.error('Audit error:', error)
    ElMessage.error(error?.response?.data?.message || '审核操作失败')
  } finally {
    auditLoading.value = false
  }
}

const maskIdCard = (id: string) => {
  if (!id || id.length < 8) return id
  return id.substring(0, 4) + '*'.repeat(id.length - 8) + id.substring(id.length - 4)
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchVerifications()
})
</script>
