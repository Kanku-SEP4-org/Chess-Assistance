import { render, screen } from '@testing-library/react'
import { describe, expect, test } from 'vitest'
import App from './App'

describe('App', () => {
  test('renders home page by default', () => {
    render(<App />)
    expect(screen.getByText(/chess performance assistant/i)).toBeInTheDocument()
  })
})
