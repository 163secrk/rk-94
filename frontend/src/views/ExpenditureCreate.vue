<template>
  <div class="max-w-3xl mx-auto" v-loading="loading">
    <el-page-header
      class="mb-6"
      content="返回支出记录"
      @back="$router.push('/expenditures')"
    />

    <div class="bg-white rounded-xl p-8 card-shadow">
      <h1 class="text-2xl font-bold text-gray-800 mb-6">登记支出</h1>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        label-position="top"
      >
        <el-form-item label="所属项目" prop="project">
          <el-select
            v-model="form.project"
            placeholder="请选择项目"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.title"
              :value="project.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="支出类型" prop="expenditure_type">
          <el-select
            v-model="form.expenditure_type"
            placeholder="请选择支出类型"
            style="width: 100%"
          >
            <el-option
              v-for="item in EXPENDITURE_TYPE_OPTIONS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="支出标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入支出标题，如：购买医疗物资"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="支出说明" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请详细描述支出用途"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <el-form-item label="支出金额（元）" prop="amount">
            <el-input-number
              v-model="form.amount"
              :min="0.01"
              :precision="2"
              :step="100"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="支出日期" prop="expenditure_date">
            <el-date-picker
              v-model="form.expenditure_date"
              type="date"
              placeholder="选择支出日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </div>

        <el-form-item label="收款方/接收人" prop="recipient">
          <el-input
            v-model="form.recipient"
            placeholder="请输入收款方名称或接收人姓名"
            maxlength="200"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="2"
            placeholder="选填"
            maxlength="500"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="!bg-love !border-love hover:!bg-love-dark"
            :loading="submitting"
            @click="submitForm"
          >
            提交支出记录
          </el-button>
          <el-button size="large" @click="$router.push('/expenditures')">
            取消
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createExpenditure, getPendingProjects } from '@/api/projects'
import type { ExpenditureCreateForm, Project } from '@/types'
import { EXPENDITURE_TYPE_OPTIONS } from '@/types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const projects = ref<Project[]>([])

const form = reactive<ExpenditureCreateForm>({
  project: 0,
  expenditure_type: 'material',
  title: '',
  description: '',
  amount: 0,
  expenditure_date: new Date().toISOString().split('T')[0],
  recipient: '',
  remark: ''
})

const rules: FormRules = {
  project: [
    { required: true, message: '请选择所属项目', trigger: 'change' }
  ],
  expenditure_type: [
    { required: true, message: '请选择支出类型', trigger: 'change' }
  ],
  title: [
    { required: true, message: '请输入支出标题', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入支出说明', trigger: 'blur' }
  ],
  amount: [
    { required: true, message: '请输入支出金额', trigger: 'blur' }
  ],
  expenditure_date: [
    { required: true, message: '请选择支出日期', trigger: 'change' }
  ],
  recipient: [
    { required: true, message: '请输入收款方/接收人', trigger: 'blur' }
  ]
}

const fetchProjects = async () => {
  loading.value = true
  try {
    const data = await getPendingProjects('all')
    projects.value = data.filter(p => p.status === 'executing' || p.status === 'completed')
  } catch (error) {
    console.error('Fetch projects error:', error)
  } finally {
    loading.value = false
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate()

  submitting.value = true
  try {
    const expenditure = await createExpenditure({
      ...form,
      remark: form.remark || undefined
    })
    ElMessage.success('支出记录创建成功')
    router.push(`/expenditures/${expenditure.id}`)
  } catch (error) {
    console.error('Create expenditure error:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchProjects()
})
</script>
