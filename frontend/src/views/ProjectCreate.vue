<template>
  <div class="max-w-4xl mx-auto">
    <div class="bg-white rounded-xl p-6 card-shadow mb-6">
      <h2 class="text-2xl font-bold text-gray-800 mb-2 flex items-center">
        <el-icon class="text-love mr-2 text-3xl"><CirclePlus /></el-icon>
        发起公益项目
      </h2>
      <p class="text-gray-500">填写项目信息和详细预算表，提交后将由平台审核员审核</p>
    </div>

    <div v-if="!userStore.isVerified" class="bg-white rounded-xl p-6 card-shadow mb-6">
      <el-result
        icon="warning"
        title="需要先完成实名认证"
        sub-title="根据平台规定，项目发起方必须先完成实名认证才能创建公益项目"
      >
        <template #extra>
          <el-button
            type="primary"
            size="large"
            class="!bg-love !border-love"
            @click="$router.push('/verification')"
          >
            <el-icon class="mr-1"><DocumentChecked /></el-icon>
            去实名认证
          </el-button>
        </template>
      </el-result>
    </div>

    <div v-else class="bg-white rounded-xl p-6 card-shadow">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <h3 class="text-lg font-bold text-gray-800 mb-4 pb-4 border-b border-gray-100">
          <el-icon class="text-love mr-1"><Document /></el-icon>
          基本信息
        </h3>

        <el-form-item label="项目标题" prop="title">
          <el-input
            v-model="formData.title"
            placeholder="请输入项目标题（200字以内）"
            size="large"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目分类" prop="category">
              <el-select
                v-model="formData.category"
                placeholder="请选择项目分类"
                size="large"
                class="w-full"
              >
                <el-option
                  v-for="cat in PROJECT_CATEGORY_OPTIONS"
                  :key="cat.value"
                  :label="cat.label"
                  :value="cat.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="截止日期" prop="deadline">
              <el-date-picker
                v-model="formData.deadline"
                type="date"
                placeholder="选择项目截止日期"
                size="large"
                class="w-full"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :disabled-date="disabledDate"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="目标金额（元）" prop="target_amount">
          <el-input-number
            v-model="formData.target_amount"
            :min="1"
            :precision="2"
            :step="100"
            placeholder="请输入筹款目标金额"
            size="large"
            class="w-full"
            controls-position="right"
          />
        </el-form-item>

        <el-form-item label="项目简介" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请简要描述您的公益项目（500字以内）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="详细内容" prop="detail_content">
          <el-input
            v-model="formData.detail_content"
            type="textarea"
            :rows="6"
            placeholder="请详细介绍项目背景、执行计划等内容"
          />
        </el-form-item>

        <el-form-item label="封面图片" prop="cover_image">
          <el-upload
            v-model:file-list="coverFileList"
            :auto-upload="false"
            :limit="1"
            list-type="picture-card"
            accept="image/*"
            :on-change="handleCoverChange"
            :on-remove="handleCoverRemove"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip text-xs text-gray-500 mt-2">
                请上传项目封面图片，支持 jpg/png 格式，建议尺寸 800x600
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <div class="mt-8 mb-6 pb-4 border-b border-gray-100">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-bold text-gray-800">
              <el-icon class="text-love mr-1"><Money /></el-icon>
              资金用途分类预算表
            </h3>
            <el-button type="primary" size="default" class="!bg-love !border-love" @click="addBudget">
              <el-icon class="mr-1"><Plus /></el-icon>
              添加预算项
            </el-button>
          </div>
          <p class="text-gray-500 text-sm mt-2">请详细列出每一笔资金的用途，预算总和不能超过目标金额</p>
        </div>

        <div class="overflow-x-auto">
          <el-table :data="formData.budgets" border style="width: 100%" class="mb-4">
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column label="资金用途分类" min-width="140">
              <template #default="{ row, $index }">
                <el-form-item
                  :prop="`budgets.${$index}.category`"
                  :rules="budgetRules.category"
                  class="!mb-0"
                >
                  <el-input v-model="row.category" placeholder="如：物资采购" size="default" />
                </el-form-item>
              </template>
            </el-table-column>
            <el-table-column label="用途说明" min-width="180">
              <template #default="{ row }">
                <el-input v-model="row.description" placeholder="详细说明" size="default" />
              </template>
            </el-table-column>
            <el-table-column label="单价（元）" width="140">
              <template #default="{ row, $index }">
                <el-form-item
                  :prop="`budgets.${$index}.amount`"
                  :rules="budgetRules.amount"
                  class="!mb-0"
                >
                  <el-input-number
                    v-model="row.amount"
                    :min="0.01"
                    :precision="2"
                    :step="10"
                    size="default"
                    class="w-full"
                    controls-position="right"
                  />
                </el-form-item>
              </template>
            </el-table-column>
            <el-table-column label="数量" width="110">
              <template #default="{ row, $index }">
                <el-form-item
                  :prop="`budgets.${$index}.quantity`"
                  :rules="budgetRules.quantity"
                  class="!mb-0"
                >
                  <el-input-number
                    v-model="row.quantity"
                    :min="1"
                    :precision="0"
                    :step="1"
                    size="default"
                    class="w-full"
                    controls-position="right"
                  />
                </el-form-item>
              </template>
            </el-table-column>
            <el-table-column label="单位" width="100">
              <template #default="{ row }">
                <el-input v-model="row.unit" placeholder="如：件/个" size="default" />
              </template>
            </el-table-column>
            <el-table-column label="小计（元）" width="130" align="right">
              <template #default="{ row }">
                <span class="font-semibold text-gray-800">¥{{ calcSubtotal(row) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ $index }">
                <el-button
                  type="danger"
                  :icon="Delete"
                  circle
                  size="small"
                  :disabled="formData.budgets.length <= 1"
                  @click="removeBudget($index)"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="bg-gray-50 rounded-lg p-4 mb-6">
          <div class="flex items-center justify-between">
            <span class="text-gray-600 font-medium">预算总金额：</span>
            <div class="flex items-center gap-3">
              <span
                class="text-2xl font-bold"
                :class="isBudgetOverTarget ? 'text-red-500' : 'text-love'"
              >
                ¥{{ totalBudget }}
              </span>
              <span class="text-gray-400">/ 目标金额 ¥{{ formatNumber(formData.target_amount || 0) }}</span>
            </div>
          </div>
          <el-progress
            v-if="formData.target_amount"
            :percentage="budgetPercentage"
            :stroke-width="6"
            :show-text="false"
            :color="isBudgetOverTarget ? '#ef4444' : '#e11d48'"
            class="mt-3"
          />
          <p v-if="isBudgetOverTarget" class="text-red-500 text-sm mt-2">
            <el-icon class="mr-1"><WarningFilled /></el-icon>
            预算总金额已超过目标金额，请调整预算或提高目标金额
          </p>
        </div>

        <el-divider />

        <el-form-item>
          <div class="flex items-center justify-end gap-4">
            <el-button size="large" @click="$router.back()">
              取消
            </el-button>
            <el-button
              type="primary"
              size="large"
              class="!bg-love !border-love hover:!bg-love-dark"
              :loading="loading"
              :disabled="isBudgetOverTarget"
              @click="handleSubmit"
            >
              <el-icon class="mr-1"><Check /></el-icon>
              提交审核
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { createProject } from '@/api/projects'
import type { FormInstance, FormRules, UploadFile, UploadFiles } from 'element-plus'
import type { ProjectBudget, ProjectCategory, ProjectCreateForm } from '@/types'
import { PROJECT_CATEGORY_OPTIONS } from '@/types'
import { ElMessage } from 'element-plus'
import {
  CirclePlus, DocumentChecked, Document, Money, Plus, Delete, Check, WarningFilled
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const coverFileList = ref<UploadFile[]>([])

const formData = reactive<ProjectCreateForm>({
  title: '',
  category: 'education' as ProjectCategory,
  description: '',
  detail_content: '',
  cover_image: null,
  target_amount: '',
  deadline: '',
  budgets: [
    { category: '', description: '', amount: 0, quantity: 1, unit: '' },
  ] as ProjectBudget[],
})

const formRules: FormRules = {
  title: [
    { required: true, message: '请输入项目标题', trigger: 'blur' },
    { min: 5, max: 200, message: '标题长度在 5 到 200 个字符', trigger: 'blur' },
  ],
  category: [{ required: true, message: '请选择项目分类', trigger: 'change' }],
  deadline: [{ required: true, message: '请选择截止日期', trigger: 'change' }],
  target_amount: [
    { required: true, message: '请输入目标金额', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && parseFloat(value) > 0) {
          callback()
        } else {
          callback(new Error('目标金额必须大于0'))
        }
      },
      trigger: 'blur',
    },
  ],
  description: [
    { required: true, message: '请输入项目简介', trigger: 'blur' },
    { min: 10, max: 500, message: '简介长度在 10 到 500 个字符', trigger: 'blur' },
  ],
}

