import request from '@/utils/request'
import type { LoginForm, RegisterForm, LoginResponse, User, VerificationProfile, VerificationForm } from '@/types'

export const register = (data: RegisterForm) => {
  return request.post<any, any>('/auth/register/', data)
}

export const login = (data: LoginForm) => {
  return request.post<any, LoginResponse>('/auth/login/', data)
}

export const logout = () => {
  return request.post<any, any>('/auth/logout/')
}

export const refreshToken = (refresh: string) => {
  return request.post<any, { access: string }>('/auth/token/refresh/', { refresh })
}

export const getUserInfo = () => {
  return request.get<any, User>('/auth/user/info/')
}

export const updateUserInfo = (data: Partial<User>) => {
  return request.put<any, User>('/auth/user/info/', data)
}

export const getVerificationProfile = () => {
  return request.get<any, VerificationProfile | null>('/auth/verification/')
}

export const submitVerification = (data: FormData) => {
  return request.post<any, VerificationProfile>('/auth/verification/', data, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export const getVerificationList = (status: string = 'pending') => {
  return request.get<any, VerificationProfile[]>('/auth/verification/list/', {
    params: { status },
  })
}

export const auditVerification = (id: number, data: { status: string; reject_reason?: string }) => {
  return request.post<any, VerificationProfile>(`/auth/verification/${id}/audit/`, data)
}
