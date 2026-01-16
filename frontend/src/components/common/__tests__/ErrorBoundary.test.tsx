import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ErrorBoundary, ErrorFallback } from '../ErrorBoundary'

// Component that throws an error for testing
function ThrowingComponent({ shouldThrow = true }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>No error</div>
}

describe('ErrorBoundary', () => {
  // Suppress console.error for cleaner test output
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  describe('Error Catching', () => {
    it('renders children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>Child content</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('Child content')).toBeInTheDocument()
    })

    it('renders fallback UI when error is thrown', () => {
      render(
        <ErrorBoundary>
          <ThrowingComponent />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      // Error message is inside a collapsed details element, verify it's present
      expect(screen.getByText('Error details')).toBeInTheDocument()
      // Expand details to verify error message
      fireEvent.click(screen.getByText('Error details'))
      expect(screen.getByText(/Test error message/)).toBeInTheDocument()
    })

    it('renders custom fallback when provided', () => {
      render(
        <ErrorBoundary fallback={<div>Custom fallback</div>}>
          <ThrowingComponent />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom fallback')).toBeInTheDocument()
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
    })

    it('calls onError callback when error occurs', () => {
      const onError = vi.fn()

      render(
        <ErrorBoundary onError={onError}>
          <ThrowingComponent />
        </ErrorBoundary>
      )

      expect(onError).toHaveBeenCalledTimes(1)
      expect(onError.mock.calls[0][0]).toBeInstanceOf(Error)
      expect(onError.mock.calls[0][0].message).toBe('Test error message')
    })
  })

  describe('Error Reset', () => {
    it('calls onReset callback when reset is triggered', () => {
      const onReset = vi.fn()

      render(
        <ErrorBoundary onReset={onReset}>
          <ThrowingComponent />
        </ErrorBoundary>
      )

      fireEvent.click(screen.getByText('Try again'))

      expect(onReset).toHaveBeenCalledTimes(1)
    })
  })
})

describe('ErrorFallback', () => {
  describe('Default Display', () => {
    it('renders with default title', () => {
      render(<ErrorFallback error={null} />)

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('renders with custom title', () => {
      render(<ErrorFallback error={null} title="Custom error title" />)

      expect(screen.getByText('Custom error title')).toBeInTheDocument()
    })

    it('displays error message when error is provided', () => {
      const error = new Error('Detailed error message')

      render(<ErrorFallback error={error} />)

      // Error message is inside a collapsed details element
      expect(screen.getByText('Error details')).toBeInTheDocument()
      // Expand details to verify error message
      fireEvent.click(screen.getByText('Error details'))
      expect(screen.getByText(/Detailed error message/)).toBeInTheDocument()
    })

    it('shows reload page button', () => {
      render(<ErrorFallback error={null} />)

      expect(screen.getByText('Reload page')).toBeInTheDocument()
    })
  })

  describe('Reset Button', () => {
    it('shows try again button when onReset is provided', () => {
      const onReset = vi.fn()

      render(<ErrorFallback error={null} onReset={onReset} />)

      expect(screen.getByText('Try again')).toBeInTheDocument()
    })

    it('does not show try again button when onReset is not provided', () => {
      render(<ErrorFallback error={null} />)

      expect(screen.queryByText('Try again')).not.toBeInTheDocument()
    })

    it('calls onReset when try again is clicked', () => {
      const onReset = vi.fn()

      render(<ErrorFallback error={null} onReset={onReset} />)
      fireEvent.click(screen.getByText('Try again'))

      expect(onReset).toHaveBeenCalledTimes(1)
    })
  })

  describe('Compact Mode', () => {
    it('renders compact UI when compact prop is true', () => {
      render(<ErrorFallback error={null} compact />)

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
      // In compact mode, the description text is not shown
      expect(
        screen.queryByText('An unexpected error occurred while rendering this component.')
      ).not.toBeInTheDocument()
    })

    it('shows error message in compact mode', () => {
      const error = new Error('Compact error')

      render(<ErrorFallback error={error} compact />)

      expect(screen.getByText('Compact error')).toBeInTheDocument()
    })

    it('shows try again link in compact mode when onReset provided', () => {
      const onReset = vi.fn()

      render(<ErrorFallback error={null} onReset={onReset} compact />)
      fireEvent.click(screen.getByText('Try again'))

      expect(onReset).toHaveBeenCalledTimes(1)
    })
  })

  describe('Error Details', () => {
    it('displays error stack in details when available', () => {
      const error = new Error('Error with stack')
      error.stack = 'at Component\n  at App'

      render(<ErrorFallback error={error} />)

      // Click to expand details
      fireEvent.click(screen.getByText('Error details'))

      expect(screen.getByText(/at Component/)).toBeInTheDocument()
    })
  })
})
