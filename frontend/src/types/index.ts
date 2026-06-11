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

export type ProjectStatus = 'pending' | 'approved' | 'rejected' | 'funding' | 'completed'

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

export interface ProjectAuditForm {
  status: 'approved' | 'rejected'
  reject_reason?: string
}
