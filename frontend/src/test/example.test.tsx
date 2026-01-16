import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

// Simple component for testing the setup
function ExampleComponent({ message }: { message: string }) {
  return <div role="alert">{message}</div>
}

describe('Vitest setup', () => {
  it('works with testing-library/react', () => {
    render(<ExampleComponent message="Hello, Vitest!" />)

    expect(screen.getByRole('alert')).toHaveTextContent('Hello, Vitest!')
  })

  it('supports jest-dom matchers', () => {
    render(<ExampleComponent message="Testing matchers" />)

    const element = screen.getByRole('alert')
    expect(element).toBeInTheDocument()
    expect(element).toBeVisible()
  })
})
