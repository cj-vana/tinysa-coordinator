import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

export type PresetCategory = 'UHF' | 'VHF' | 'ISM' | 'Custom'

export interface Preset {
  id: number
  name: string
  description: string | null
  start_freq_hz: number
  stop_freq_hz: number
  points: number
  rbw_khz: number | null
  category: PresetCategory
  is_builtin: boolean
  created_at: string
  updated_at: string
}

export interface PresetCreate {
  name: string
  description?: string | null
  start_freq_hz: number
  stop_freq_hz: number
  points?: number
  rbw_khz?: number | null
  category?: PresetCategory
}

export interface PresetUpdate {
  name?: string
  description?: string | null
  start_freq_hz?: number
  stop_freq_hz?: number
  points?: number
  rbw_khz?: number | null
  category?: PresetCategory
}

export interface PresetListResponse {
  items: Preset[]
  total: number
  page: number
  per_page: number
}

const API_BASE = '/api'

async function fetchPresets(category?: PresetCategory): Promise<PresetListResponse> {
  const params = new URLSearchParams()
  if (category) {
    params.set('category', category)
  }
  const url = `${API_BASE}/presets${params.toString() ? `?${params}` : ''}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error('Failed to fetch presets')
  }
  return response.json()
}

async function fetchPreset(id: number): Promise<Preset> {
  const response = await fetch(`${API_BASE}/presets/${id}`)
  if (!response.ok) {
    throw new Error('Failed to fetch preset')
  }
  return response.json()
}

async function createPreset(data: PresetCreate): Promise<Preset> {
  const response = await fetch(`${API_BASE}/presets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create preset' }))
    throw new Error(error.detail || 'Failed to create preset')
  }
  return response.json()
}

async function updatePreset(id: number, data: PresetUpdate): Promise<Preset> {
  const response = await fetch(`${API_BASE}/presets/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to update preset' }))
    throw new Error(error.detail || 'Failed to update preset')
  }
  return response.json()
}

async function deletePreset(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/presets/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete preset' }))
    throw new Error(error.detail || 'Failed to delete preset')
  }
}

export function usePresets(category?: PresetCategory) {
  return useQuery({
    queryKey: ['presets', category],
    queryFn: () => fetchPresets(category),
  })
}

export function usePreset(id: number | null) {
  return useQuery({
    queryKey: ['preset', id],
    queryFn: () => fetchPreset(id!),
    enabled: id !== null,
  })
}

export function useCreatePreset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createPreset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presets'] })
    },
  })
}

export function useUpdatePreset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PresetUpdate }) => updatePreset(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['presets'] })
      queryClient.invalidateQueries({ queryKey: ['preset', variables.id] })
    },
  })
}

export function useDeletePreset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deletePreset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['presets'] })
    },
  })
}

export function formatFrequencyMHz(hz: number): string {
  return `${(hz / 1e6).toFixed(3)} MHz`
}

export function formatFrequencyRange(startHz: number, stopHz: number): string {
  return `${(startHz / 1e6).toFixed(3)} - ${(stopHz / 1e6).toFixed(3)} MHz`
}
