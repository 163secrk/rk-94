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
