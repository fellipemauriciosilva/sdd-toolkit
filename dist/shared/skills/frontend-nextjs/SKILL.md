---
name: frontend-nextjs
description: "Skill para desenvolvimento frontend com Next.js e TypeScript. Use quando a tarefa envolver páginas, rotas, Server Components, Client Components, Server Actions ou integração com APIs usando Next.js App Router. Inclui padrões de TDD com Vitest e React Testing Library, estrutura de projeto App Router, convenções de código e boas práticas de segurança."
---

# Frontend Next.js (TypeScript)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | TypeScript 5+ |
| Framework | Next.js 15+ (App Router) |
| Testes unitários | Vitest + React Testing Library |
| Testes E2E | Playwright |
| Cobertura | Istanbul via Vitest (mínimo 80%) |
| Estilização | Tailwind CSS |
| Gerenciamento de estado | Zustand (client) + React Query ou fetch nativo (server) |
| Linting | ESLint + eslint-config-next + typescript-eslint |
| Formatação | Prettier |

---

## Estrutura de projeto (App Router)

```
src/
  app/                      # roteamento baseado em arquivos (App Router)
    layout.tsx              # layout raiz
    page.tsx                # rota /
    <segmento>/
      page.tsx              # rota /<segmento>
      layout.tsx            # layout aninhado (opcional)
      loading.tsx           # Suspense fallback
      error.tsx             # error boundary
      actions.ts            # Server Actions
  features/
    <dominio>/
      components/
        <Componente>.tsx       # Client Component ('use client')
        <Componente>.test.tsx
        <ComponenteServer>.tsx # Server Component (default)
      hooks/
        use<Hook>.ts
        use<Hook>.test.ts
      services/
        <dominio>Service.ts    # fetch server-side
      types/
        index.ts
  shared/
    components/
    hooks/
    utils/
  lib/                      # configurações globais (auth, db, etc.)
```

---

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
node_modules/
.next/
out/
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
- Como gerar build de produção (`npx next build`)
- Variáveis de ambiente necessárias (sem valores reais — distinguir `NEXT_PUBLIC_` de variáveis privadas)

---

## Regras do App Router

### Server Components (padrão)

- Podem fazer `async/await` diretamente — sem `useEffect` para buscar dados.
- **Nunca** usam `useState`, `useEffect`, event handlers — para isso use Client Components.
- Acesso direto a banco de dados, variáveis de ambiente privadas, tokens.

```tsx
// src/features/users/components/UserList.tsx  (Server Component)
import { fetchUsers } from '../services/usersService'

export async function UserList() {
  const users = await fetchUsers()   // fetch direto, server-side

  return (
    <ul>
      {users.map(u => <li key={u.id}>{u.name}</li>)}
    </ul>
  )
}
```

### Client Components

- Adicione `'use client'` **apenas quando necessário** (interatividade, hooks, browser APIs).
- Prefira manter o máximo de lógica em Server Components.

```tsx
'use client'
// src/features/auth/components/LoginButton.tsx

import { useState } from 'react'

export function LoginButton({ onLogin }: { onLogin: () => void }) {
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    setLoading(true)
    await onLogin()
    setLoading(false)
  }

  return (
    <button onClick={handleClick} disabled={loading}>
      {loading ? 'Entrando...' : 'Entrar'}
    </button>
  )
}
```

### Server Actions

```tsx
// src/app/users/actions.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function createUser(formData: FormData) {
  const name = formData.get('name') as string
  // validação e persistência aqui
  revalidatePath('/users')
}
```

---

## TDD com Vitest + React Testing Library

### Ciclo obrigatório

```
🔴 RED    → npx vitest run → deve FALHAR
🟢 GREEN  → implementar o mínimo → npx vitest run → deve PASSAR
🔵 REFACTOR → refatorar → npx vitest run → deve continuar PASSANDO
```

### Configuração (vitest.config.ts)

```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
})
```

### Teste de Client Component

```tsx
// src/features/auth/components/LoginButton.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { LoginButton } from './LoginButton'

describe('LoginButton', () => {
  it('exibe "Entrando..." durante o login', async () => {
    const user = userEvent.setup()
    const onLogin = vi.fn(() => new Promise(r => setTimeout(r, 100)))
    render(<LoginButton onLogin={onLogin} />)

    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(screen.getByText(/entrando/i)).toBeInTheDocument()
  })
})
```

### Teste de Server Component

Server Components são testados mockando dependências de dados:

```tsx
// src/features/users/components/UserList.test.tsx
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import * as usersService from '../services/usersService'
import { UserList } from './UserList'

vi.mock('../services/usersService')

describe('UserList', () => {
  it('renderiza a lista de usuários', async () => {
    vi.mocked(usersService.fetchUsers).mockResolvedValue([
      { id: 1, name: 'Alice' },
    ])

    render(await UserList())   // aguarda o Server Component async

    expect(screen.getByText('Alice')).toBeInTheDocument()
  })
})
```

### Comandos de teste

```bash
npx vitest run             # CI
npx vitest                 # watch
npx vitest run --coverage  # cobertura
npx playwright test        # E2E
```

---

## Convenções de código

### Busca de dados server-side com cache

```tsx
// src/features/users/services/usersService.ts
export async function fetchUsers(): Promise<User[]> {
  const res = await fetch(`${process.env.API_URL}/users`, {
    next: { revalidate: 60 },   // ISR: revalida a cada 60s
  })
  if (!res.ok) throw new Error('Failed to fetch users')
  return res.json()
}
```

### Metadata de página

```tsx
// src/app/users/page.tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Usuários',
  description: 'Lista de usuários do sistema',
}

export default async function UsersPage() {
  return <h1>Usuários</h1>
}
```

---

## Segurança (OWASP)

- **Nunca** exponha variáveis `NEXT_PUBLIC_` para segredos — use apenas para valores públicos.
- Server Actions devem validar e autorizar cada chamada — não confie no cliente.
- Sanitize conteúdo dinâmico renderizado como HTML — use `dompurify` quando necessário.
- Configure `next.config.ts` com `headers()` para CSP, X-Frame-Options e HSTS.
- Tokens de sessão via `httpOnly cookies` — **nunca** em `localStorage`.

---

## Definition of Done (Next.js)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, execução local e testes
- [ ] Todos os testes passam: `npx vitest run`
- [ ] Cobertura ≥ 80%
- [ ] **Build de produção obrigatório**: executar `npx next build` ao finalizar a tarefa e garantir que termina sem erros e sem warnings — esta verificação é **bloqueante** e deve ser feita antes de marcar a tarefa como concluída
- [ ] Sem erros de tipos: `npx tsc --noEmit`
- [ ] Sem erros de linting: `npx next lint`
- [ ] `NEXT_PUBLIC_` não contém segredos
