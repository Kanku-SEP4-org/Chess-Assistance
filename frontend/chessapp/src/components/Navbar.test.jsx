import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, test } from 'vitest'
import Navbar from './Navbar'

function renderNavbar() {
  return render(
    <MemoryRouter>
      <Navbar />
    </MemoryRouter>
  )
}

beforeEach(() => {
  localStorage.clear()
})

describe('Navbar', () => {
  test('renders logo text and nav links', () => {
    renderNavbar()
    expect(screen.getByText('ChessTrack™')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /chesstrack/i })).toBeInTheDocument()
  })

  test('profile dropdown is hidden by default', () => {
    renderNavbar()
    expect(screen.queryByText(/login/i)).not.toBeInTheDocument()
  })

  test('opens profile dropdown on settings button click', () => {
    renderNavbar()
    const settingsBtn = screen.getByRole('button')
    fireEvent.click(settingsBtn)
    expect(screen.getByRole('link', { name: /login/i })).toBeInTheDocument()
  })

  test('closes profile dropdown on second click', () => {
    renderNavbar()
    const settingsBtn = screen.getByRole('button')
    fireEvent.click(settingsBtn)
    fireEvent.click(settingsBtn)
    expect(screen.queryByRole('link', { name: /login/i })).not.toBeInTheDocument()
  })

  test('shows login link when no user is stored', () => {
    renderNavbar()
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByRole('link', { name: /login/i })).toBeInTheDocument()
  })

  test('shows username when lichess user is in localStorage', () => {
    localStorage.setItem(
      'lichess_user',
      JSON.stringify({ player_username: 'Magnus' })
    )
    renderNavbar()
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByText(/Magnus/)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /login/i })).not.toBeInTheDocument()
  })

  test('logout button removes user from localStorage and hides username', () => {
    localStorage.setItem(
      'lichess_user',
      JSON.stringify({ player_username: 'Magnus' })
    )
    renderNavbar()
    fireEvent.click(screen.getByRole('button'))
    fireEvent.click(screen.getByText(/logout/i))
    expect(localStorage.getItem('lichess_user')).toBeNull()
    expect(screen.queryByText(/Magnus/)).not.toBeInTheDocument()
  })

  test('IoT Dashboard link is present in dropdown', () => {
    renderNavbar()
    fireEvent.click(screen.getByRole('button'))
    expect(screen.getByRole('link', { name: /iot dashboard/i })).toBeInTheDocument()
  })
})
