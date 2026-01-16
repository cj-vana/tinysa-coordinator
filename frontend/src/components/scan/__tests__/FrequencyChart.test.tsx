import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import FrequencyChart from '../FrequencyChart'
import type { ScanPoint } from '../../../lib/websocket'

// Mock ResizeObserver which is used by Recharts
class ResizeObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

vi.stubGlobal('ResizeObserver', ResizeObserverMock)

// Mock Recharts components since they don't render well in jsdom
vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  ReferenceDot: ({ x, y }: { x: number; y: number }) => (
    <div data-testid="reference-dot" data-x={x} data-y={y} />
  ),
}))

describe('FrequencyChart', () => {
  const mockScanData: ScanPoint[] = [
    { index: 0, frequency_hz: 470000000, amplitude_dbm: -80 },
    { index: 1, frequency_hz: 475000000, amplitude_dbm: -75 },
    { index: 2, frequency_hz: 480000000, amplitude_dbm: -60 },
    { index: 3, frequency_hz: 485000000, amplitude_dbm: -70 },
    { index: 4, frequency_hz: 490000000, amplitude_dbm: -85 },
  ]

  const peakPoint: ScanPoint = {
    index: 2,
    frequency_hz: 480000000,
    amplitude_dbm: -60,
  }

  describe('rendering with data', () => {
    it('renders the chart title', () => {
      render(
        <FrequencyChart data={mockScanData} peakPoint={peakPoint} isScanning={false} />
      )

      expect(screen.getByText('Frequency Spectrum')).toBeInTheDocument()
    })

    it('renders the chart container with data', () => {
      render(
        <FrequencyChart data={mockScanData} peakPoint={peakPoint} isScanning={false} />
      )

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    })

    it('displays peak information when peak point is provided', () => {
      render(
        <FrequencyChart data={mockScanData} peakPoint={peakPoint} isScanning={false} />
      )

      expect(screen.getByText('Peak:')).toBeInTheDocument()
      expect(screen.getByText('480.0 MHz')).toBeInTheDocument()
      expect(screen.getByText('-60.0 dBm')).toBeInTheDocument()
    })

    it('renders a reference dot for the peak point', () => {
      render(
        <FrequencyChart data={mockScanData} peakPoint={peakPoint} isScanning={false} />
      )

      const referenceDot = screen.getByTestId('reference-dot')
      expect(referenceDot).toBeInTheDocument()
      expect(referenceDot).toHaveAttribute('data-x', String(peakPoint.frequency_hz))
      expect(referenceDot).toHaveAttribute('data-y', String(peakPoint.amplitude_dbm))
    })

    it('does not show peak info when peakPoint is null', () => {
      render(
        <FrequencyChart data={mockScanData} peakPoint={null} isScanning={false} />
      )

      expect(screen.queryByText('Peak:')).not.toBeInTheDocument()
    })
  })

  describe('rendering with empty data', () => {
    it('shows empty state message when no data', () => {
      render(
        <FrequencyChart data={[]} peakPoint={null} isScanning={false} />
      )

      expect(screen.getByText('No scan data')).toBeInTheDocument()
      expect(screen.getByText('Start a scan to see the frequency spectrum')).toBeInTheDocument()
    })

    it('does not render the chart when no data', () => {
      render(
        <FrequencyChart data={[]} peakPoint={null} isScanning={false} />
      )

      expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument()
    })
  })

  describe('scanning indicator', () => {
    it('shows scanning indicator when isScanning is true', () => {
      render(
        <FrequencyChart data={mockScanData} peakPoint={peakPoint} isScanning={true} />
      )

      expect(screen.getByText('Scanning...')).toBeInTheDocument()
    })

    it('does not show scanning indicator when isScanning is false', () => {
      render(
        <FrequencyChart data={mockScanData} peakPoint={peakPoint} isScanning={false} />
      )

      expect(screen.queryByText('Scanning...')).not.toBeInTheDocument()
    })

    it('shows scanning indicator even with empty data', () => {
      render(
        <FrequencyChart data={[]} peakPoint={null} isScanning={true} />
      )

      expect(screen.getByText('Scanning...')).toBeInTheDocument()
    })
  })

  describe('frequency formatting', () => {
    it('formats MHz frequencies correctly in peak display', () => {
      const dataWithMhzFreq: ScanPoint[] = [
        { index: 0, frequency_hz: 500000000, amplitude_dbm: -50 },
      ]
      const peakMhz: ScanPoint = { index: 0, frequency_hz: 500000000, amplitude_dbm: -50 }

      render(
        <FrequencyChart data={dataWithMhzFreq} peakPoint={peakMhz} isScanning={false} />
      )

      expect(screen.getByText('500.0 MHz')).toBeInTheDocument()
    })

    it('formats GHz frequencies correctly in peak display', () => {
      const dataWithGhzFreq: ScanPoint[] = [
        { index: 0, frequency_hz: 2400000000, amplitude_dbm: -50 },
      ]
      const peakGhz: ScanPoint = { index: 0, frequency_hz: 2400000000, amplitude_dbm: -50 }

      render(
        <FrequencyChart data={dataWithGhzFreq} peakPoint={peakGhz} isScanning={false} />
      )

      expect(screen.getByText('2.40 GHz')).toBeInTheDocument()
    })
  })
})
