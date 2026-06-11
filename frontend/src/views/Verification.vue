<template>
  <div class="max-w-3xl mx-auto">
    <div class="bg-white rounded-xl p-6 card-shadow mb-6">
      <h2 class="text-2xl font-bold text-gray-800 mb-2 flex items-center">
        <el-icon class="text-love mr-2 text-3xl"><DocumentChecked /></el-icon>
        实名认证
      </h2>
      <p class="text-gray-500">完成实名认证后，您可以参与更多公益项目</p>
    </div>

    <div v-if="profile" class="bg-white rounded-xl p-6 card-shadow mb-6">
      <el-result
        :title="statusTitle"
        :sub-title="statusSubtitle"
        :status="resultStatus"
      >
        <template #icon>
          <el-icon :class="statusIconClass" class="text-6xl">
            <component :is="statusIcon" />
          </el-icon>
        </template>
        <template #extra>
          <div class="text-left space-y-3">
            <div class="flex items-center space-x-4">
              <span class="text-gray-500 w-24">认证类型：</span>
              <el-tag :type="profile.profile_type === 'personal' ? 'primary' : 'warning'" size="large">
                {{ profile.profile_type_display }}
              </el-tag>
            </div>
            <div class="flex items-center space-x-4">
              <span class="text-gray-500 w-24">{{ profile.profile_type === 'personal' ? '真实姓名' : '企业名称' }}：</span>
              <span class="font-medium">{{ profile.real_name }}</span>
            </div>
            <div class="flex items-center space-x-4">
              <span class="text-gray-500 w-24">{{ profile.profile_type === 'personal' ? '身份证号' : '统一社会信用代码' }}：</span>
              <span class="font-medium">{{ maskIdCard(profile.id_card) }}</span>
            </div>
            <div v-if="profile.reject_reason" class="flex items-start space-x-4">
              <span class="text-gray-500 w-24">拒绝原因：</span>
              <span class="text-red-500">{{ profile.reject_reason }}</span>
            </div>
            <div class="flex items-center space-x-4">
              <span class="text-gray-500 w-24">提交时间：</span>
              <span>{{ formatDate(profile.submitted_at) }}</span>
            </div>
            <div v-if="profile.verified_at" class="flex items-center space-x-4">
              <span class="text-gray-500 w-24">通过时间：</span>
              <span>{{ formatDate(profile.verified_at) }}</span>
            </div>
          </div>
          <div class="mt-6" v-if="canEdit">
            <el-button type="primary" size="large" class="!bg-love !border-love" @click="showForm = true">
              <el-icon class="mr-1"><Edit /></el-icon>
              重新提交
            </el-button>
          </div>
        </template>
      </el-result>
    </div>

    <div v-if="showForm || !profile" class="bg-white rounded-xl p-6 card-shadow">
      <h3 class="text-lg font-bold text-gray-800 mb-6">
        {{ profile && profile.status !== 'approved' ? '重新提交认证' : '提交认证信息' }}
      </h3>

      <el-radio-group v-model="formType" class="mb-6 w-full">
        <el-radio-button value="personal" class="w-1/2 text-center h-16">
          <div class="flex flex-col items-center justify-center py-2">
            <el-icon class="text-2xl mb-1"><User /></el-icon>
            <span>个人实名认证</span>
          </div>
        </el-radio-button>
        <el-radio-button value="enterprise" class="w-1/2 text-center h-16">
          <div class="flex flex-col items-center justify-center py-2">
            <el-icon class="text-2xl mb-1"><OfficeBuilding /></el-icon>
            <span>企业实名认证</span>
          </div>
        </el-radio-button>
      </el-radio-group>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <template v-if="formType === 'personal'">
          <el-form-item label="真实姓名" prop="real_name">
            <el-input
              v-model="formData.real_name"
              placeholder="请输入真实姓名"
              size="large"
            />
          </el-form-item>

          <el-form-item label="身份证号" prop="id_card">
            <el-input
              v-model="formData.id_card"
              placeholder="请输入18位身份证号"
              size="large"
              maxlength="18"
            />
          </el-form-item>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="身份证正面照片" prop="personal_id_front">
                <el-upload
                  v-model:file-list="idFrontFileList"
                  :auto-upload="false"
                  :limit="1"
                  list-type="picture-card"
                  accept="image/*"
                  :on-change="handleIdFrontChange"
                  :on-remove="() => handleRemoveFile('personal_id_front')"
                >
                  <el-icon><Plus /></el-icon>
                  <template #tip>
                    <div class="el-upload__tip text-xs text-gray-500">
                      请上传身份证正面（国徽面）
                    </div>
                  </template>
                </el-upload>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="身份证反面照片" prop="personal_id_back">
                <el-upload
                  v-model:file-list="idBackFileList"
                  :auto-upload="false"
                  :limit="1"
                  list-type="picture-card"
                  accept="image/*"
                  :on-change="handleIdBackChange"
                  :on-remove="() => handleRemoveFile('personal_id_back')"
                >
                  <el-icon><Plus /></el-icon>
                  <template #tip>
                    <div class="el-upload__tip text-xs text-gray-500">
                      请上传身份证反面（头像面）
                    </div>
                  </template>
                </el-upload>
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <template v-else>
          <el-form-item label="企业名称" prop="real_name">
            <el-input
              v-model="formData.real_name"
              placeholder="请输入企业全称"
              size="large"
            />
          </el-form-item>

          <el-form-item label="统一社会信用代码" prop="id_card">
            <el-input
              v-model="formData.id_card"
              placeholder="请输入18位统一社会信用代码"
              size="large"
              maxlength="18"
            />
          </el-form-item>

          <el-form-item label="企业法人" prop="enterprise_legal_person">
            <el-input
              :model-value="(formData as any).enterprise_legal_person"
              @update:model-value="(val: string) => handleUpdateField('enterprise_legal_person', val)"
              placeholder="请输入企业法人姓名"
              size="large"
            />
          </el-form-item>

          <el-form-item label="企业营业执照" prop="enterprise_license">
            <el-upload
              v-model:file-list="licenseFileList"
              :auto-upload="false"
              :limit="1"
              list-type="picture-card"
              accept="image/*"
              :on-change="handleLicenseChange"
              :on-remove="() => handleRemoveFile('enterprise_license')"
            >
              <el-icon><Plus /></el-icon>
              <template #tip>
                <div class="el-upload__tip text-xs text-gray-500">
                  请上传企业营业执照照片
                </div>
              </template>
            </el-upload>
          </el-form-item>
        </template>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="w-full !bg-love !border-love hover:!bg-love-dark"
            :loading="loading"
            @click="handleSubmit"
          >
            <el-icon class="mr-1"><Check /></el-icon>
            提交认证
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getVerificationProfile, submitVerification } from '@/api/auth'
import type { FormInstance, FormRules, UploadFile, UploadFiles } from 'element-plus'
import type { VerificationProfile, PersonalVerificationForm, EnterpriseVerificationForm } from '@/types'
import { ElMessage } from 'element-plus'
import {
  DocumentChecked, Edit, User, OfficeBuilding, Plus, Check,
  InfoFilled, CircleCheckFilled, CircleCloseFilled, Clock
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const profile = ref<VerificationProfile | null>(null)
const showForm = ref(false)

const formType = ref<'personal' | 'enterprise'>('personal')

const idFrontFileList = ref<UploadFile[]>([])
const idBackFileList = ref<UploadFile[]>([])
const licenseFileList = ref<UploadFile[]>([])

const formData = reactive<PersonalVerificationForm | EnterpriseVerificationForm>({
  profile_type: 'personal',
  real_name: '',
  id_card: '',
  personal_id_front: null,
  personal_id_back: null,
  enterprise_license: null,
  enterprise_legal_person: '',
} as PersonalVerificationForm)

const personalRules: FormRules = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  id_card: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { pattern: /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/, message: '请输入正确的18位身份证号', trigger: 'blur' },
  ],
}

