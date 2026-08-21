import axios from 'axios'

const API_BASE = '/api'

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Ticket {
  id: number
  ticket_id: string
  customer_name: string
  contact_number: string
  review: string
  timestamp?: string
  predicted_category: string
  predicted_priority: string
  predicted_department: string
  confidence: number
  routing_status: 'AUTO_ROUTED' | 'HUMAN_REVIEW'
  escalated: boolean
  escalation_reason?: string
  final_category: string
  final_priority: string
  final_department: string
  is_reviewed: boolean
  reviewer_notes?: string
  model_version: string
  created_at?: string
  reviewed_at?: string
}

export interface AnalyticsSummary {
  total_tickets: number
  auto_routed_count: number
  human_review_count: number
  auto_routing_rate: number
  avg_confidence: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  categories: Record<string, number>
  priorities: Record<string, number>
  departments: Record<string, number>
}

export interface TrendItem {
  name: string
  current: number
  previous: number
  percentage_change: number
  direction: 'UP' | 'DOWN' | 'FLAT'
}

export interface AnalyticsTrends {
  summary_trends: TrendItem[]
  category_trends: TrendItem[]
  priority_trends: TrendItem[]
  department_trends: TrendItem[]
}

// API methods
export const triageSingleTicket = async (data: {
  review: string
  customer_name?: string
  contact_number?: string
}): Promise<Ticket> => {
  const res = await apiClient.post('/triage', data)
  return res.data
}

export const uploadBatchCsv = async (file: File): Promise<any> => {
  const formData = new FormData()
  formData.append('file', file)
  const res = await apiClient.post('/upload-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export const fetchTickets = async (params: {
  page?: number
  page_size?: number
  category?: string
  priority?: string
  department?: string
  routing_status?: string
  search?: string
}): Promise<{ total: number; page: number; total_pages: number; tickets: Ticket[] }> => {
  const res = await apiClient.get('/tickets', { params })
  return res.data
}

export const fetchAnalyticsSummary = async (): Promise<AnalyticsSummary> => {
  const res = await apiClient.get('/analytics/summary')
  return res.data
}

export const fetchAnalyticsTrends = async (days_window = 7): Promise<AnalyticsTrends> => {
  const res = await apiClient.get('/analytics/trends', { params: { days_window } })
  return res.data
}

export const fetchReviewQueue = async (): Promise<Ticket[]> => {
  const res = await apiClient.get('/review-queue')
  return res.data
}

export const resolveReviewTicket = async (
  ticketId: number,
  data: {
    final_category: string
    final_priority: string
    final_department: string
    reviewer_notes?: string
  }
): Promise<Ticket> => {
  const res = await apiClient.post(`/review-queue/${ticketId}/resolve`, data)
  return res.data
}
