<template>
  <div class="max-w-7xl mx-auto" v-loading="loading">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800">支出记录</h1>
      <el-button
        v-if="userStore.isAuditor"
        type="primary"
        class="!bg-love !border-love hover:!bg-love-dark"
        @click="$router.push('/expenditures/create')"
      >
        <el-icon class="mr-1"><Plus /></el-icon>
        登记支出
      </el-button>
    </div>

    <div class="bg-white rounded-xl p-6 card-shadow mb-6">
      <div class="flex flex-wrap gap-4 items-center">
        <el-select
          v-model="filterType"
          placeholder="选择支出类型"
          clearable
          style="width: 200px"
          @change="fetchExpenditures"
        >
          <el-option
            v-for="item in EXPENDITURE_TYPE_OPTIONS"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-select
          v-model="filterProject"
          placeholder="选择项目"
          clearable
          filterable
          style="width: 300px"
          @change="fetchExpenditures"
        >
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.title"
            :value="project.id"
          />
        </el-select>
      </div>
    </div>

    <div v-if="expenditures.length > 0" class="space-y-4">
      <el-card
        v-for="exp in expenditures"
        :key="exp.id"
        class="card-shadow hover:shadow-lg transition-shadow cursor-pointer"
        @click="$router.push(`/expenditures/${exp.id}`)"
      >
        <div class="flex justify-between items-start">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="text-lg font-semibold text-gray-800">{{ exp.title }}</h3>
              <el-tag :type="expenditureTypeTagType(exp.expenditure_type)" size="small">
                {{ exp.expenditure_type_display }}
              </el-tag>
              <el-tag type="info" size="small">{{ exp.project_title }}</el-tag>
            </div>
            <p class="text-gray-600 text-sm mb-3 line-clamp-2">{{ exp.description }}</p>
            <div class="flex flex-wrap gap-4 text-sm text-gray-500">
              <div class="flex items-center">
                <el-icon class="mr-1"><Calendar /></el-icon>
                支出日期：{{ formatDate(exp.expenditure_date) }}
              </div>
              <div class="flex items-center">
                <el-icon class="mr-1"><User /></el-icon>
                收款方：{{ exp.recipient }}
              </div>
              <div class="flex items-center">
                <el-icon class="mr-1"><Document /></el-icon>
                发票：{{ exp.invoices ? exp.invoices.length : 0 }} 张
              </div>
              <div class="flex items-center">
                <el-icon class="mr-1"><Coin /></el-icon>
                已分配：¥{{ formatNumber(exp.allocated_amount) }} / ¥{{ formatNumber(exp.amount) }}
              </div>
            </div>
          </div>
          <div class="text-right ml-6">
            <div class="text-2xl font-bold text-love">¥{{ formatNumber(exp.amount) }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ formatDateTime(exp.created_at) }}</div>
          </div>
        </div>
        <el-progress
          class="mt-3"
          :percentage="allocationPercentage(exp)"
          :stroke-width="6"
          :show-text="false"
          color="#e11d48"
        />
      </el-card>
    </div>

    <el-empty v-else-if="!loading" description="暂无支出记录" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getExpenditures, getMyProjects, getPendingProjects } from '@/api/projects'
import { useUserStore } from '@/stores/user'
import type { Expenditure, Project } from '@/types'
import { EXPENDITURE_TYPE_OPTIONS } from '@/types'
import {
  Plus, Calendar, User, Document, Coin
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const expenditures = ref<Expenditure[]>([])
const projects = ref<Project[]>([])
const filterType = ref('')
const filterProject = ref<number | ''>('')

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

const expenditureTypeTagType = (type: string) => {
  switch (type) {
    case 'material': return 'warning'
    case 'cash': return 'danger'
    case 'service': return 'primary'
    default: return 'info'
  }
}

const allocationPercentage = (exp: Expenditure) => {
  const amount = parseFloat(String(exp.amount))
  const allocated = parseFloat(String(exp.allocated_amount))
  if (amount <= 0) return 0
  return Math.min(100, Math.round((allocated / amount) * 100))
}

const fetchProjects = async () => {
  try {
    let data: Project[]
    if (userStore.isAuditor) {
      data = await getPendingProjects('all')
    } else {
      data = await getMyProjects()
    }
    projects.value = data
  } catch (error) {
    console.error('Fetch projects error:', error)
  }
}

const fetchExpenditures = async () => {
  loading.value = true
  try {
    const projectId = filterProject.value ? Number(filterProject.value) : undefined
    const data = await getExpenditures(projectId, filterType.value || undefined)
    expenditures.value = data
  } catch (error) {
    console.error('Fetch expenditures error:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchProjects()
  await fetchExpenditures()
})
</script>