const budgetRules = {
  category: [{ required: true, message: '请填写用途分类', trigger: 'blur' }],
  amount: [
    { required: true, message: '请填写金额', trigger: 'blur' },
    {
      validator: (_rule: any, value: any, callback: any) => {
        if (value && parseFloat(value) > 0) {
          callback()
        } else {
          callback(new Error('金额必须大于0'))
        }
      },
      trigger: 'blur',
    },
  ],
  quantity: [
    { required: true, message: '请填写数量', trigger: 'blur' },
    {
      validator: (_rule: any, value: any, callback: any) => {
        if (value && parseInt(value) > 0) {
          callback()
        } else {
          callback(new Error('数量必须大于0'))
        }
      },
      trigger: 'blur',
    },
  ],
}

const totalBudget = computed(() => {
  const total = formData.budgets.reduce((sum, b) => {
    const amount = parseFloat(String(b.amount || 0))
    const quantity = parseInt(String(b.quantity || 0))
    return sum + amount * quantity
  }, 0)
  return formatNumber(total)
})

const budgetPercentage = computed(() => {
  const target = parseFloat(String(formData.target_amount || 0))
  if (target <= 0) return 0
  const total = formData.budgets.reduce((sum, b) => {
    const amount = parseFloat(String(b.amount || 0))
    const quantity = parseInt(String(b.quantity || 0))
    return sum + amount * quantity
  }, 0)
  return Math.min(100, Math.round((total / target) * 100))
})

