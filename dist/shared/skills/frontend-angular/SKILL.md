---
name: frontend-angular
description: "Skill para desenvolvimento frontend com Angular e TypeScript. Use quando a tarefa envolver componentes Angular, serviços, módulos, formulários reativos ou integração com APIs usando Angular. Inclui padrões de TDD com Jasmine/Jest e Angular Testing Utilities, estrutura de projeto, convenções de código e boas práticas de segurança."
---

# Frontend Angular (TypeScript)

## Stack tecnológica

| Componente | Tecnologia |
|---|---|
| Linguagem | TypeScript 5+ |
| Framework | Angular 19+ (Standalone Components) |
| Testes unitários | Jest + Angular Testing Library ou Jasmine + Karma |
| Testes E2E | Playwright ou Cypress |
| Cobertura | Istanbul via Jest (mínimo 80%) |
| Estilização | SCSS ou Tailwind CSS |
| Gerenciamento de estado | NgRx (complexo) ou Angular Signals (simples/médio) |
| HTTP client | Angular `HttpClient` |
| Linting | ESLint + angular-eslint |
| Formatação | Prettier |

---

## Estrutura de projeto (feature-based)

```
src/
  app/
    core/                   # serviços singleton, guards, interceptors
      interceptors/
      guards/
      services/
    features/
      <dominio>/
        components/
          <dominio>.component.ts
          <dominio>.component.html
          <dominio>.component.scss
          <dominio>.component.spec.ts
        services/
          <dominio>.service.ts
          <dominio>.service.spec.ts
        models/
          <dominio>.model.ts
        <dominio>.routes.ts   # lazy routes do feature
    shared/
      components/
      pipes/
      directives/
    app.config.ts
    app.routes.ts
  environments/
    environment.ts
    environment.prod.ts
```

---

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
node_modules/
dist/
.angular/
coverage/
.env
.env.local
.confluence-cache/
```

### `README.md`

Crie um `README.md` na raiz do projeto com, no mínimo:

- Nome e descrição do projeto
- Pré-requisitos (Node.js, Angular CLI)
- Como instalar dependências (`npm install`)
- Como rodar o projeto localmente (`ng serve`)
- Como rodar os testes (`ng test --watch=false`)
- Como gerar build de produção (`ng build`)
- Variáveis de ambiente necessárias (sem valores reais)

---

## TDD com Jasmine / Jest

### Ciclo obrigatório

```
🔴 RED    → ng test --watch=false → deve FALHAR
🟢 GREEN  → implementar o mínimo → ng test --watch=false → deve PASSAR
🔵 REFACTOR → refatorar → ng test --watch=false → deve continuar PASSANDO
```

### Teste de componente (TestBed)

```typescript
// src/app/features/users/components/user-card.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing'
import { By } from '@angular/platform-browser'
import { UserCardComponent } from './user-card.component'

describe('UserCardComponent', () => {
  let fixture: ComponentFixture<UserCardComponent>
  let component: UserCardComponent

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserCardComponent],   // Standalone Component
    }).compileComponents()

    fixture = TestBed.createComponent(UserCardComponent)
    component = fixture.componentInstance
  })

  it('deve exibir o nome do usuário', () => {
    // Arrange
    component.name = 'Alice'
    fixture.detectChanges()

    // Act
    const nameEl = fixture.debugElement.query(By.css('[data-testid="user-name"]'))

    // Assert
    expect(nameEl.nativeElement.textContent).toContain('Alice')
  })

  it('deve emitir evento ao clicar em Selecionar', () => {
    // Arrange
    const selectSpy = jest.spyOn(component.selected, 'emit')
    component.name = 'Alice'
    component.email = 'alice@example.com'
    fixture.detectChanges()

    // Act
    const btn = fixture.debugElement.query(By.css('button'))
    btn.nativeElement.click()

    // Assert
    expect(selectSpy).toHaveBeenCalledWith('alice@example.com')
  })
})
```

### Teste de serviço (com HttpClientTestingModule)

```typescript
// src/app/features/users/services/users.service.spec.ts
import { TestBed } from '@angular/core/testing'
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing'
import { UsersService } from './users.service'
import { User } from '../models/user.model'