const enterpriseRules: FormRules = {
  real_name: [{ required: true, message: '请输入企业名称', trigger: 'blur' }],
  id_card: [
    { required: true, message: '请输入统一社会信用代码', trigger: 'blur' },
    { pattern: /^[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}$/, message: '请输入正确的18位统一社会信用代码', trigger: 'blur' },
  ],
  enterprise_legal_person: [{ required: true, message: '请输入企业法人姓名', trigger: 'blur' }],
}

const formRules = computed(() => {
  return formType.value === 'personal' ? personalRules : enterpriseRules
})

const resultStatus = computed(() => {
  if (!profile.value) return 'info'
  switch (profile.value.status) {
    case 'approved':
      return 'success'
    case 'rejected':
      return 'error'
    default:
      return 'warning'
  }
})

const statusIcon = computed(() => {
  if (!profile.value) return markRaw(InfoFilled)
  switch (profile.value.status) {
    case 'approved':
      return markRaw(CircleCheckFilled)
    case 'rejected':
      return markRaw(CircleCloseFilled)
    default:
      return markRaw(Clock)
  }
})

const statusIconClass = computed(() => {
  if (!profile.value) return 'text-blue-500'
  switch (profile.value.status) {
    case 'approved':
      return 'text-green-500'
    case 'rejected':
      return 'text-red-500'
    default:
      return 'text-yellow-500'
  }
})

