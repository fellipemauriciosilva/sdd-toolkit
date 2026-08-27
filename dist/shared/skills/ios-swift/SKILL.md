---
name: swift-ios
description: "Convenções de desenvolvimento iOS/Swift. Usar quando: escrever código Swift, criar features, views, testes, coordinators, presenters ou repositories neste projeto."
---

# iOS & Swift — Convenções do Projeto

## Arquitetura: MVVM-C (Coordinator)

Cada feature segue esta estrutura:

```
Feature/
├── Coordinator/    # Navegação (herda de VVBaseCoordinator)
├── Presenter/      # Lógica de negócio (protocolos de Entrada/Saída)
├── Repository/     # Acesso a dados e API
├── Controller/     # UIViewController
├── View/           # Telas e componentes visuais
└── Protocols/      # Contratos de cada camada
```

- **Coordinator** gerencia navegação e instancia dependências.
- **Presenter** contém lógica via protocolos `*PresenterInput` / `*PresenterOutput`.
- **Repository** isola chamadas de rede/persistência, injetado via construtor.
- Todo componente tem um **protocolo** associado para testabilidade.

## UI

- **UIKit** é o framework principal (Storyboards + código).
- **SwiftUI** usado em componentes novos (`SwiftUIViews/`).
- Sistema de design interno: **Forro** (SPM local em `Libraries/Forro/`).
- Elementos de UI declarados como `lazy var`.

## Múltiplos Targets (3 marcas)

Base de código única gera 3 apps: **ExampleAppA**, **Extra**, **ExampleAppC**.
Cada um com variantes: Dev, Homolog, Staging, Release.
Configurações de marca ficam em diretórios dedicados e plists do Salesforce.

## Dependências

- **CocoaPods** (`Podfile`) — Alamofire, Firebase, Mixpanel, IOSSecuritySuite.
- **SPM** (`Package.swift`) — Forro, VVCommonUI, VVNetwork, FirebaseModule.
- Projeto gerado via **XcodeGen** (`project.yml`). Nunca edite o `.xcodeproj` diretamente.

## Padrões de Código

- **SwiftLint** ativo. Linha máx: 250 caracteres. MARK obrigatório por seção.
- Sufixos de nomenclatura: `*Protocol`, `*Coordinator`, `*Presenter`, `*Repository`.
- Injeção de dependência via **construtor** (nunca Service Locator).
- `NSNotification` para comunicação entre módulos.
- `StateManager` (singleton) para estado global de sessão.
- `FeatureManager` para flags de funcionalidade remotas.

## Testes

- **XCTest** com padrão **Spy** para objetos de teste.
- Espelham a estrutura de `LegacyPortfolio/` em `LegacyPortfolioTests/`.
- Nomear dublês de teste com sufixo `*Spy`.
- Testar Coordinator, Presenter, Repository e ViewController separadamente.

## Rede

- `APIClient` com protocolo próprio e decorador de renovação de token.
- Suporte a MTLS, cache Akamai e impressão digital de dispositivo.

## Compilação e Integração Contínua

- **XcodeGen** gera o projeto — rodar `scripts/postgen.sh` após mudanças.
- **Fastlane** para compilações e deploys (importado de repositório externo).
- **Jenkins** com pipelines por branch (PR, Master).

## Scaffolding inicial

Ao iniciar um novo projeto, crie os seguintes arquivos **antes de qualquer código de produção ou teste**:

### `.gitignore`

```gitignore
Pods/
DerivedData/
build/
*.xcworkspace
*.pbxuser
*.mode1v3
*.mode2v3
*.perspectivev3
*.moved-aside
*.hmap
*.ipa
*.dSYM.zip
*.dSYM
xcuserdata/
*.xcscmblueprint
*.xccheckout
.env
.confluence-cache/
```

### `README.md`

Crie um `README.md` na raiz do projeto com, no mínimo:

- Nome e descrição do projeto
- Pré-requisitos (Xcode, CocoaPods, XcodeGen)
- Como gerar o projeto (`xcodegen generate` + `scripts/postgen.sh`)
- Como instalar dependências (`pod install`)
- Como rodar o projeto no simulador/device
- Como rodar os testes (`xcodebuild test`)
- Targets e variantes disponíveis (ExampleAppA, Extra, ExampleAppC × Dev/Homolog/Staging/Release)
- Variáveis de ambiente necessárias (sem valores reais)

## Lista de Verificação ao Criar Feature

1. `.gitignore` configurado com entradas adequadas à stack.
2. `README.md` com instruções de setup, execução e testes.
3. Criar protocolos de cada camada (Coordinator, Presenter, Repository).
2. Implementar Coordinator herdando de `VVBaseCoordinator`.
3. Presenter com protocolos de Entrada/Saída.
4. Repository com injeção no Presenter via construtor.
5. ViewController conecta à Saída do Presenter.
6. Testes com Spys para cada camada.
7. Registrar rota no Coordinator pai.
