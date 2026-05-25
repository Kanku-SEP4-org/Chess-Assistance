import { render, screen, fireEvent, act } from '@testing-library/react'
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
  globalThis.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
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
    fireEvent.click(screen.getAllByRole('button', { name: /open menu/i })[0])
    expect(screen.getAllByRole('link', { name: /login/i })[0]).toBeInTheDocument()
  })

  test('closes profile dropdown on second click', () => {
    renderNavbar()
    const btn = screen.getAllByRole('button', { name: /open menu/i })[0]
    fireEvent.click(btn)
    fireEvent.click(btn)
    expect(screen.queryByRole('link', { name: /login/i })).not.toBeInTheDocument()
  })

  test('shows login link when no user is stored', () => {
    renderNavbar()
    fireEvent.click(screen.getAllByRole('button', { name: /open menu/i })[0])
    expect(screen.getAllByRole('link', { name: /login/i })[0]).toBeInTheDocument()
  })

  test('shows username when lichess user is in localStorage', () => {
    localStorage.setItem('lichess_user', JSON.stringify({ player_username: 'Magnus' }))
    renderNavbar()
    fireEvent.click(screen.getAllByRole('button', { name: /open menu/i })[0])
    expect(screen.getAllByText(/Magnus/)[0]).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /login/i })).not.toBeInTheDocument()
  })

  test('logout button removes user from localStorage and hides username', async () => {
    localStorage.setItem('lichess_user', JSON.stringify({ player_username: 'Magnus' }))
    renderNavbar()
    fireEvent.click(screen.getAllByRole('button', { name: /open menu/i })[0])
    await act(async () => {
      fireEvent.click(screen.getAllByText(/logout/i)[0])
    })
    expect(localStorage.getItem('lichess_user')).toBeNull()
    expect(screen.queryByText(/Magnus/)).not.toBeInTheDocument()
  })

  test('IoT Dashboard link is present in dropdown', () => {
    renderNavbar()
    fireEvent.click(screen.getAllByRole('button', { name: /open menu/i })[0])
    expect(screen.getAllByRole('link', { name: /iot dashboard/i })[0]).toBeInTheDocument()
  })

  test('hamburger button toggles collapsible nav visibility', () => {
    renderNavbar()
    const hamburger = screen.getByRole('button', { name: '' })
    fireEvent.click(hamburger)
    expect(document.querySelector('.navbar-collapse.show')).toBeInTheDocument()
    fireEvent.click(hamburger)
    expect(document.querySelector('.navbar-collapse.show')).not.toBeInTheDocument()
  })

  test('clicking a nav link closes the collapsible nav', () => {
    renderNavbar()
    const hamburger = screen.getByRole('button', { name: '' })
    fireEvent.click(hamburger)
    expect(document.querySelector('.navbar-collapse.show')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('link', { name: /home/i }))
    expect(document.querySelector('.navbar-collapse.show')).not.toBeInTheDocument()
  })

  test('desktop open menu button opens dropdown', () => {
    renderNavbar()
    fireEvent.click(screen.getAllByRole('button', { name: /open menu/i })[1])
    expect(screen.getAllByRole('link', { name: /iot dashboard/i })[0]).toBeInTheDocument()
  })

  test('logout with active session sends beacon and removes session id', async () => {
    localStorage.setItem('lichess_user', JSON.stringify({ player_username: 'Magnus' }))
    localStorage.setItem('active_session_id', '99')
    globalThis.navigator = { ...globalThis.navigator, sendBeacon: () => true }
    renderNavbar()
    fireEvent.click(screen.getAllByRole('button', { name: /open menu/i })[0])
    await act(async () => {
      fireEvent.click(screen.getAllByText(/logout/i)[0])
    })
    expect(localStorage.getItem('active_session_id')).toBeNull()
    expect(localStorage.getItem('lichess_user')).toBeNull()
  })
})