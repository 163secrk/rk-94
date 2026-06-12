export interface User {
  id: number
  username: string
  email: string
  role: 'donor' | 'initiator' | 'auditor'
  role_display: string
  phone: string | null
  avatar: string | null
  is_verified: boolean
  date_joined: string
}

export interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export interface VerificationProfileUser {
  id: number
  username: string
  email: string
  role: string
  role_display: string
}

export interface VerificationProfile {
  id: number
  profile_type: 'personal' | 'enterprise'
  profile_type_display: string
  status: 'pending' | 'approved' | 'rejected'
  status_display: string
  real_name: string
  id_card: string
  personal_id_front: string | null
  personal_id_back: string | null
  enterprise_license: string | null
  enterprise_legal_person: string | null
  reject_reason: string | null
  verified_at: string | null
  submitted_at: string
  user?: VerificationProfileUser
}

export interface VerificationAuditForm {
  status: 'approved' | 'rejected'
  reject_reason?: string
}

export interface RegisterForm {
  username: string
  email: string
  password: string
  confirm_password: string
  role: 'donor' | 'initiator' | 'auditor'
  phone: string
}

export interface LoginForm {
  username: string
  password: string
}

export interface PersonalVerificationForm {
  profile_type: 'personal'
  real_name: string
  id_card: string
  personal_id_front: File | null
  personal_id_back: File | null
}

export interface EnterpriseVerificationForm {
  profile_type: 'enterprise'
  real_name: string
  id_card: string
  enterprise_license: File | null
  enterprise_legal_person: string
}

export type VerificationForm = PersonalVerificationForm | EnterpriseVerificationForm

export type ProjectCategory = 'education' | 'medical' | 'disaster' | 'poverty' | 'environment' | 'animal' | 'elderly' | 'children' | 'other'

export type ProjectStatus = 'pending' | 'approved' | 'rejected' | 'funding' | 'executing' | 'completed'

export const PROJECT_CATEGORY_OPTIONS: { value: ProjectCategory; label: string }[] = [
  { value: 'education', label: '教育助学' },
  { value: 'medical', label: '医疗救助' },
  { value: 'disaster', label: '灾害救援' },
  { value: 'poverty', label: '扶贫济困' },
  { value: 'environment', label: '环境保护' },
  { value: 'animal', label: '动物保护' },
  { value: 'elderly', label: '关爱老人' },
  { value: 'children', label: '关爱儿童' },
  { value: 'other', label: '其他公益' },
]

