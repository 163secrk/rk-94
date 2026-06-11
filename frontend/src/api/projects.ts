import request from '@/utils/request'
import type { Project, ProjectCreateForm, ProjectAuditForm, Donation, DonationCreateForm } from '@/types'

export const getPublicProjects = (category?: string) => {
  const params = category ? { category } : {}
  return request.get<any, Project[]>('/projects/public/', { params })
}

export const getMyProjects = () => {
  return request.get<any, Project[]>('/projects/my/')
}

export const getPendingProjects = (status: string = 'pending') => {
  return request.get<any, Project[]>('/projects/pending/', { params: { status } })
}

export const getProjectDetail = (id: number) => {
  return request.get<any, Project>(`/projects/${id}/`)
}

export const createProject = (data: FormData) => {
  return request.post<any, Project>('/projects/create/', data, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export const auditProject = (id: number, data: ProjectAuditForm) => {
  return request.post<any, Project>(`/projects/${id}/audit/`, data)
}

export const createDonation = (data: DonationCreateForm) => {
  return request.post<any, { donation: Donation; payment_url: string }>('/projects/donations/', data)
}

export const simulatePayment = (donationId: number) => {
  return request.post<any, Donation>(`/projects/donations/${donationId}/pay/`)
}

export const getProjectDonations = (projectId: number) => {
  return request.get<any, Donation[]>(`/projects/${projectId}/donations/`)
}
