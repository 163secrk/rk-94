import request from '@/utils/request'
import type {
  Project, ProjectCreateForm, ProjectAuditForm, Donation, DonationCreateForm,
  Expenditure, ExpenditureCreateForm, ExpenditureInvoice,
  DonationAllocationCreateForm, DonationAllocationDetail,
  DonationTracking, ProjectExpenditureSummary,
  ProjectUpdate, ProjectUpdateCreateForm, Notification, NotificationListResponse,
  UserHonorProfile
} from '@/types'

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

export const getExpenditures = (projectId?: number, expenditureType?: string) => {
  const url = projectId ? `/projects/${projectId}/expenditures/` : '/projects/expenditures/'
  const params = expenditureType ? { expenditure_type: expenditureType } : {}
  return request.get<any, Expenditure[]>(url, { params })
}

export const createExpenditure = (data: ExpenditureCreateForm) => {
  return request.post<any, Expenditure>('/projects/expenditures/create/', data)
}

export const getExpenditureDetail = (id: number) => {
  return request.get<any, Expenditure>(`/projects/expenditures/${id}/`)
}

export const uploadExpenditureInvoice = (expenditureId: number, data: FormData) => {
  return request.post<any, ExpenditureInvoice>(
    `/projects/expenditures/${expenditureId}/upload-invoice/`,
    data,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
}

export const getAvailableDonationsForAllocation = (expenditureId: number) => {
  return request.get<any, Donation[]>(`/projects/expenditures/${expenditureId}/available-donations/`)
}

export const createDonationAllocation = (data: DonationAllocationCreateForm) => {
  return request.post<any, DonationAllocationDetail>('/projects/allocations/', data)
}

export const getDonationTracking = (donationId: number) => {
  return request.get<any, DonationTracking>(`/projects/donations/${donationId}/tracking/`)
}

export const getProjectExpenditureSummary = (projectId: number) => {
  return request.get<any, ProjectExpenditureSummary>(`/projects/${projectId}/expenditure-summary/`)
}

export const getProjectUpdates = (projectId: number) => {
  return request.get<any, ProjectUpdate[]>(`/projects/${projectId}/updates/`)
}

export const getMyProjectUpdates = (projectId?: number) => {
  const url = projectId ? `/projects/updates/my/${projectId}/` : '/projects/updates/my/'
  return request.get<any, ProjectUpdate[]>(url)
}

export const getMySupportedProjectUpdates = () => {
  return request.get<any, ProjectUpdate[]>('/projects/updates/supported/')
}

export const getProjectUpdateDetail = (id: number) => {
  return request.get<any, ProjectUpdate>(`/projects/updates/${id}/`)
}

export const createProjectUpdate = (data: FormData) => {
  return request.post<any, ProjectUpdate>('/projects/updates/create/', data, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export const getNotifications = (isRead?: boolean, type?: string) => {
  const params: any = {}
  if (isRead !== undefined) params.is_read = isRead
  if (type) params.type = type
  return request.get<any, NotificationListResponse>('/projects/notifications/', { params })
}

export const getNotificationUnreadCount = () => {
  return request.get<any, { unread_count: number }>('/projects/notifications/unread-count/')
}

export const markNotificationsRead = (notificationIds?: number[], all = false) => {
  const data: any = { all }
  if (notificationIds) data.notification_ids = notificationIds
  return request.post<any, { updated_count: number }>('/projects/notifications/mark-read/', data)
}

export const getNotificationDetail = (id: number) => {
  return request.get<any, Notification>(`/projects/notifications/${id}/`)
}

export const getMyHonorProfile = () => {
  return request.get<any, UserHonorProfile>('/projects/honor/my/')
}
