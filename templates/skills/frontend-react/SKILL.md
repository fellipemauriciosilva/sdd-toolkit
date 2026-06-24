---
name: frontend-react
description: Skill para desenvolvimento frontend com React e TypeScript. Use quando a tarefa envolver componentes React, hooks, estado, formulários ou integração com APIs usando React puro (Vite/CRA). Inclui padrões de TDD com Vitest e React Testing Library, estrutura de projeto feature-based, convenções de código e boas práticas de segurança.
---

# Frontend React (TypeScript)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | TypeScript 5+ |
| Framework | React 19+ |
| Bundler | Vite |
| Testes unitários | Vitest + React Testing Library |
| Testes E2E | Playwright |
| Cobertura | Istanbul via Vitest (mínimo 80%) |
| Estilização | Tailwind CSS ou CSS Modules |
| Gerenciamento de estado | Zustand (local/global) ou React Query (server state) |
| HTTP client | Axios ou fetch nativo |
| Linting | ESLint + eslint-plugin-react + typescript-eslint |
| Formatação | Prettier |

---

## Estrutura de projeto (feature-based)

```
src/
  features/
    <dominio>/
      components/
        <Componente>.tsx
        <Componente>.test.tsx
      hooks/
        use<Hook>.ts
        use<Hook>.test.ts
      services/
        <dominio>Service.ts
        <dominio>Service.test.ts
      types/
        index.ts
      index.ts              # barrel export
  shared/
    components/             # componentes reutilizáveis
    hooks/
    utils/
    types/
  pages/                    # composição de features em páginas
  App.tsx
  main.tsx
```

---

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
node_modules/
dist/
build/
coverage/
.env
.env.local
.env.*.local
.confluence-cache/
```

### `README.md`

Crie um `README.md` na raiz do projeto com, no mínimo:

- Nome e descrição do projeto
- Pré-requisitos (Node.js, npm/yarn/pnpm)
- Como instalar dependências (`npm install`)
- Como rodar o projeto localmente (`npm run dev`)
- Como rodar os testes (`npx vitest run`)
- Como gerar build de produção (`npm run build`)
- Variáveis de ambiente necessárias (sem valores reais)

---

## TDD com Vitest + React Testing Library

### Ciclo obrigatório

```
🔴 RED    → npx vitest run → deve FALHAR
🟢 GREEN  → implementar o mínimo → npx vitest run → deve PASSAR
🔵 REFACTOR → refatorar → npx vitest run → deve continuar PASSANDO
```

### Princípios do React Testing Library

> "The more your tests resemble the way your software is used, the more confidence they can give you."

- Teste **comportamento**, não implementação.
- Use queries semânticas: `getByRole`, `getByLabelText`, `getByText` — **nunca** `getByTestId` como primeiro recurso.
- Evite testar detalhes internos (estado, props internas, métodos de instância).

### Teste de componente

```tsx
// src/features/auth/components/LoginForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { LoginForm } from './LoginForm'

describe('LoginForm', () => {
  it('chama onSubmit com email e senha ao enviar o formulário', async () => {
    // Arrange
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<LoginForm onSubmit={onSubmit} />)

    // Act
    await user.type(screen.getByLabelText(/e-mail/i), 'alice@example.com')
    await user.type(screen.getByLabelText(/senha/i), 'secret123')
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    // Assert
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'alice@example.com',
        password: 'secret123',
      })
    })
  })

  it('exibe erro de validação quando email está vazio', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSubmit={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(screen.getByText(/e-mail é obrigatório/i)).toBeInTheDocument()
  })
})
```

### Teste de hook customizado

```tsx
// src/features/auth/hooks/useAuth.test.ts
import { renderHook, act } from '@testing-library/react'
import { vi } from 'vitest'
import { useAuth } from './useAuth'
import * as authService from '../services/authService'

describe('useAuth', () => {
  it('define usuário após login bem-sucedido', async () => {
    // Arrange
    vi.spyOn(authService, 'login').mockResolvedValue({ id: 1, name: 'Alice' })
    const { result } = renderHook(() => useAuth())

    // Act
    await act(() => result.current.login('alice@example.com', 'secret'))

    // Assert
    expect(result.current.user?.name).toBe('Alice')
  })
})
```

### Comandos de teste

```bash
# rodar em modo watch
npx vitest

# rodar uma vez (CI)
npx vitest run

# com cobertura
npx vitest run --coverage

# apenas um arquivo
npx vitest run src/features/auth/components/LoginForm.test.tsx
```

---

## Convenções de código

### Componente funcional

```tsx
// src/features/users/components/UserCard.tsx
interface UserCardProps {
  name: string
  email: string
  onSelect: (email: string) => void
}

export function UserCard({ name, email, onSelect }: UserCardProps) {
  return (
    <article className="rounded border p-4">
      <h2 className="text-lg font-semibold">{name}</h2>
      <p className="text-sm text-gray-500">{email}</p>
      <button
        type="button"
        onClick={() => onSelect(email)}
        className="mt-2 rounded bg-blue-600 px-4 py-1 text-white"
      >
        Selecionar
      </button>
    </article>
  )
}
```

### Hook de integração com API

```tsx
// src/features/users/hooks/useUsers.ts
import { useQuery } from '@tanstack/react-query'
import { fetchUsers } from '../services/usersService'

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  })
}
```

---

## Segurança (OWASP)

- **Nunca** insira HTML via `dangerouslySetInnerHTML` sem sanitização — use `dompurify`.
- Tokens JWT/session ficam em `httpOnly cookies` (gerenciados pelo backend) — **nunca** em `localStorage`.
- Valide e sanitize dados de formulário antes de enviar ao backend.
- Use variáveis de ambiente do Vite (`import.meta.env.VITE_*`) — **nunca** hardcode URLs ou chaves.
- Implemente Content Security Policy (CSP) no servidor/proxy.

---

## Definition of Done (React)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, execução local e testes
- [ ] Todos os testes passam: `npx vitest run`
- [ ] Cobertura ≥ 80%: `npx vitest run --coverage`
- [ ] Sem erros de linting: `npx eslint src/`
- [ ] Sem erros de tipos: `npx tsc --noEmit`
- [ ] Nenhum `any` não justificado
- [ ] Sem tokens ou segredos no código-fonte