describe('UsersService', () => {
  let service: UsersService
  let httpMock: HttpTestingController

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UsersService],
    })
    service = TestBed.inject(UsersService)
    httpMock = TestBed.inject(HttpTestingController)
  })

  afterEach(() => httpMock.verify())

  it('deve retornar lista de usuários', () => {
    // Arrange
    const mockUsers: User[] = [{ id: 1, name: 'Alice', email: 'alice@example.com' }]

    // Act
    service.getAll().subscribe(users => {
      // Assert
      expect(users).toHaveLength(1)
      expect(users[0].name).toBe('Alice')
    })

    const req = httpMock.expectOne('/api/users')
    expect(req.request.method).toBe('GET')
    req.flush(mockUsers)
  })
})
```

### Comandos de teste

```bash
# rodar todos os testes (Karma/Jasmine padrão)
ng test --watch=false

# com cobertura
ng test --watch=false --code-coverage

# Jest (se configurado)
npx jest
npx jest --coverage

# filtrar por nome de spec
ng test --include="**/user-card*"
```

---

## Convenções de código

### Standalone Component

```typescript
// src/app/features/users/components/user-card.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core'
import { CommonModule } from '@angular/common'

@Component({
  selector: 'app-user-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './user-card.component.html',
  styleUrl: './user-card.component.scss',
})
export class UserCardComponent {
  @Input({ required: true }) name!: string
  @Input({ required: true }) email!: string
  @Output() selected = new EventEmitter<string>()

  onSelect(): void {
    this.selected.emit(this.email)
  }
}
```

### Serviço com HttpClient

```typescript
// src/app/features/users/services/users.service.ts
import { Injectable, inject } from '@angular/core'
import { HttpClient } from '@angular/common/http'
import { Observable } from 'rxjs'
import { User } from '../models/user.model'

@Injectable({ providedIn: 'root' })
export class UsersService {
  private readonly http = inject(HttpClient)
  private readonly baseUrl = '/api/users'

  getAll(): Observable<User[]> {
    return this.http.get<User[]>(this.baseUrl)
  }

  getById(id: number): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/${id}`)
  }
}
```

### Roteamento lazy (feature routes)

```typescript
// src/app/features/users/users.routes.ts
import { Routes } from '@angular/router'

export const USERS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/user-list.component').then(m => m.UserListComponent),
  },
  {
    path: ':id',
    loadComponent: () =>
      import('./components/user-detail.component').then(m => m.UserDetailComponent),
  },
]
```

---

## Segurança (OWASP)

- **Nunca** use `[innerHTML]` com dados do usuário sem sanitização — Angular sanitiza automaticamente, mas conteúdo marcado como `bypassSecurityTrustHtml` é perigoso.
- Valide formulários reativos (`FormGroup` + `Validators`) no frontend **e** no backend.
- Tokens ficam em `httpOnly cookies` — **nunca** em `localStorage`.
- Use `HttpInterceptor` para adicionar cabeçalhos de autenticação — não repita lógica de auth em cada serviço.
- Variáveis sensíveis ficam em `environment.ts` injetado no build — **nunca** hardcoded.
- Implemente guards (`CanActivate`) para rotas protegidas.

---

## Definition of Done (Angular)

- [ ] `.gitignore` configurado com entradas adequadas à stack
- [ ] `README.md` com instruções de setup, execução local e testes
- [ ] Todos os testes passam: `ng test --watch=false`
- [ ] Cobertura ≥ 80%: `ng test --watch=false --code-coverage`
- [ ] Build sem erros: `ng build`
- [ ] Sem erros de linting: `ng lint`
- [ ] Sem erros de tipos: `npx tsc --noEmit`
- [ ] Rotas lazy-loaded configuradas por feature
- [ ] Sem tokens ou segredos hardcoded
