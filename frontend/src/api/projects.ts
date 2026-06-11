import request from '@/utils/request'
import type {
  Project, ProjectCreateForm, ProjectAuditForm, Donation, DonationCreateForm,
  Expenditure, ExpenditureCreateForm, ExpenditureInvoice,
  DonationAllocationCreateForm, DonationAllocationDetail,
  DonationTracking, ProjectExpenditureSummary
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
