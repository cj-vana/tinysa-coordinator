import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach, type Mock } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import PresetList from '../presets/PresetList'
import type { Preset, PresetListResponse } from '../../hooks/usePresets'

// Mock the usePresets hooks
vi.mock('../../hooks/usePresets', async () => {
  const actual = await vi.importActual('../../hooks/usePresets')
  return {
    ...actual,
    usePresets: vi.fn(),
    useDeletePreset: vi.fn(),
    useCreatePreset: vi.fn(() => ({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
    })),
    useUpdatePreset: vi.fn(() => ({
      mutate: vi.fn(),
      mutateAsync: vi.fn(),
      isPending: false,
    })),
  }
})

// Import after mocking
import { usePresets, useDeletePreset } from '../../hooks/usePresets'

// Create a wrapper with QueryClientProvider for testing
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
  }
}

function renderWithClient(ui: ReactNode) {
  return render(ui, { wrapper: createWrapper() })
}

const mockPresets: Preset[] = [
  {
    id: 1,
    name: 'UHF TV Band',
    description: 'Standard UHF TV frequencies',
    start_freq_hz: 470000000,
    stop_freq_hz: 698000000,
    points: 450,
    rbw_khz: 100,
    category: 'UHF',
    is_builtin: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'VHF Band',
    description: 'VHF frequency range',
    start_freq_hz: 174000000,
    stop_freq_hz: 216000000,
    points: 300,
    rbw_khz: 50,
    category: 'VHF',
    is_builtin: false,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 3,
    name: 'Custom Range',
    description: null,
    start_freq_hz: 900000000,
    stop_freq_hz: 930000000,
    points: 200,
    rbw_khz: null,
    category: 'Custom',
    is_builtin: false,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
]

const mockPresetResponse: PresetListResponse = {
  items: mockPresets,
  total: 3,
  page: 1,
  per_page: 20,
}

describe('PresetList', () => {
  const mockDeleteMutate = vi.fn()
  const mockDeleteMutateAsync = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    // Default mock implementations
    ;(usePresets as Mock).mockReturnValue({
      data: mockPresetResponse,
      isLoading: false,
      error: null,
    })

    ;(useDeletePreset as Mock).mockReturnValue({
      mutate: mockDeleteMutate,
      mutateAsync: mockDeleteMutateAsync,
      isPending: false,
    })
  })

  describe('Rendering Presets', () => {
    it('renders the list of presets', () => {
      renderWithClient(<PresetList />)

      expect(screen.getByText('UHF TV Band')).toBeInTheDocument()
      expect(screen.getByText('VHF Band')).toBeInTheDocument()
      expect(screen.getByText('Custom Range')).toBeInTheDocument()
    })

    it('renders preset descriptions', () => {
      renderWithClient(<PresetList />)

      expect(screen.getByText('Standard UHF TV frequencies')).toBeInTheDocument()
      expect(screen.getByText('VHF frequency range')).toBeInTheDocument()
    })

    it('renders preset categories on cards', () => {
      renderWithClient(<PresetList />)

      // Category badges appear on preset cards (as span elements with specific classes)
      // Use getAllByText since categories also appear in filter buttons
      const uhfElements = screen.getAllByText('UHF')
      const vhfElements = screen.getAllByText('VHF')
      const customElements = screen.getAllByText('Custom')

      // There should be at least 2 UHF elements (filter button + preset card badge)
      expect(uhfElements.length).toBeGreaterThanOrEqual(2)
      expect(vhfElements.length).toBeGreaterThanOrEqual(2)
      expect(customElements.length).toBeGreaterThanOrEqual(2)
    })

    it('displays loading state', () => {
      ;(usePresets as Mock).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      })

      renderWithClient(<PresetList />)

      // Check for loading spinner (div with animate-spin class)
      const spinner = document.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('displays error state', () => {
      ;(usePresets as Mock).mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Network error'),
      })

      renderWithClient(<PresetList />)

      expect(screen.getByText(/Failed to load presets/)).toBeInTheDocument()
      expect(screen.getByText(/Network error/)).toBeInTheDocument()
    })

    it('displays empty state when no presets exist', () => {
      ;(usePresets as Mock).mockReturnValue({
        data: { items: [], total: 0, page: 1, per_page: 20 },
        isLoading: false,
        error: null,
      })

      renderWithClient(<PresetList />)

      expect(screen.getByText('No presets found.')).toBeInTheDocument()
      expect(screen.getByText('Create your first preset')).toBeInTheDocument()
    })
  })

  describe('Add Preset Button', () => {
    it('renders the Add Preset button', () => {
      renderWithClient(<PresetList />)

      expect(screen.getByRole('button', { name: /Add Preset/i })).toBeInTheDocument()
    })

    it('opens preset form when Add Preset is clicked', async () => {
      renderWithClient(<PresetList />)

      const addButton = screen.getByRole('button', { name: /Add Preset/i })
      fireEvent.click(addButton)

      // The PresetForm should open - look for the modal heading
      expect(await screen.findByRole('heading', { name: 'Create Preset' })).toBeInTheDocument()
    })

    it('opens preset form when "Create your first preset" is clicked in empty state', async () => {
      ;(usePresets as Mock).mockReturnValue({
        data: { items: [], total: 0, page: 1, per_page: 20 },
        isLoading: false,
        error: null,
      })

      renderWithClient(<PresetList />)

      const createLink = screen.getByText('Create your first preset')
      fireEvent.click(createLink)

      // The PresetForm should open - look for the modal heading
      expect(await screen.findByRole('heading', { name: 'Create Preset' })).toBeInTheDocument()
    })
  })

  describe('Preset Selection', () => {
    it('calls onSelectPreset when a preset is clicked', () => {
      const onSelectPreset = vi.fn()
      renderWithClient(<PresetList onSelectPreset={onSelectPreset} />)

      const presetCard = screen.getByText('UHF TV Band').closest('div[class*="cursor-pointer"]')
      expect(presetCard).toBeInTheDocument()
      fireEvent.click(presetCard!)

      expect(onSelectPreset).toHaveBeenCalledWith(mockPresets[0])
    })

    it('highlights the selected preset', () => {
      renderWithClient(<PresetList selectedPresetId={1} />)

      // The selected preset should have a different border/background
      const presetCard = screen.getByText('UHF TV Band').closest('div[class*="cursor-pointer"]')
      expect(presetCard).toHaveClass('border-blue-500')
    })

    it('does not highlight unselected presets', () => {
      renderWithClient(<PresetList selectedPresetId={1} />)

      const vhfCard = screen.getByText('VHF Band').closest('div[class*="cursor-pointer"]')
      expect(vhfCard).not.toHaveClass('border-blue-500')
    })
  })

  describe('Category Filtering', () => {
    it('renders all category filter buttons', () => {
      renderWithClient(<PresetList />)

      expect(screen.getByRole('button', { name: 'All' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'UHF' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'VHF' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'ISM' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Custom' })).toBeInTheDocument()
    })

    it('calls usePresets with category when filter is clicked', () => {
      renderWithClient(<PresetList />)

      const uhfFilter = screen.getByRole('button', { name: 'UHF' })
      fireEvent.click(uhfFilter)

      // Check that usePresets was called with the category
      expect(usePresets).toHaveBeenLastCalledWith('UHF')
    })

    it('calls usePresets with undefined when All filter is clicked', () => {
      renderWithClient(<PresetList />)

      // First click a specific category
      const uhfFilter = screen.getByRole('button', { name: 'UHF' })
      fireEvent.click(uhfFilter)

      // Then click All
      const allFilter = screen.getByRole('button', { name: 'All' })
      fireEvent.click(allFilter)

      expect(usePresets).toHaveBeenLastCalledWith(undefined)
    })
  })

  describe('Delete Preset', () => {
    it('shows delete confirmation dialog when delete is clicked', async () => {
      renderWithClient(<PresetList />)

      // Find the VHF Band preset card (not built-in, has delete button)
      const vhfCard = screen.getByText('VHF Band').closest('div[class*="rounded-lg"]')
      const deleteButton = vhfCard?.querySelector('button[class*="bg-red"]')

      expect(deleteButton).toBeInTheDocument()
      fireEvent.click(deleteButton!)

      expect(screen.getByText('Delete Preset')).toBeInTheDocument()
      expect(screen.getByText(/Are you sure you want to delete "VHF Band"/)).toBeInTheDocument()
    })

    it('calls delete mutation when confirmed', async () => {
      mockDeleteMutateAsync.mockResolvedValue(undefined)

      renderWithClient(<PresetList />)

      // Click delete on VHF Band preset
      const vhfCard = screen.getByText('VHF Band').closest('div[class*="rounded-lg"]')
      const deleteButton = vhfCard?.querySelector('button[class*="bg-red"]')
      fireEvent.click(deleteButton!)

      // Wait for the confirmation dialog to appear
      await screen.findByText('Delete Preset')

      // Click the Delete button in the confirmation dialog (it's in the modal with bg-red-600)
      const dialog = screen.getByText('Delete Preset').closest('div[class*="relative"]')
      const confirmDeleteButton = dialog?.querySelector('button[class*="bg-red-600"]')
      expect(confirmDeleteButton).toBeInTheDocument()
      fireEvent.click(confirmDeleteButton!)

      await waitFor(() => {
        expect(mockDeleteMutateAsync).toHaveBeenCalledWith(2)
      })
    })

    it('closes confirmation dialog when cancel is clicked', () => {
      renderWithClient(<PresetList />)

      // Click delete on VHF Band preset
      const vhfCard = screen.getByText('VHF Band').closest('div[class*="rounded-lg"]')
      const deleteButton = vhfCard?.querySelector('button[class*="bg-red"]')
      fireEvent.click(deleteButton!)

      // Click cancel
      const cancelButton = screen.getByRole('button', { name: 'Cancel' })
      fireEvent.click(cancelButton)

      // Dialog should be closed
      expect(screen.queryByText('Delete Preset')).not.toBeInTheDocument()
    })

    it('does not show delete button for built-in presets', () => {
      renderWithClient(<PresetList />)

      // Find the UHF TV Band preset card (built-in)
      const uhfCard = screen.getByText('UHF TV Band').closest('div[class*="rounded-lg"]')
      const deleteButton = uhfCard?.querySelector('button[class*="bg-red"]')

      expect(deleteButton).not.toBeInTheDocument()
    })
  })

  describe('Edit Preset', () => {
    it('opens edit form when edit button is clicked', () => {
      renderWithClient(<PresetList />)

      // Find the VHF Band preset card (not built-in, has edit button)
      const vhfCard = screen.getByText('VHF Band').closest('div[class*="rounded-lg"]')
      const editButton = vhfCard?.querySelector('button[class*="bg-gray-700"]')

      expect(editButton).toBeInTheDocument()
      fireEvent.click(editButton!)

      // Should open the edit form
      expect(screen.getByText('Edit Preset')).toBeInTheDocument()
    })

    it('does not show edit button for built-in presets', () => {
      renderWithClient(<PresetList />)

      // Find the UHF TV Band preset card (built-in)
      const uhfCard = screen.getByText('UHF TV Band').closest('div[class*="rounded-lg"]')

      // There should be no Edit button in the card
      const buttons = uhfCard?.querySelectorAll('button')
      const editButton = Array.from(buttons || []).find(btn => btn.textContent === 'Edit')

      expect(editButton).toBeUndefined()
    })
  })
})