export const PROJECT_STATUS_OPTIONS: { value: ProjectStatus; label: string }[] = [
  { value: 'pending', label: '待审核' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已拒绝' },
  { value: 'funding', label: '募集中' },
  { value: 'executing', label: '执行中' },
  { value: 'completed', label: '已完成' },
]

export interface ProjectBudget {
  id?: number
  category: string
  description?: string
  amount: string | number
  quantity: number
  unit?: string
  subtotal?: string | number
}

export interface ProjectInitiator {
  id: number
  username: string
  email: string
  avatar: string | null
}

export interface Project {
  id: number
  title: string
  category: ProjectCategory
  category_display: string
  description: string
  detail_content?: string
  cover_image: string | null
  target_amount: string | number
  current_amount: string | number
  progress_percentage: number
  deadline: string
  status: ProjectStatus
  status_display: string
  reject_reason?: string
  initiator: ProjectInitiator
  budgets?: ProjectBudget[]
  budget_total?: string | number
  audited_at?: string
  created_at: string
  updated_at?: string
}

export interface ProjectCreateForm {
  title: string
  category: ProjectCategory
  description: string
  detail_content: string
  cover_image: File | null
  target_amount: string | number
  deadline: string
  budgets: ProjectBudget[]
}

export type DonationStatus = 'pending' | 'paid' | 'failed' | 'refunded'

export interface DonationProject {
  id: number
  title: string
  cover_image: string | null
}

export interface DonationDonor {
  id: number
  username: string
  avatar: string | null
}

export interface Donation {
  id: number
  order_no: string
  user: DonationDonor
  project: DonationProject
  amount: string | number
  status: DonationStatus
  status_display: string
  message: string | null
  paid_at: string | null
  refunded_at: string | null
  transaction_id: string | null
  created_at: string
  updated_at: string
}

export interface DonationCreateForm {
  project: number
  amount: number
  message?: string
}

export interface ProjectAuditForm {
  status: 'approved' | 'rejected'
  reject_reason?: string
}

export type ExpenditureType = 'material' | 'cash' | 'service' | 'other'

export const EXPENDITURE_TYPE_OPTIONS: { value: ExpenditureType; label: string }[] = [
  { value: 'material', label: '物料采购' },
  { value: 'cash', label: '现金发放' },
  { value: 'service', label: '服务采购' },
  { value: 'other', label: '其他支出' },
]

export interface ExpenditureInvoice {
  id: number
  invoice_no: string | null
  invoice_file: string
  amount: string | number
  issued_date: string | null
  issuer: string | null
  remark: string | null
  created_at: string
}

export interface DonationAllocation {
  id: number
  donation_order_no: string
  donor_username: string
  donor_avatar: string | null
  donation_amount: string | number
  amount: string | number
  created_at: string
}

export interface Expenditure {
  id: number
  project: number
  project_title: string
  expenditure_type: ExpenditureType
  expenditure_type_display: string
  title: string
  description: string
  amount: string | number
  allocated_amount: string | number
  invoices_total: string | number
  expenditure_date: string
  recipient: string
  operator_name: string | null
  remark: string | null
  invoices?: ExpenditureInvoice[]
  donation_allocations?: DonationAllocation[]
  created_at: string
  updated_at: string
}

export interface ExpenditureCreateForm {
  project: number
  expenditure_type: ExpenditureType
  title: string
  description: string
  amount: number
  expenditure_date: string
  recipient: string
  remark?: string
}

export interface ExpenditureInvoiceCreateForm {
  invoice_no?: string
  invoice_file: File
  amount: number
  issued_date?: string
  issuer?: string
  remark?: string
}

export interface DonationAllocationCreateForm {
  donation: number
  expenditure: number
  amount: number
}

export interface DonationAllocationDetail {
  id: number
  donation_order_no: string
  donor_username: string
  expenditure_id: number
  expenditure_title: string
  expenditure_type: ExpenditureType
  expenditure_type_display: string
  project_title: string
  amount: string | number
  allocated_by_name: string | null
  created_at: string
}

export interface DonationTracking {
  id: number
  order_no: string
  amount: string | number
  status: DonationStatus
  status_display: string
  total_allocated: string | number
  expenditure_allocations: DonationAllocationDetail[]
  paid_at: string | null
  created_at: string
}

export interface ProjectExpenditureSummary {
  id: number
  title: string
  current_amount: string | number
  used_amount: string | number
  total_expenditure: string | number
  total_allocated: string | number
  expenditures: Expenditure[]
}

export type UpdateType = 'text' | 'image' | 'video' | 'mixed'

export const UPDATE_TYPE_OPTIONS: { value: UpdateType; label: string }[] = [
  { value: 'text', label: '文字动态' },
  { value: 'image', label: '图片动态' },
  { value: 'video', label: '视频动态' },
  { value: 'mixed', label: '混合动态' },
]

export interface ProjectUpdateImage {
  id: number
  image: string
  description: string | null
  sort_order: number
  created_at: string
}

export interface ProjectUpdateVideo {
  id: number
  video: string
  cover_image: string | null
  description: string | null
  sort_order: number
  created_at: string
}

export interface ProjectUpdateSimpleProject {
  id: number
  title: string
  cover_image: string | null
  status: ProjectStatus
  status_display: string
}

export interface ProjectUpdate {
  id: number
  project: ProjectUpdateSimpleProject
  title: string
  content: string
  update_type: UpdateType
  update_type_display: string
  initiator: ProjectInitiator
  images_count: number
  videos_count: number
  images?: ProjectUpdateImage[]
  videos?: ProjectUpdateVideo[]
  created_at: string
  updated_at: string
}

export interface ProjectUpdateCreateForm {
  project: number
  title: string
  content: string
  images?: File[]
  videos?: File[]
}

export type NotificationType = 'project_update' | 'donation_success' | 'project_completed' | 'system'

export const NOTIFICATION_TYPE_OPTIONS: { value: NotificationType; label: string }[] = [
  { value: 'project_update', label: '项目进展' },
  { value: 'donation_success', label: '捐赠成功' },
  { value: 'project_completed', label: '项目完成' },
  { value: 'system', label: '系统通知' },
]

export interface Notification {
  id: number
  notification_type: NotificationType
  notification_type_display: string
  title: string
  content: string
  is_read: boolean
  read_at: string | null
  related_project_id: number | null
  related_update_id: number | null
  related_donation_id: number | null
  created_at: string
}

export interface NotificationListResponse {
  list: Notification[]
  unread_count: number
}

export interface UserHonorProfile {
  love_points: number
  total_donation_amount: string | number
  consecutive_donation_days: number
  current_badge_level: string | null
  badge_level_display: string | null
  donation_points: number
  streak_points: number
  last_donation_date: string | null
  next_badge_level: string | null
  next_badge_threshold: number | null
  points_to_next: number
  available_receipt_types: Array<{ value: string; label: string; available: boolean }>
  supported_projects_count: number
  updated_at: string
}