const statusTitle = computed(() => {
  if (!profile.value) return ''
  switch (profile.value.status) {
    case 'approved':
      return '认证已通过'
    case 'rejected':
      return '认证已拒绝'
    default:
      return '认证审核中'
  }
})

const statusSubtitle = computed(() => {
  if (!profile.value) return ''
  switch (profile.value.status) {
    case 'approved':
      return '您的实名认证已通过，可以参与更多公益项目'
    case 'rejected':
      return '您的实名认证未通过，请检查信息后重新提交'
    default:
      return '您的实名认证正在审核中，请耐心等待'
  }
})

const canEdit = computed(() => {
  return profile.value && profile.value.status !== 'approved'
})

const fetchProfile = async () => {
  try {
    const res = await getVerificationProfile()
    profile.value = res
    if (res) {
      formType.value = res.profile_type
      formData.profile_type = res.profile_type
      formData.real_name = res.real_name
      formData.id_card = res.id_card
      if (res.profile_type === 'enterprise') {
        ;(formData as EnterpriseVerificationForm).enterprise_legal_person = res.enterprise_legal_person || ''
      }
    }
  } catch (error) {
    console.error('Fetch verification profile error:', error)
  }
}

const handleFileChange = (file: UploadFile, field: string) => {
  ;(formData as any)[field] = file.raw || null
}

const handleIdFrontChange = (file: UploadFile | UploadFile[]) => {
  const f = Array.isArray(file) ? file[0] : file
  ;(formData as PersonalVerificationForm).personal_id_front = f?.raw || null
}

const handleIdBackChange = (file: UploadFile | UploadFile[]) => {
  const f = Array.isArray(file) ? file[0] : file
  ;(formData as PersonalVerificationForm).personal_id_back = f?.raw || null
}

const handleLicenseChange = (file: UploadFile | UploadFile[]) => {
  const f = Array.isArray(file) ? file[0] : file
  ;(formData as EnterpriseVerificationForm).enterprise_license = f?.raw || null
}

const handleRemoveFile = (field: string) => {
  ;(formData as any)[field] = null
}

const handleUpdateField = (field: string, value: any) => {
  ;(formData as any)[field] = value
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  try {
    loading.value = true
    const formDataToSend = new FormData()
    
    formDataToSend.append('profile_type', formType.value)
    formDataToSend.append('real_name', formData.real_name)
    formDataToSend.append('id_card', formData.id_card)

    if (formType.value === 'personal') {
      const personalForm = formData as PersonalVerificationForm
      if (personalForm.personal_id_front) {
        formDataToSend.append('personal_id_front', personalForm.personal_id_front)
      }
      if (personalForm.personal_id_back) {
        formDataToSend.append('personal_id_back', personalForm.personal_id_back)
      }
    } else {
      const enterpriseForm = formData as EnterpriseVerificationForm
      formDataToSend.append('enterprise_legal_person', enterpriseForm.enterprise_legal_person)
      if (enterpriseForm.enterprise_license) {
        formDataToSend.append('enterprise_license', enterpriseForm.enterprise_license)
      }
    }

    const res = await submitVerification(formDataToSend)
    profile.value = res
    showForm.value = false
    
    if (res.status === 'approved') {
      userStore.updateVerificationStatus(true)
    }
    
    ElMessage.success('提交成功')
    await fetchProfile()
  } catch (error) {
    console.error('Submit verification error:', error)
  } finally {
    loading.value = false
  }
}

const maskIdCard = (id: string) => {
  if (!id || id.length < 8) return id
  return id.substring(0, 4) + '*'.repeat(id.length - 8) + id.substring(id.length - 4)
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchProfile()
})
</script>
