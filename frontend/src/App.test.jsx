import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import userEvent from '@testing-library/user-event'
import App from './App'

describe('App', () => {
  it('introduces the workflow playbook', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: /从需求输入，到可验证、可交付的产品方案/,
      }),
    ).toBeInTheDocument()
  })

  it('shows all eight workflow stages', () => {
    render(<App />)

    expect(screen.getAllByRole('button', { name: /阶段 \d：/ })).toHaveLength(8)
  })

  it('opens the selected stage guide', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /阶段 3：业务访谈/ }))

    expect(
      screen.getByRole('heading', { name: /业务访谈：校准真实业务流程/ }),
    ).toBeInTheDocument()
  })

  it('keeps the real case study empty', () => {
    render(<App />)

    expect(screen.getByText('真实案例待补充')).toBeInTheDocument()
  })
})
