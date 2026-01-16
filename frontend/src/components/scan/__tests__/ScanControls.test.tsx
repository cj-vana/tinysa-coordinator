import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ScanControls from '../ScanControls'
import type { ScanConfig } from '../../../hooks/useScanData'

// Create a wrapper with React Query provider
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  })
}

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = createTestQueryClient()
  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    ),
    queryClient,
  }
}

// Mock fetch for presets API
const mockPresets = [
  {
    id: 1,
    name: 'UHF TV Band',
    category: 'TV',
    start_freq_hz: 470000000,
    stop_freq_hz: 698000000,
    points: 450,
    rbw_khz: null,
  },
  {
    id: 2,
    name: 'WiFi 2.4GHz',
    category: 'WiFi',
    start_freq_hz: 2400000000,
    stop_freq_hz: 2500000000,
    points: 225,
    rbw_khz: 100,
  },
]

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ items: mockPresets }),
    })
  ))
})

// Helper functions to find inputs by their label text (since component doesn't use htmlFor)
function findInputByLabelText(container: HTMLElement, labelText: string): HTMLInputElement | null {
  const labels = container.querySelectorAll('label')
  for (const label of labels) {
    if (label.textContent?.includes(labelText)) {
      const parent = label.parentElement
      if (parent) {
        const input = parent.querySelector('input')
        if (input) return input
      }
    }
  }
  return null
}

function findSelectByLabelText(container: HTMLElement, labelText: string): HTMLSelectElement | null {
  const labels = container.querySelectorAll('label')
  for (const label of labels) {
    if (label.textContent?.includes(labelText)) {
      const parent = label.parentElement
      if (parent) {
        const select = parent.querySelector('select')
        if (select) return select
      }
    }
  }
  return null
}

