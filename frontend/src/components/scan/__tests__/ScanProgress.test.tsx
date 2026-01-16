import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ScanProgress from '../ScanProgress'

describe('ScanProgress', () => {
  const defaultProps = {
    progress: 0,
    totalPoints: 450,
    currentPoints: 0,
    isScanning: false,
    scanDuration: null,
    error: null,
  }

  describe('progress bar rendering', () => {
    it('renders progress percentage', () => {
      render(<ScanProgress {...defaultProps} progress={50} />)

      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('renders 0% progress initially', () => {
      render(<ScanProgress {...defaultProps} />)

      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('renders 100% progress when complete', () => {
      render(<ScanProgress {...defaultProps} progress={100} />)

      expect(screen.getByText('100%')).toBeInTheDocument()
    })

    it('applies correct width style to progress bar', () => {
      const { container } = render(<ScanProgress {...defaultProps} progress={75} />)

      // Find the inner progress bar div
      const progressBar = container.querySelector('[style*="width: 75%"]')
      expect(progressBar).toBeInTheDocument()
    })
  })

  describe('status text', () => {
    it('shows "Ready" when not scanning and progress is 0', () => {
      render(<ScanProgress {...defaultProps} />)

      expect(screen.getByText('Ready')).toBeInTheDocument()
    })

    it('shows "Scanning..." when isScanning is true', () => {
      render(<ScanProgress {...defaultProps} isScanning={true} progress={25} />)

      expect(screen.getByText('Scanning...')).toBeInTheDocument()
    })

    it('shows "Complete" when progress is 100 and not scanning', () => {
      render(<ScanProgress {...defaultProps} progress={100} />)

      expect(screen.getByText('Complete')).toBeInTheDocument()
    })
  })

  describe('points display', () => {
    it('displays current and total points', () => {
      render(
        <ScanProgress
          {...defaultProps}
          currentPoints={225}
          totalPoints={450}
        />
      )

      expect(screen.getByText('225 / 450')).toBeInTheDocument()
    })

    it('displays dash when totalPoints is 0', () => {
      render(
        <ScanProgress
          {...defaultProps}
          currentPoints={0}
          totalPoints={0}
        />
      )

      expect(screen.getByText('0 / -')).toBeInTheDocument()
    })

    it('shows Points label', () => {
      render(<ScanProgress {...defaultProps} />)

      expect(screen.getByText('Points:')).toBeInTheDocument()
    })
  })

  describe('duration display', () => {
    it('does not show duration when null', () => {
      render(<ScanProgress {...defaultProps} />)

      expect(screen.queryByText('Duration:')).not.toBeInTheDocument()
    })

    it('shows duration in milliseconds when less than 1 second', () => {
      render(<ScanProgress {...defaultProps} scanDuration={500} />)

      expect(screen.getByText('Duration:')).toBeInTheDocument()
      expect(screen.getByText('500ms')).toBeInTheDocument()
    })

    it('shows duration in seconds when 1 second or more', () => {
      render(<ScanProgress {...defaultProps} scanDuration={2500} />)

      expect(screen.getByText('Duration:')).toBeInTheDocument()
      expect(screen.getByText('2.5s')).toBeInTheDocument()
    })

    it('formats duration with one decimal place', () => {
      render(<ScanProgress {...defaultProps} scanDuration={3333} />)

      expect(screen.getByText('3.3s')).toBeInTheDocument()
    })
  })

  describe('error display', () => {
    it('does not show error container when error is null', () => {
      render(<ScanProgress {...defaultProps} />)

      expect(screen.queryByText('Scan Error')).not.toBeInTheDocument()
    })

    it('shows error message when error is provided', () => {
      render(
        <ScanProgress
          {...defaultProps}
          error="Device not connected"
        />
      )

      expect(screen.getByText('Scan Error')).toBeInTheDocument()
      expect(screen.getByText('Device not connected')).toBeInTheDocument()
    })

    it('displays different error messages', () => {
      render(
        <ScanProgress
          {...defaultProps}
          error="Timeout waiting for scan data"
        />
      )

      expect(screen.getByText('Timeout waiting for scan data')).toBeInTheDocument()
    })
  })

  describe('combined states', () => {
    it('shows scanning state with progress', () => {
      render(
        <ScanProgress
          {...defaultProps}
          isScanning={true}
          progress={50}
          currentPoints={225}
          totalPoints={450}
        />
      )

      expect(screen.getByText('Scanning...')).toBeInTheDocument()
      expect(screen.getByText('50%')).toBeInTheDocument()
      expect(screen.getByText('225 / 450')).toBeInTheDocument()
    })

    it('shows completed state with duration', () => {
      render(
        <ScanProgress
          {...defaultProps}
          progress={100}
          currentPoints={450}
          totalPoints={450}
          scanDuration={5000}
        />
      )

      expect(screen.getByText('Complete')).toBeInTheDocument()
      expect(screen.getByText('100%')).toBeInTheDocument()
      expect(screen.getByText('450 / 450')).toBeInTheDocument()
      expect(screen.getByText('5.0s')).toBeInTheDocument()
    })

    it('shows error state with partial progress', () => {
      render(
        <ScanProgress
          {...defaultProps}
          progress={30}
          currentPoints={135}
          totalPoints={450}
          error="Connection lost"
        />
      )

      expect(screen.getByText('30%')).toBeInTheDocument()
      expect(screen.getByText('135 / 450')).toBeInTheDocument()
      expect(screen.getByText('Scan Error')).toBeInTheDocument()
      expect(screen.getByText('Connection lost')).toBeInTheDocument()
    })
  })

  describe('progress bar styling', () => {
    it('applies blue color when scanning', () => {
      const { container } = render(
        <ScanProgress {...defaultProps} isScanning={true} progress={50} />
      )

      const progressBar = container.querySelector('.bg-blue-500')
      expect(progressBar).toBeInTheDocument()
    })

    it('applies green color when complete', () => {
      const { container } = render(
        <ScanProgress {...defaultProps} progress={100} />
      )

      const progressBar = container.querySelector('.bg-green-500')
      expect(progressBar).toBeInTheDocument()
    })

    it('applies gray color when ready (not scanning, not complete)', () => {
      const { container } = render(
        <ScanProgress {...defaultProps} progress={0} />
      )

      const progressBar = container.querySelector('.bg-gray-600')
      expect(progressBar).toBeInTheDocument()
    })
  })
})
