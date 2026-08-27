# Pipeline, gates e E2E

## Fluxo base

```mermaid
flowchart LR
    S[Create spec] --> A[Analyze demand]
    A --> AR[Architecture]
    AR --> D[Delivery]
    D --> T[Tests e E2E]
    T --> R[Review]
    R --> DOC[Documentation]
```

`analyze`, `architecture` e `delivery` são etapas core. Testes, E2E, review e
documentação podem seguir a política configurada, mas uma etapa desabilitada não
autoriza declarar uma verificação como executada.

## Visualização do fluxo

```mermaid
flowchart LR
    S[create spec] --> A[analyze demand]
    A --> G1{G1}
    G1 --> AR[architecture]
    AR --> G2{G2}
    G2 --> K{delivery_kind}
    K -->|application| I[implement spec]
    K -->|e2e-tests| E[generate E2E tests]
    I --> V[verify]
    E --> V
    V --> G3{G3}
    G3 --> T[tests e E2E run]
    T --> G4{G4}
    G4 --> R[review]
    R --> G5{G5}
    G5 --> D[docs e decisão humana]
    D --> G6{G6}
```

Os losangos são gates: se faltarem evidências, o fluxo retorna à etapa que as
produz. O agente não pode converter uma etapa ignorada em sucesso declarado.

## Gates

| Gate | Evidência principal |
|---|---|
| G1 | demanda, critérios e riscos compreendidos |
| G2 | Technical Design, arquivos afetados, delivery e verification aprovados |
| G3 | entrega validada com evidência real |
| G4 | testes e verificações declaradas concluídos |
| G5 | review arquitetural e de código sem achado crítico aberto |
| G6 | resumo e decisão humana sobre publicação/PR |

As políticas `auto`, `confirm` e `skip` são resolvidas pelo bootstrap a partir
das flags, do estado da demanda e do perfil padrão. Um gate automático precisa
de evidência do runtime atual; estado herdado não é aceito como sucesso
automático.

```mermaid
flowchart TB
    G1[G1: entendimento da demanda] --> G2[G2: design e contrato de entrega]
    G2 --> G3[G3: entrega gerada e verificada]
    G3 --> G4[G4: testes obrigatórios executados]
    G4 --> G5[G5: review sem achado crítico]
    G5 --> G6[G6: decisão humana sobre PR ou publicação]
```

## Arquitetura por demanda

Antes de G2, o toolkit classifica a demanda como `low`, `medium` ou `high`.
Mudanças de autenticação, dados, APIs, eventos, compatibilidade ou disponibilidade
devem resultar em design proporcional e, quando necessário, ADR.

```bash
sdd architecture propose --type feature --description "Adicionar paginação" --json
sdd architecture validate --task /caminho/task.md --json
```

## E2E como entrega

`test-e2e` significa que a suíte é a entrega principal: o bootstrap usa
`sdd-generate-e2e-tests --generate`, não `sdd-implement-spec`. A geração e a
execução são evidências distintas; somente a execução aprovada pode satisfazer
o G4 quando E2E é obrigatório.

Os testes Playwright ou Cypress são criados no projeto consumidor. O toolkit não
instala browsers, `package.json` ou um projeto E2E em sua própria raiz.
