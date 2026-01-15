/**
 * useHistory - React Query hooks for scan history CRUD operations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export interface ScanDataPoint {
  id: number
  scan_id: number
  index: number
  frequency_hz: number
  amplitude_dbm: number
}

export interface SavedScanSummary {
  id: number
  name: string
  start_freq_hz: number
  stop_freq_hz: number
  points: number
  preset_name: string | null
  location: string | null
  scan_completed_at: string | null
  created_at: string
}

export interface SavedScanDetail extends SavedScanSummary {
  rbw_khz: number | null
  preset_id: number | null
  notes: string | null
  tags: string | null
  scan_started_at: string | null
  data_point_count: number
  data_points: ScanDataPoint[]
}

export interface ScanListResponse {
  items: SavedScanSummary[]
  total: number
  page: number
  per_page: number
}

export interface ScanUpdateData {
  name?: string
  location?: string
  notes?: string
  tags?: string
}

export interface ScanListParams {
  page?: number
  per_page?: number
  search?: string
  sort_by?: 'name' | 'created_at' | 'start_freq_hz' | 'location'
  sort_order?: 'asc' | 'desc'
}

const API_BASE = '/api'

async function fetchScans(params: ScanListParams = {}): Promise<ScanListResponse> {
  const searchParams = new URLSearchParams()
  if (params.page) searchParams.set('page', String(params.page))
  if (params.per_page) searchParams.set('per_page', String(params.per_page))
  if (params.search) searchParams.set('search', params.search)
  if (params.sort_by) searchParams.set('sort_by', params.sort_by)
  if (params.sort_order) searchParams.set('sort_order', params.sort_order)

  const url = `${API_BASE}/scans${searchParams.toString() ? `?${searchParams}` : ''}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error('Failed to fetch scans')
  }
  return response.json()
}

async function fetchScan(id: number): Promise<SavedScanDetail> {
  const response = await fetch(`${API_BASE}/scans/${id}`)
  if (!response.ok) {
    throw new Error('Failed to fetch scan')
  }
  return response.json()
}

async function updateScan(id: number, data: ScanUpdateData): Promise<SavedScanDetail> {
  const response = await fetch(`${API_BASE}/scans/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to update scan' }))
    throw new Error(error.detail || 'Failed to update scan')
  }
  return response.json()
}

async function deleteScan(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/scans/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete scan' }))
    throw new Error(error.detail || 'Failed to delete scan')
  }
}

async function exportScan(id: number, format: 'wwb' | 'wsm' | 'csv'): Promise<Blob> {
  const response = await fetch(`${API_BASE}/scans/${id}/export?format=${format}`)
  if (!response.ok) {
    throw new Error(`Failed to export scan as ${format.toUpperCase()}`)
  }
  return response.blob()
}

export function useScans(params: ScanListParams = {}) {
  return useQuery({
    queryKey: ['scans', params],
    queryFn: () => fetchScans(params),
  })
}

export function useScan(id: number | null) {
  return useQuery({
    queryKey: ['scan', id],
    queryFn: () => fetchScan(id!),
    enabled: id !== null,
  })
}

export function useUpdateScan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ScanUpdateData }) => updateScan(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      queryClient.invalidateQueries({ queryKey: ['scan', variables.id] })
    },
  })
}

export function useDeleteScan() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
  })
}

export function useExportScan() {
  return useMutation({
    mutationFn: ({ id, format }: { id: number; format: 'wwb' | 'wsm' | 'csv' }) =>
      exportScan(id, format),
    onSuccess: (blob, { format }) => {
      // Trigger download
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scan.${format === 'csv' ? 'csv' : format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}

// Utility functions
export function formatFrequencyMHz(hz: number): string {
  return `${(hz / 1e6).toFixed(3)} MHz`
}

export function formatFrequencyRange(startHz: number, stopHz: number): string {
  return `${(startHz / 1e6).toFixed(3)} - ${(stopHz / 1e6).toFixed(3)} MHz`
}

export function formatDate(dateString: string | null): string {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function parseTags(tags: string | null): string[] {
  if (!tags) return []
  return tags.split(',').map(t => t.trim()).filter(Boolean)
}