describe('ScanControls', () => {
  const mockOnStartScan = vi.fn()
  const mockOnStopScan = vi.fn()

  const defaultProps = {
    onStartScan: mockOnStartScan,
    onStopScan: mockOnStopScan,
    isScanning: false,
    wsStatus: 'connected' as const,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders the component title', () => {
      renderWithQueryClient(<ScanControls {...defaultProps} />)

      expect(screen.getByText('Scan Controls')).toBeInTheDocument()
    })

    it('renders frequency input fields', () => {
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      expect(screen.getByText('Start Frequency (MHz)')).toBeInTheDocument()
      expect(screen.getByText('Stop Frequency (MHz)')).toBeInTheDocument()
      expect(findInputByLabelText(container, 'Start Frequency')).toBeInTheDocument()
      expect(findInputByLabelText(container, 'Stop Frequency')).toBeInTheDocument()
    })

    it('renders points selector', () => {
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      expect(screen.getByText('Points')).toBeInTheDocument()
      expect(findSelectByLabelText(container, 'Points')).toBeInTheDocument()
    })

    it('renders RBW input', () => {
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      expect(screen.getByText('RBW (kHz)')).toBeInTheDocument()
      expect(findInputByLabelText(container, 'RBW')).toBeInTheDocument()
    })

    it('renders preset selector', () => {
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      expect(screen.getByText('Preset')).toBeInTheDocument()
      expect(findSelectByLabelText(container, 'Preset')).toBeInTheDocument()
    })
  })

  describe('start/stop buttons', () => {
    it('shows Start Scan button when not scanning', () => {
      renderWithQueryClient(<ScanControls {...defaultProps} />)

      expect(screen.getByRole('button', { name: 'Start Scan' })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: 'Stop Scan' })).not.toBeInTheDocument()
    })

    it('shows Stop Scan button when scanning', () => {
      renderWithQueryClient(
        <ScanControls {...defaultProps} isScanning={true} />
      )

      expect(screen.getByRole('button', { name: 'Stop Scan' })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: 'Start Scan' })).not.toBeInTheDocument()
    })

    it('disables Start Scan button when disconnected', () => {
      renderWithQueryClient(
        <ScanControls {...defaultProps} wsStatus="disconnected" />
      )

      expect(screen.getByRole('button', { name: 'Start Scan' })).toBeDisabled()
    })

    it('enables Start Scan button when connected', () => {
      renderWithQueryClient(<ScanControls {...defaultProps} />)

      expect(screen.getByRole('button', { name: 'Start Scan' })).toBeEnabled()
    })

    it('calls onStartScan with config when Start Scan is clicked', async () => {
      const user = userEvent.setup()
      renderWithQueryClient(<ScanControls {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: 'Start Scan' }))

      expect(mockOnStartScan).toHaveBeenCalledTimes(1)
      expect(mockOnStartScan).toHaveBeenCalledWith(
        expect.objectContaining({
          start_freq_hz: expect.any(Number),
          stop_freq_hz: expect.any(Number),
          points: expect.any(Number),
        })
      )
    })

    it('calls onStopScan when Stop Scan is clicked', async () => {
      const user = userEvent.setup()
      renderWithQueryClient(
        <ScanControls {...defaultProps} isScanning={true} />
      )

      await user.click(screen.getByRole('button', { name: 'Stop Scan' }))

      expect(mockOnStopScan).toHaveBeenCalledTimes(1)
    })
  })

  describe('frequency inputs', () => {
    it('allows changing start frequency', async () => {
      const user = userEvent.setup()
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      const startInput = findInputByLabelText(container, 'Start Frequency')!
      await user.clear(startInput)
      await user.type(startInput, '500')

      expect(startInput).toHaveValue(500)
    })

    it('allows changing stop frequency', async () => {
      const user = userEvent.setup()
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      const stopInput = findInputByLabelText(container, 'Stop Frequency')!
      await user.clear(stopInput)
      await user.type(stopInput, '800')

      expect(stopInput).toHaveValue(800)
    })

    it('shows validation error when start >= stop frequency', async () => {
      const user = userEvent.setup()
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      const startInput = findInputByLabelText(container, 'Start Frequency')!
      const stopInput = findInputByLabelText(container, 'Stop Frequency')!

      await user.clear(startInput)
      await user.type(startInput, '700')
      await user.clear(stopInput)
      await user.type(stopInput, '500')

      expect(screen.getByText(/Stop frequency must be greater than start frequency/i)).toBeInTheDocument()
    })

    it('disables Start Scan button when frequencies are invalid', async () => {
      const user = userEvent.setup()
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      const startInput = findInputByLabelText(container, 'Start Frequency')!
      const stopInput = findInputByLabelText(container, 'Stop Frequency')!

      await user.clear(startInput)
      await user.type(startInput, '700')
      await user.clear(stopInput)
      await user.type(stopInput, '500')

      expect(screen.getByRole('button', { name: 'Start Scan' })).toBeDisabled()
    })

    it('disables inputs when scanning', () => {
      const { container } = renderWithQueryClient(
        <ScanControls {...defaultProps} isScanning={true} />
      )

      expect(findInputByLabelText(container, 'Start Frequency')).toBeDisabled()
      expect(findInputByLabelText(container, 'Stop Frequency')).toBeDisabled()
      expect(findSelectByLabelText(container, 'Points')).toBeDisabled()
      expect(findInputByLabelText(container, 'RBW')).toBeDisabled()
    })
  })

  describe('connection status', () => {
    it('displays connected status', () => {
      renderWithQueryClient(
        <ScanControls {...defaultProps} wsStatus="connected" />
      )

      expect(screen.getByText('connected')).toBeInTheDocument()
    })

    it('displays disconnected status', () => {
      renderWithQueryClient(
        <ScanControls {...defaultProps} wsStatus="disconnected" />
      )

      expect(screen.getByText('disconnected')).toBeInTheDocument()
    })

    it('displays connecting status', () => {
      renderWithQueryClient(
        <ScanControls {...defaultProps} wsStatus="connecting" />
      )

      expect(screen.getByText('connecting')).toBeInTheDocument()
    })

    it('displays error status', () => {
      renderWithQueryClient(
        <ScanControls {...defaultProps} wsStatus="error" />
      )

      expect(screen.getByText('error')).toBeInTheDocument()
    })
  })

  describe('points selector', () => {
    it('allows selecting different point values', async () => {
      const user = userEvent.setup()
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      const pointsSelect = findSelectByLabelText(container, 'Points')!
      await user.selectOptions(pointsSelect, '900')

      expect(pointsSelect).toHaveValue('900')
    })

    it('includes correct point options', () => {
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      const pointsSelect = findSelectByLabelText(container, 'Points')!
      const options = Array.from(pointsSelect.querySelectorAll('option'))
      const values = options.map(opt => opt.value)

      expect(values).toContain('100')
      expect(values).toContain('225')
      expect(values).toContain('450')
      expect(values).toContain('900')
      expect(values).toContain('1800')
    })
  })

  describe('scan config', () => {
    it('passes correct config to onStartScan', async () => {
      const user = userEvent.setup()
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      // Set custom values
      const startInput = findInputByLabelText(container, 'Start Frequency')!
      const stopInput = findInputByLabelText(container, 'Stop Frequency')!
      const rbwInput = findInputByLabelText(container, 'RBW')!

      await user.clear(startInput)
      await user.type(startInput, '500')
      await user.clear(stopInput)
      await user.type(stopInput, '600')
      await user.type(rbwInput, '50')

      await user.click(screen.getByRole('button', { name: 'Start Scan' }))

      const expectedConfig: ScanConfig = {
        start_freq_hz: 500000000,
        stop_freq_hz: 600000000,
        points: 450,
        rbw_khz: 50,
      }

      expect(mockOnStartScan).toHaveBeenCalledWith(expectedConfig)
    })

    it('does not include rbw_khz when empty', async () => {
      const user = userEvent.setup()
      renderWithQueryClient(<ScanControls {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: 'Start Scan' }))

      expect(mockOnStartScan).toHaveBeenCalledWith(
        expect.not.objectContaining({ rbw_khz: expect.anything() })
      )
    })
  })

  describe('presets', () => {
    it('loads presets from API', async () => {
      renderWithQueryClient(<ScanControls {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByRole('option', { name: /UHF TV Band/i })).toBeInTheDocument()
      })
    })

    it('applies preset values when selected', async () => {
      const user = userEvent.setup()
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      // Wait for presets to load
      await waitFor(() => {
        expect(screen.getByRole('option', { name: /UHF TV Band/i })).toBeInTheDocument()
      })

      const presetSelect = findSelectByLabelText(container, 'Preset')!
      await user.selectOptions(presetSelect, '1')

      const startInput = findInputByLabelText(container, 'Start Frequency')!
      const stopInput = findInputByLabelText(container, 'Stop Frequency')!

      expect(startInput).toHaveValue(470)
      expect(stopInput).toHaveValue(698)
    })

    it('has Custom Range option as default', () => {
      const { container } = renderWithQueryClient(<ScanControls {...defaultProps} />)

      const presetSelect = findSelectByLabelText(container, 'Preset')!
      expect(presetSelect).toHaveValue('')
      expect(screen.getByRole('option', { name: 'Custom Range' })).toBeInTheDocument()
    })
  })
})
