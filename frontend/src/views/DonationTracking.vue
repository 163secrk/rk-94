<template>
  <div class="max-w-4xl mx-auto" v-loading="loading">
    <el-page-header
      class="mb-6"
      content="返回"
      @back="$router.back()"
    />

    <template v-if="tracking">
      <div class="bg-white rounded-xl p-6 card-shadow mb-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h1 class="text-2xl font-bold text-gray-800 mb-1">捐款追踪</h1>
            <p class="text-gray-500 text-sm">订单号：{{ tracking.order_no }}</p>
          </div>
          <el-tag :type="statusTagType(tracking.status)" size="large" effect="dark">
            {{ tracking.status_display }}
          </el-tag>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mt-6">
          <div class="bg-gradient-to-br from-love-50 to-love-100 rounded-xl p-4">
            <div class="text-sm text-gray-600 mb-1">捐赠金额</div>
            <div class="text-2xl font-bold text-love">¥{{ formatNumber(tracking.amount) }}</div>
          </div>
          <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4">
            <div class="text-sm text-gray-600 mb-1">已使用</div>
            <div class="text-2xl font-bold text-green-600">¥{{ formatNumber(tracking.total_allocated) }}</div>
          </div>
          <div class="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4">
            <div class="text-sm text-gray-600 mb-1">待分配</div>
            <div class="text-2xl font-bold text-gray-700">¥{{ formatNumber(remainingAmount) }}</div>
          </div>
          <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4">
            <div class="text-sm text-gray-600 mb-1">使用比例</div>
            <div class="text-2xl font-bold text-blue-600">{{ usagePercentage }}%</div>
          </div>
        </div>

        <el-progress
          class="mt-6"
          :percentage="usagePercentage"
          :stroke-width="12"
          color="#e11d48"
        />

        <div class="flex gap-4 mt-4 text-sm text-gray-500">
          <div>捐赠时间：{{ tracking.created_at ? formatDateTime(tracking.created_at) : '-' }}</div>
          <div v-if="tracking.paid_at">支付时间：{{ formatDateTime(tracking.paid_at) }}</div>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 card-shadow">
        <h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center">
          <el-icon class="text-love mr-2"><Guide /></el-icon>
          钱款去向明细
        </h3>

        <el-alert
          v-if="tracking.expenditure_allocations.length === 0"
          type="info"
          :closable="false"
          show-icon
          class="mb-4"
        >
          您的捐款暂未被分配到具体支出项目中，请耐心等待。
        </el-alert>

        <el-timeline v-else>
          <el-timeline-item
            v-for="(alloc, index) in tracking.expenditure_allocations"
            :key="alloc.id"
            :timestamp="formatDateTime(alloc.created_at)"
            placement="top"
            :type="timelineType(index)"
            :hollow="index === tracking.expenditure_allocations.length - 1"
          >
            <el-card class="card-shadow hover:shadow-md transition-shadow cursor-pointer" @click="goToExpenditure(alloc)">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <el-tag :type="expenditureTypeTagType(alloc.expenditure_type)" size="small">
                      {{ alloc.expenditure_type_display }}
                    </el-tag>
                    <el-tag type="info" size="small">{{ alloc.project_title }}</el-tag>
                  </div>
                  <h4 class="text-base font-semibold text-gray-800 mb-1">{{ alloc.expenditure_title }}</h4>
                  <p class="text-sm text-gray-500">
                    分配人：{{ alloc.allocated_by_name || '系统' }}
                  </p>
                </div>
                <div class="text-right ml-4">
                  <div class="text-xl font-bold text-love">-¥{{ formatNumber(alloc.amount) }}</div>
                </div>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </template>

    <el-empty v-else-if="!loading" description="无法获取捐款追踪信息" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDonationTracking } from '@/api/projects'
import type { DonationTracking, DonationAllocationDetail } from '@/types'
import { Guide } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const tracking = ref<DonationTracking | null>(null)

const formatNumber = (num: string | number) => {
  const n = typeof num === 'string' ? parseFloat(num) : num
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const statusTagType = (status: string) => {
  switch (status) {
    case 'paid': return 'success'
    case 'refunded': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const expenditureTypeTagType = (type: string) => {
  switch (type) {
    case 'material': return 'warning'
    case 'cash': return 'danger'
    case 'service': return 'primary'
    default: return 'info'
  }
}

const timelineType = (index: number) => {
  const types = ['danger', 'warning', 'primary', 'success', 'info']
  return types[index % types.length] as any
}

const remainingAmount = computed(() => {
  if (!tracking.value) return 0
  const total = parseFloat(String(tracking.value.amount))
  const allocated = parseFloat(String(tracking.value.total_allocated))
  return Math.max(0, total - allocated)
})

const usagePercentage = computed(() => {
  if (!tracking.value) return 0
  const total = parseFloat(String(tracking.value.amount))
  const allocated = parseFloat(String(tracking.value.total_allocated))
  if (total <= 0) return 0
  return Math.min(100, Math.round((allocated / total) * 100))
})

const goToExpenditure = (alloc: DonationAllocationDetail) => {
  router.push(`/expenditures/${alloc.expenditure_id}`)
}

const fetchTracking = async () => {
  loading.value = true
  try {
    const id = parseInt(route.params.id as string)
    tracking.value = await getDonationTracking(id)
  } catch (error) {
    console.error('Fetch donation tracking error:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTracking()
})
</script>
