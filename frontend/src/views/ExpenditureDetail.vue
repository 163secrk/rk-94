<template>
  <div class="max-w-5xl mx-auto" v-loading="loading">
    <el-page-header
      class="mb-6"
      content="返回支出记录"
      @back="$router.push('/expenditures')"
    />

    <template v-if="expenditure">
      <div class="bg-white rounded-xl p-6 card-shadow mb-6">
        <div class="flex justify-between items-start mb-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h1 class="text-2xl font-bold text-gray-800">{{ expenditure.title }}</h1>
              <el-tag :type="expenditureTypeTagType(expenditure.expenditure_type)" size="large">
                {{ expenditure.expenditure_type_display }}
              </el-tag>
              <el-tag type="info" size="large">{{ expenditure.project_title }}</el-tag>
            </div>
            <p class="text-gray-600">{{ expenditure.description }}</p>
          </div>
          <div class="text-right">
            <div class="text-3xl font-bold text-love">¥{{ formatNumber(expenditure.amount) }}</div>
            <div class="text-sm text-gray-500 mt-1">
              已分配 ¥{{ formatNumber(expenditure.allocated_amount) }}
              <span class="mx-1">/</span>
              发票 ¥{{ formatNumber(expenditure.invoices_total) }}
            </div>
          </div>
        </div>

        <el-progress
          :percentage="allocationPercentage"
          :stroke-width="10"
          color="#e11d48"
        />

        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mt-6">
          <div>
            <div class="text-sm text-gray-500 mb-1">支出日期</div>
            <div class="text-gray-800 font-medium">{{ formatDate(expenditure.expenditure_date) }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-500 mb-1">收款方/接收人</div>
            <div class="text-gray-800 font-medium">{{ expenditure.recipient }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-500 mb-1">经办人</div>
            <div class="text-gray-800 font-medium">{{ expenditure.operator_name || '-' }}</div>
          </div>
          <div>
            <div class="text-sm text-gray-500 mb-1">创建时间</div>
            <div class="text-gray-800 font-medium">{{ formatDateTime(expenditure.created_at) }}</div>
          </div>
        </div>

        <div v-if="expenditure.remark" class="mt-4 bg-gray-50 rounded-lg p-4">
          <div class="text-sm text-gray-500 mb-1">备注</div>
          <div class="text-gray-700">{{ expenditure.remark }}</div>
        </div>
      </div>

      <div class="bg-white rounded-xl p-6 card-shadow mb-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold text-gray-800 flex items-center">
            <el-icon class="text-love mr-2"><Document /></el-icon>
            发票凭证
          </h3>
          <el-button
            v-if="userStore.isAuditor"
            type="primary"
            size="small"
            class="!bg-love !border-love hover:!bg-love-dark"
            @click="invoiceDialogVisible = true"
          >
            <el-icon class="mr-1"><Upload /></el-icon>
            上传发票
          </el-button>
        </div>

        <div v-if="expenditure.invoices && expenditure.invoices.length > 0">
          <el-table :data="expenditure.invoices" border stripe>
            <el-table-column type="index" label="序号" width="70" align="center" />
            <el-table-column prop="invoice_no" label="发票号码" min-width="160" />
            <el-table-column label="发票金额" width="140" align="right">
              <template #default="{ row }">
                <span class="font-semibold text-love">¥{{ formatNumber(row.amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="issuer" label="开票方" min-width="160" />
            <el-table-column prop="issued_date" label="开票日期" width="120">
              <template #default="{ row }">
                {{ row.issued_date ? formatDate(row.issued_date) : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="previewInvoice(row)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-empty v-else description="暂无发票凭证" />
      </div>

      <div class="bg-white rounded-xl p-6 card-shadow mb-6">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold text-gray-800 flex items-center">
            <el-icon class="text-love mr-2"><Coin /></el-icon>
            捐款分配（钱款去向）
          </h3>
          <el-button
            v-if="userStore.isAuditor"
            type="primary"
            size="small"
            class="!bg-love !border-love hover:!bg-love-dark"
            @click="openAllocationDialog"
          >
            <el-icon class="mr-1"><Plus /></el-icon>
            分配捐款
          </el-button>
        </div>

        <div v-if="expenditure.donation_allocations && expenditure.donation_allocations.length > 0">
          <el-table :data="expenditure.donation_allocations" border stripe>
            <el-table-column type="index" label="序号" width="70" align="center" />
            <el-table-column label="捐赠订单" min-width="200">
              <template #default="{ row }">
                <div class="flex items-center gap-2">
                  <el-avatar :size="28" class="bg-love">
                    {{ row.donor_username?.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <div>
                    <div class="text-sm font-medium text-gray-800">{{ row.donor_username }}</div>
                    <div class="text-xs text-gray-500">{{ row.donation_order_no }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="捐赠金额" width="140" align="right">
              <template #default="{ row }">
                ¥{{ formatNumber(row.donation_amount) }}
              </template>
            </el-table-column>
            <el-table-column label="本次分配" width="140" align="right">
              <template #default="{ row }">
                <span class="font-semibold text-love">¥{{ formatNumber(row.amount) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="分配时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-empty v-else description="暂无捐款分配记录" />
      </div>

      <el-dialog
        v-model="invoiceDialogVisible"
        title="上传发票"
        width="500px"
        destroy-on-close
      >
        <el-form
          ref="invoiceFormRef"
          :model="invoiceForm"
          :rules="invoiceRules"
          label-width="100px"
          label-position="top"
        >
          <el-form-item label="发票文件" prop="invoice_file">
            <el-upload
              :auto-upload="false"
              :limit="1"
              :on-change="handleInvoiceFileChange"
              accept=".pdf,.jpg,.jpeg,.png,.gif"
            >
              <el-button type="primary">选择文件</el-button>
              <template #tip>
                <div class="el-upload__tip text-xs text-gray-500 mt-1">
                  支持 PDF、JPG、PNG 格式
                </div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item label="发票号码">
            <el-input v-model="invoiceForm.invoice_no" placeholder="选填" />
          </el-form-item>
          <el-form-item label="发票金额（元）" prop="amount">
            <el-input-number
              v-model="invoiceForm.amount"
              :min="0.01"
              :precision="2"
              :step="100"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="开票方">
            <el-input v-model="invoiceForm.issuer" placeholder="选填" />
          </el-form-item>
          <el-form-item label="开票日期">
            <el-date-picker
              v-model="invoiceForm.issued_date"
              type="date"
              placeholder="选择开票日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="invoiceForm.remark"
              type="textarea"
              :rows="2"
              placeholder="选填"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="invoiceDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            class="!bg-love !border-love hover:!bg-love-dark"
            :loading="invoiceSubmitting"
            @click="submitInvoice"
          >
            上传
          </el-button>
        </template>
      </el-dialog>

      <el-dialog
        v-model="allocationDialogVisible"
        title="分配捐款"
        width="600px"
        destroy-on-close
        @open="fetchAvailableDonations"
      >
        <el-alert
          type="info"
          :closable="false"
          class="mb-4"
          show-icon
        >
          选择一笔已支付的捐赠，将其部分或全部分配到本支出项目中，实现"钱款去向"的精准追踪。
        </el-alert>
        <el-form
          ref="allocationFormRef"
          :model="allocationForm"
          :rules="allocationRules"
          label-width="120px"
          label-position="top"
        >
          <el-form-item label="选择捐赠" prop="donation">
            <el-select
              v-model="allocationForm.donation"
              placeholder="请选择要分配的捐赠"
              filterable
              style="width: 100%"
              @change="handleDonationChange"
            >
              <el-option
                v-for="don in availableDonations"
                :key="don.id"
                :label="`${don.user?.username || '匿名'} - ${don.order_no} - ¥${formatNumber(don.amount)}`"
                :value="don.id"
              />
            </el-select>
          </el-form-item>
          <div v-if="selectedDonation" class="bg-gray-50 rounded-lg p-4 mb-4">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-500">订单号：</span>
                <span class="font-medium">{{ selectedDonation.order_no }}</span>
              </div>
              <div>
                <span class="text-gray-500">捐赠人：</span>
                <span class="font-medium">{{ selectedDonation.user?.username || '匿名' }}</span>
              </div>
              <div>
                <span class="text-gray-500">捐赠金额：</span>
                <span class="font-medium text-love">¥{{ formatNumber(selectedDonation.amount) }}</span>
              </div>
              <div>
                <span class="text-gray-500">支付时间：</span>
                <span class="font-medium">{{ selectedDonation.paid_at ? formatDateTime(selectedDonation.paid_at) : '-' }}</span>
              </div>
            </div>
          </div>
          <el-form-item label="分配金额（元）" prop="amount">
            <el-input-number
              v-model="allocationForm.amount"
              :min="0.01"
              :max="maxAllocationAmount"
              :precision="2"
              :step="10"
              controls-position="right"
              style="width: 100%"
            />
            <div v-if="selectedDonation" class="text-xs text-gray-500 mt-1">
              最大可分配金额：¥{{ formatNumber(maxAllocationAmount) }}
            </div>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="allocationDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            class="!bg-love !border-love hover:!bg-love-dark"
            :loading="allocationSubmitting"
            @click="submitAllocation"
          >
            确认分配
          </el-button>
        </template>
      </el-dialog>
    </template>

    <el-empty v-else-if="!loading" description="支出记录不存在或暂无权限查看" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  getExpenditureDetail,
  uploadExpenditureInvoice,
  getAvailableDonationsForAllocation,
  createDonationAllocation
} from '@/api/projects'
import { useUserStore } from '@/stores/user'
import type {
  Expenditure, ExpenditureInvoice, Donation,
  ExpenditureInvoiceCreateForm, DonationAllocationCreateForm
} from '@/types'
import {
  ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile
} from 'element-plus'
import { Document, Upload, Plus, Coin } from '@element-plus/icons-vue'

const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const expenditure = ref<Expenditure | null>(null)

const invoiceDialogVisible = ref(false)
const invoiceSubmitting = ref(false)
const invoiceFormRef = ref<FormInstance>()
const invoiceFile = ref<File | null>(null)
const invoiceForm = reactive<Partial<ExpenditureInvoiceCreateForm>>({
  invoice_no: '',
  amount: 0,
  issued_date: '',
  issuer: '',
  remark: ''
})

const allocationDialogVisible = ref(false)
const allocationSubmitting = ref(false)
const allocationFormRef = ref<FormInstance>()
const availableDonations = ref<Donation[]>([])
const selectedDonation = ref<Donation | null>(null)
const allocationForm = reactive<DonationAllocationCreateForm>({
  donation: 0,
  expenditure: 0,
  amount: 0
})

const invoiceRules: FormRules = {
  invoice_file: [
    { required: true, message: '请选择发票文件', trigger: 'change' }
  ],
  amount: [
    { required: true, message: '请输入发票金额', trigger: 'blur' }
  ]
}

const allocationRules: FormRules = {
  donation: [
    { required: true, message: '请选择要分配的捐赠', trigger: 'change' }
  ],
  amount: [
    { required: true, message: '请输入分配金额', trigger: 'blur' }
  ]
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

const expenditureTypeTagType = (type: string) => {
  switch (type) {
    case 'material': return 'warning'
    case 'cash': return 'danger'
    case 'service': return 'primary'
    default: return 'info'
  }
}

const allocationPercentage = computed(() => {
  if (!expenditure.value) return 0
  const amount = parseFloat(String(expenditure.value.amount))
  const allocated = parseFloat(String(expenditure.value.allocated_amount))
  if (amount <= 0) return 0
  return Math.min(100, Math.round((allocated / amount) * 100))
})

const maxAllocationAmount = computed(() => {
  if (!selectedDonation.value) return 0
  return parseFloat(String(selectedDonation.value.amount))
})

const fetchDetail = async () => {
  loading.value = true
  try {
    const id = parseInt(route.params.id as string)
    expenditure.value = await getExpenditureDetail(id)
    allocationForm.expenditure = id
  } catch (error) {
    console.error('Fetch expenditure detail error:', error)
  } finally {
    loading.value = false
  }
}

const handleInvoiceFileChange = (file: UploadFile) => {
  invoiceFile.value = file.raw as File
}

const submitInvoice = async () => {
  if (!invoiceFormRef.value || !invoiceFile.value || !expenditure.value) return
  await invoiceFormRef.value.validate()

  invoiceSubmitting.value = true
  try {
    const formData = new FormData()
    formData.append('invoice_file', invoiceFile.value)
    if (invoiceForm.invoice_no) formData.append('invoice_no', invoiceForm.invoice_no)
    formData.append('amount', String(invoiceForm.amount))
    if (invoiceForm.issued_date) formData.append('issued_date', invoiceForm.issued_date)
    if (invoiceForm.issuer) formData.append('issuer', invoiceForm.issuer)
    if (invoiceForm.remark) formData.append('remark', invoiceForm.remark)

    await uploadExpenditureInvoice(expenditure.value.id, formData)
    ElMessage.success('发票上传成功')
    invoiceDialogVisible.value = false
    invoiceFile.value = null
    fetchDetail()
  } catch (error) {
    console.error('Upload invoice error:', error)
  } finally {
    invoiceSubmitting.value = false
  }
}

const previewInvoice = (invoice: ExpenditureInvoice) => {
  window.open(invoice.invoice_file, '_blank')
}

const openAllocationDialog = () => {
  allocationForm.donation = 0
  allocationForm.amount = 0
  selectedDonation.value = null
  allocationDialogVisible.value = true
}

const fetchAvailableDonations = async () => {
  if (!expenditure.value) return
  try {
    availableDonations.value = await getAvailableDonationsForAllocation(expenditure.value.id)
  } catch (error) {
    console.error('Fetch available donations error:', error)
  }
}

const handleDonationChange = (donationId: number) => {
  selectedDonation.value = availableDonations.value.find(d => d.id === donationId) || null
  if (selectedDonation.value) {
    allocationForm.amount = parseFloat(String(selectedDonation.value.amount))
  }
}

const submitAllocation = async () => {
  if (!allocationFormRef.value) return
  await allocationFormRef.value.validate()

  allocationSubmitting.value = true
  try {
    await createDonationAllocation({
      donation: allocationForm.donation,
      expenditure: allocationForm.expenditure,
      amount: allocationForm.amount
    })
    ElMessage.success('捐款分配成功')
    allocationDialogVisible.value = false
    fetchDetail()
  } catch (error) {
    console.error('Create allocation error:', error)
  } finally {
    allocationSubmitting.value = false
  }
}

onMounted(() => {
  fetchDetail()
})
</script>