const isBudgetOverTarget = computed(() => {
  const target = parseFloat(String(formData.target_amount || 0))
  if (target <= 0) return false
  const total = formData.budgets.reduce((sum, b) => {
    const amount = parseFloat(String(b.amount || 0))
    const quantity = parseInt(String(b.quantity || 0))
    return sum + amount * quantity
  }, 0)
  return total > target
})

const addBudget = () => {
  formData.budgets.push({
    category: '',
    description: '',
    amount: 0,
    quantity: 1,
    unit: '',
  })
}

const removeBudget = (index: number) => {
  if (formData.budgets.length > 1) {
    formData.budgets.splice(index, 1)
  }
}

const calcSubtotal = (row: ProjectBudget) => {
  const amount = parseFloat(String(row.amount || 0))
  const quantity = parseInt(String(row.quantity || 0))
  return formatNumber(amount * quantity)
}

const disabledDate = (time: Date) => {
  return time.getTime() < Date.now() - 24 * 60 * 60 * 1000
}

const handleCoverChange = (file: UploadFile | UploadFile[]) => {
  const f = Array.isArray(file) ? file[0] : file
  formData.cover_image = f?.raw || null
}

const handleCoverRemove = () => {
  formData.cover_image = null
}

const formatNumber = (num: string | number) => {
  const n = typeof num === 'string' ? parseFloat(num) : num
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  if (formData.budgets.length === 0) {
    ElMessage.warning('请至少添加一条预算明细')
    return
  }

  try {
    loading.value = true
    const formDataToSend = new FormData()

    formDataToSend.append('title', formData.title)
    formDataToSend.append('category', formData.category)
    formDataToSend.append('description', formData.description)
    formDataToSend.append('detail_content', formData.detail_content)
    formDataToSend.append('target_amount', String(formData.target_amount))
    formDataToSend.append('deadline', formData.deadline)

    if (formData.cover_image) {
      formDataToSend.append('cover_image', formData.cover_image)
    }

    formDataToSend.append('budgets', JSON.stringify(formData.budgets.map(b => ({
      category: b.category,
      description: b.description || '',
      amount: parseFloat(String(b.amount)),
      quantity: parseInt(String(b.quantity)),
      unit: b.unit || '',
    }))))

    await createProject(formDataToSend)
    ElMessage.success('项目提交成功，请等待平台审核')
    router.push('/projects/my')
  } catch (error: any) {
    console.error('Create project error:', error)
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error?.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}
</script>
