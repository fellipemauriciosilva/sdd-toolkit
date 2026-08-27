---
name: visualage-mainframe
description: "Skill para leitura, interpretação e navegação de projetos IBM VisualAge para mainframe. Use quando a tarefa envolver análise de estrutura de projetos VisualAge, localização de código COBOL em workspaces e bibliotecas, identificação de artefatos gerados versus manuais, rastreamento de dependências entre programas e planejamento de modernização a partir desse ambiente de desenvolvimento."
---

# IBM VisualAge para Mainframe — Estrutura de Projetos e Modernização

## Objetivo desta skill

Capacitar o agente a **entender a estrutura e organização de projetos IBM VisualAge para mainframe**, com foco em localizar e interpretar código para modernização. O VisualAge foi um IDE (Integrated Development Environment) da IBM usado para desenvolver, depurar e gerenciar programas COBOL (e PL/I) que executam em ambiente z/OS. Compreender sua organização é essencial para rastrear onde está o código-fonte real, distinguir código gerado de código manual e reconstruir o grafo de dependências de um sistema legado.

---

## Contexto do ambiente

| Componente | Tecnologia |
|---|---|
| IDE | IBM VisualAge para COBOL / VisualAge for Java (mainframe) |
| Plataforma-alvo | IBM z/OS |
| Linguagem principal | COBOL (Enterprise COBOL) |
| Controle de fonte | SCLM, Endevor, ISPF/PDFs ou repositório interno do VisualAge |
| Compilação | IBM Enterprise COBOL Compiler no z/OS |
| Linkedit | Binder (IEWL / IEWBLINK) |
| Bibliotecas de código | PDS (Partitioned Data Sets) no z/OS |
| Artefatos visuais | Definições de tela, record layouts, diagramas de estrutura |
| Integração | CICS, DB2, IMS, MQ Series, batch JCL |

---

# PARTE 1 — ORGANIZAÇÃO DE PROJETOS

---

## 1. Estrutura de workspace e projetos

O VisualAge organiza código em uma hierarquia de **workspace → projetos → pacotes/pastas → programas**. Essa organização é proprietária do IDE e não corresponde diretamente à estrutura de diretórios no sistema de arquivos local nem aos PDSs no mainframe.

### Hierarquia conceitual

```
Workspace VisualAge
├── Projeto A (ex.: "SistemaContabil")
│   ├── Pacote/Pasta "Batch"
│   │   ├── CALCFOLH.cbl       (programa COBOL)
│   │   ├── CALCFOLH.cpy       (copybook associado)
│   │   └── GERRELA.cbl        (programa COBOL)
│   ├── Pacote/Pasta "Online"
│   │   ├── CONTACOR.cbl       (programa CICS)
│   │   └── CONTACOR.bms       (mapa BMS)
│   └── Pacote/Pasta "Copybooks"
│       ├── CPYCLIEN.cpy
│       ├── CPYCONTA.cpy
│       └── CPYTRANS.cpy
├── Projeto B (ex.: "InterfaceCliente")
│   └── ...
└── Configuração de Build
    ├── Perfis de compilação
    ├── Mapeamentos para PDSs
    └── Definições de linkedit
```

### Significado para modernização

| Conceito VisualAge | Conceito moderno equivalente |
|---|---|
| Workspace | Monorepo ou conjunto de repositórios |
| Projeto | Módulo / Microserviço / Biblioteca |
| Pacote/Pasta | Package / Namespace / Feature folder |
| Programa COBOL (.cbl) | Classe / Serviço / Controller |
| Copybook (.cpy) | DTO / Schema / Interface compartilhada |
| Perfil de compilação | Build profile / Pipeline CI/CD |

### Regra fundamental

**A organização de projetos no VisualAge é uma visão lógica.** O código-fonte real pode estar:
1. No sistema de arquivos local da estação de trabalho (diretórios do workspace)
2. No mainframe, em PDSs (sincronizado via upload/download)
3. Em um SCM (Software Configuration Management) como SCLM ou Endevor
4. Em alguma combinação dos três, com risco de versões divergentes

O agente deve sempre perguntar ou investigar **onde está a versão autoritativa** do código antes de assumir que o fonte encontrado é o correto.

---

## 2. Identificando o ponto de entrada de um programa

No VisualAge, cada programa COBOL tem um ponto de entrada definido pela `PROCEDURE DIVISION`. Porém, o ponto de entrada **dentro do contexto do projeto** depende de como o programa é invocado:

### Programas batch (executados via JCL)

```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALCFOLH.
       ...
       PROCEDURE DIVISION.
       0000-PRINCIPAL.
           PERFORM 1000-INICIALIZAR
           PERFORM 2000-PROCESSAR UNTIL WS-FIM = 'S'
           PERFORM 9000-FINALIZAR
           STOP RUN.
```

**Como identificar:** Procurar o `PROGRAM-ID` e cruzar com o JCL que executa `EXEC PGM=CALCFOLH`. O programa é chamado diretamente pelo job scheduler.

### Programas online (CICS)

```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CONTACOR.
       ...
       PROCEDURE DIVISION.
       0000-PRINCIPAL.
           EVALUATE TRUE
               WHEN EIBCALEN = 0
                   PERFORM 1000-PRIMEIRO-ACESSO
               WHEN OTHER
                   PERFORM 2000-PROCESSAR-ENTRADA
           END-EVALUATE
           EXEC CICS RETURN
               TRANSID('CCOR')
               COMMAREA(WS-COMMAREA)
           END-EXEC.
```

**Como identificar:** Procurar o `PROGRAM-ID` e cruzar com a definição de transação CICS (CSD ou tabela PCT) que associa o TRANSID ao programa. O VisualAge pode ter essa configuração nos metadados do projeto.

### Sub-programas (CALLed programs)

```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. VALCPF.
       ...
       PROCEDURE DIVISION USING LS-CPF LS-RESULTADO.
       0000-VALIDAR.
           ...
           GOBACK.
```

**Como identificar:** Sub-programas têm `PROCEDURE DIVISION USING` (recebem parâmetros por LINKAGE SECTION) e terminam com `GOBACK` em vez de `STOP RUN`. São invocados via `CALL 'VALCPF' USING ...` de outros programas.

### Navegação no VisualAge

O VisualAge oferece funcionalidades para rastrear pontos de entrada:
- **Build order:** A configuração de build indica quais programas são compilados e linkeditados como load modules independentes (pontos de entrada) versus quais são linkados como sub-rotinas.
- **Program list:** A lista de programas do projeto pode indicar quais são "main programs" versus "called programs".
- **Metadados de projeto:** Arquivos `.vap`, `.vpj` ou equivalentes contêm definições de build targets que indicam os programas principais.

### Estratégia de identificação

1. Verificar os **build targets** do projeto — cada target que gera um load module é um ponto de entrada
2. Procurar programas com `STOP RUN` (batch) ou `EXEC CICS RETURN` sem `TRANSID` (fim de cadeia CICS)
3. Procurar programas que **não aparecem** como argumento de `CALL`, `LINK` ou `XCTL` em nenhum outro programa — são candidatos a pontos de entrada raiz
4. Cruzar com JCL (para batch) ou CSD (para CICS) para confirmar

---

## 3. Dependências entre programas — grafo de dependências

O VisualAge mantém um modelo de dependências entre programas do projeto. Porém, as dependências em COBOL são frequentemente **implícitas e dinâmicas**, o que torna a análise mais complexa.

### Tipos de dependências

#### Dependência estática — CALL literal

```cobol
           CALL 'VALCPF' USING WS-CPF WS-RESULTADO
```

**Detecção:** Buscar todos os `CALL 'nome-literal'` no código. O nome entre aspas é o `PROGRAM-ID` do sub-programa.

#### Dependência dinâmica — CALL variável

```cobol
           MOVE 'VALCPF' TO WS-PROGRAMA
           CALL WS-PROGRAMA USING WS-CPF WS-RESULTADO
```

**Risco:** O nome do programa é determinado em runtime. Pode vir de uma tabela, VSAM, DB2 ou cálculo. A análise estática não consegue resolver todas as possibilidades.

**Estratégia:** Buscar todos os `MOVE ... TO WS-PROGRAMA` (ou a variável usada no CALL) para identificar possíveis valores. Se o valor vem de I/O externo, documentar como dependência dinâmica não-resolvível estaticamente.

#### Dependência CICS — LINK e XCTL

```cobol
           EXEC CICS LINK
               PROGRAM('VALCPF')
               COMMAREA(WS-COMMAREA)
               LENGTH(WS-COMM-LEN)
           END-EXEC

           EXEC CICS XCTL
               PROGRAM('MENUPRI')
               COMMAREA(WS-COMMAREA)
           END-EXEC
```

**LINK:** Chamada síncrona com retorno (equivalente a chamada de função). O programa chamador espera o retorno.
**XCTL:** Transferência de controle sem retorno (equivalente a redirect/forward). O programa chamador é descarregado da memória.

#### Dependência de copybook — COPY

```cobol
           COPY CPYCLIEN.
           COPY CPYCONTA REPLACING ==:PREFIX:== BY ==CLI-==.
```

**Significado:** Inclusão textual de código compartilhado. A dependência é **em tempo de compilação** — o copybook precisa estar disponível na SYSLIB ou caminho configurado no VisualAge.

#### Dependência de dados — datasets compartilhados

Programas que leem e escrevem os mesmos datasets (VSAM, DB2, arquivos sequenciais) têm dependência implícita de dados. Essa dependência não aparece no código como `CALL` mas é crítica para a ordem de execução e integridade dos dados.

### Reconstruindo o grafo de dependências

```
MENUPRI (CICS)
├── XCTL → CONTACOR (CICS)
│   ├── LINK → VALCPF (sub-programa)
│   ├── LINK → CALCSALD (sub-programa)
│   │   └── CALL → CALCJUR (sub-programa)
│   └── COPY → CPYCLIEN, CPYCONTA
├── XCTL → RELACLI (CICS)
│   ├── LINK → BUSCACLI (sub-programa)
│   └── COPY → CPYCLIEN
└── COPY → CPYMENU
```

### Procedimento para reconstruir o grafo

1. **Listar todos os programas** do projeto VisualAge
2. **Para cada programa**, extrair:
   - `CALL 'literal'` → dependência estática de sub-programa
   - `CALL variável` → dependência dinâmica (documentar possíveis valores)
   - `EXEC CICS LINK PROGRAM('nome')` → dependência CICS síncrona
   - `EXEC CICS XCTL PROGRAM('nome')` → transferência de controle CICS
   - `COPY nome` → dependência de copybook
3. **Construir o grafo dirigido** de chamadas
4. **Identificar ciclos** (não devem existir em CALL/LINK, mas podem existir em XCTL para navegação)
5. **Identificar programas órfãos** (nunca chamados por nenhum outro) — podem ser pontos de entrada ou código morto
6. **Cruzar com artefatos de build** do VisualAge para validar

---

# PARTE 2 — ARTEFATOS E GERAÇÃO DE CÓDIGO

---

## 4. Código gerado pelo VisualAge vs código manual

O VisualAge pode gerar código COBOL a partir de definições visuais (editores de tela, modeladores de dados, wizards). Distinguir código gerado de código manual é **crítico** para modernização porque:
- Código gerado segue padrões repetitivos e pode ser substituído por frameworks modernos
- Código manual contém regras de negócio que precisam ser preservadas
- Tentar modernizar código gerado linha a linha é desperdício — melhor entender o que o gerador fazia e recriar com ferramentas modernas

### Marcadores de código gerado

O VisualAge tipicamente insere comentários ou padrões reconhecíveis no código gerado:

```cobol
      *================================================================
      * GENERATED BY IBM VISUALAGE FOR COBOL
      * DO NOT MODIFY - CHANGES WILL BE LOST ON REGENERATION
      * Generation Date: 2003-05-15 14:30:22
      *================================================================
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SCRNCLI.
```

#### Indicadores de código gerado

| Indicador | Exemplo | Significado |
|---|---|---|
| Comentários de geração | `* GENERATED BY IBM VISUALAGE` | Marcador explícito do gerador |
| Prefixos padronizados | `VA-`, `GEN-`, `DG-` em nomes de variáveis | Namespacing do gerador |
| Parágrafos boilerplate | `VA-INIT`, `VA-TERM`, `VA-ERROR-HANDLER` | Infraestrutura do runtime VisualAge |
| COPY de runtime | `COPY VARUNTIME`, `COPY VAERRHND` | Copybooks do framework VisualAge |
| Estrutura rígida | Exatamente os mesmos parágrafos em todos os programas gerados | Template do gerador |
| Data division inflada | Dezenas de variáveis `VA-WS-*` nunca usadas na lógica de negócio | Variáveis de controle do framework |

#### Indicadores de código manual

| Indicador | Exemplo | Significado |
|---|---|---|
| Nomes semânticos de negócio | `CALCULAR-JUROS`, `VALIDAR-LIMITE` | Desenvolvedor nomeou com significado |
| Comentários em português/negócio | `* REGRA: DESCONTO SÓ PARA CLIENTES GOLD` | Documentação de regra |
| Lógica condicional complexa | `IF` aninhados com condições de negócio | Regras que não vêm de template |
| Cálculos específicos | `COMPUTE VL-JUROS = VL-SALDO * TX-MENSAL / 100` | Fórmulas de negócio |
| Seções `PERFORM` com nomes de negócio | `PERFORM 5000-APLICAR-DESCONTO` | Lógica específica da aplicação |

### Tipos de código que o VisualAge gera

#### 1. Código de interface de tela (BMS/Maps)

O VisualAge gera programas que gerenciam a interação com telas 3270:
- `SEND MAP` / `RECEIVE MAP` com tratamento de AID keys
- Parágrafos de movimentação de dados entre mapa e WORKING-STORAGE
- Validação de campos de tela (obrigatório, numérico, tamanho)

**Na modernização:** Substituir por API REST + frontend web. Não tentar traduzir a lógica de tela 3270 — redesenhar a interface.

#### 2. Código de acesso a dados (SQL/VSAM)

O VisualAge pode gerar wrappers para acesso a DB2 ou VSAM:
- `EXEC SQL` com cursores gerados
- `OPEN/READ/WRITE/CLOSE` para VSAM
- Tratamento de `SQLCODE` e `FILE STATUS` padronizado

**Na modernização:** Substituir por repositórios/DAOs com ORM ou query builders modernos. Preservar a semântica das queries, não a estrutura do wrapper.

#### 3. Código de estrutura de programa

O VisualAge pode gerar o esqueleto do programa:
- `IDENTIFICATION DIVISION` completa
- Parágrafos `0000-PRINCIPAL`, `1000-INICIALIZAR`, `9000-FINALIZAR`
- Tratamento de erros padrão
- Lógica de commarea (CICS)

**Na modernização:** O esqueleto pode ser descartado. Focar nos parágrafos de negócio que foram codificados manualmente dentro do esqueleto.

### Estratégia de triagem

```
Programa VisualAge
├── Código gerado (VA-*, boilerplate)     → DESCARTAR — reconstruir com framework moderno
├── Código de interface (SEND/RECEIVE)    → REDESENHAR — API + frontend
├── Código de acesso a dados (SQL/VSAM)   → SUBSTITUIR — repositório/DAO moderno
└── Código de negócio (cálculos, regras)  → PRESERVAR — extrair e migrar com cuidado
```

---

## 5. Copybooks e includes — localização e referências

### Como copybooks são referenciados no projeto

```cobol
       DATA DIVISION.
       WORKING-STORAGE SECTION.
      * Layout do cliente
           COPY CPYCLIEN.
      * Layout da conta com substituição de prefixo
           COPY CPYCONTA REPLACING ==:PREFIX:== BY ==CT-==.
      * Constantes do sistema
           COPY CPYCONST.
       
       PROCEDURE DIVISION.
      * Rotinas utilitárias
           COPY CPYUTILS.
```

### Onde localizar copybooks no contexto VisualAge

O VisualAge resolve copybooks em uma ordem de busca configurável:

```
Ordem de resolução de COPY:
1. Pasta "Copybooks" do projeto atual no VisualAge
2. Projetos referenciados (dependências de projeto)
3. SYSLIB configurada no perfil de compilação
4. PDSs mapeados no mainframe (ex.: PROD.COPYLIB, PROD.SQLCOPY)
```

### Mapeamento de localização

| Localização no VisualAge | Localização real | Como encontrar |
|---|---|---|
| Pasta do projeto | Diretório local no workspace | Navegar o file system do workspace |
| Projeto referenciado | Outro diretório local | Verificar dependências de projeto nas configurações |
| SYSLIB | PDS no mainframe | Verificar o JCL de compilação ou perfil de build |
| PDS mapeado | PDS no mainframe | Verificar `//SYSLIB DD` no JCL ou configuração de remote systems |

### Riscos na modernização

1. **Copybook ausente:** O código fonte pode referenciar um COPY que não está no projeto VisualAge — está apenas no mainframe. É necessário buscar no PDS correto.
2. **Versões divergentes:** O copybook local pode estar desatualizado em relação ao que está no mainframe. **Sempre validar contra a versão em produção.**
3. **REPLACING:** A cláusula `REPLACING` altera o texto do copybook na inclusão. A versão final do código (pós-preprocessamento) pode ser diferente do que aparece no arquivo `.cpy`.
4. **Copybooks de DB2:** Copybooks gerados por `DCLGEN` (declarações SQL) ficam em PDSs separados (geralmente `*.DCLGEN` ou `*.SQLCOPY`). Contêm layouts de tabelas DB2 como estruturas COBOL.
5. **Copybooks aninhados:** Um copybook pode incluir outro copybook (`COPY` dentro de `COPY`). Rastrear toda a cadeia.

### Procedimento para localizar todos os copybooks

1. **Buscar** todos os `COPY` statements nos fontes COBOL do projeto
2. **Verificar** primeiro na pasta local do projeto VisualAge
3. Se não encontrado, **verificar** projetos referenciados
4. Se não encontrado, **verificar** PDSs no mainframe (via SYSLIB do JCL)
5. Para cada copybook encontrado, **verificar** se há `REPLACING` e documentar as substituições
6. **Verificar** se o copybook contém outros `COPY` (aninhamento)
7. **Comparar** versão local vs mainframe para detectar divergências

---

# PARTE 3 — INTEGRAÇÃO COM MAINFRAME

---

## 6. Conexão com PDSs (Partitioned Data Sets)

O VisualAge funciona como uma ponte entre a estação de trabalho (workstation) e o mainframe z/OS. O código-fonte real pode residir em qualquer um dos dois lados, e o VisualAge gerencia a sincronização.

### Arquitetura de conexão

```
┌─────────────────────────┐         ┌─────────────────────────────┐
│   Workstation (PC)      │         │   Mainframe z/OS            │
│                         │  TCP/IP │                             │
│  VisualAge IDE          │◄───────►│  FTP / ISPF Gateway /       │
│  ├── Projeto local      │         │  RSE (Remote System         │
│  │   ├── fontes .cbl    │  sync   │  Explorer)                  │
│  │   ├── copybooks .cpy │◄──────► │                             │
│  │   └── configs        │         │  PDSs:                      │
│  └── Build configs      │         │  ├── DESENV.SRCLIB (fontes) │
│      └── PDS mappings   │         │  ├── DESENV.COPYLIB (copy)  │
│                         │         │  ├── DESENV.LOADLIB (load)  │
│                         │         │  ├── DESENV.DBRMLIB (DBRM)  │
│                         │         │  └── PROD.* (produção)      │
└─────────────────────────┘         └─────────────────────────────┘
```

### Tipos de PDS envolvidos

| PDS | Conteúdo | Significado |
|---|---|---|
| `*.SRCLIB` ou `*.COBOL` | Fontes COBOL | Código-fonte dos programas |
| `*.COPYLIB` ou `*.COPY` | Copybooks | Includes compartilhados |
| `*.LOADLIB` ou `*.LOAD` | Load modules | Programas compilados e linkeditados (executáveis) |
| `*.DBRMLIB` ou `*.DBRM` | Database Request Modules | SQL pré-compilado (usado pelo BIND do DB2) |
| `*.LISTLIB` ou `*.LIST` | Listagens de compilação | Output do compilador (para diagnóstico) |
| `*.OBJLIB` ou `*.OBJ` | Object modules | Código compilado antes do linkedit |
| `*.JCLLIB` ou `*.JCL` | JCLs de compilação/execução | Jobs de build e execução |
| `*.PROCLIB` | Procedures JCL | PROCs de compilação reutilizáveis |

### Como o VisualAge mapeia PDSs

O VisualAge mantém configurações de **mapeamento** entre pastas do projeto e PDSs no mainframe:

```
Configuração de mapeamento (exemplo):
  Pasta "Fontes"     →  DESENV.PROJCONT.SRCLIB
  Pasta "Copybooks"  →  DESENV.PROJCONT.COPYLIB
  Pasta "JCL"        →  DESENV.PROJCONT.JCLLIB
  Build output       →  DESENV.PROJCONT.LOADLIB
```

### Onde está o código real?

Esta é a **pergunta mais importante** ao analisar um projeto VisualAge para modernização:

| Cenário | Onde está o código autoritativo | Risco |
|---|---|---|
| Desenvolvimento ativo com VisualAge | Workspace local (sincronizado para mainframe) | Versão local pode estar à frente do mainframe |
| VisualAge abandonado, manutenção via ISPF | PDS no mainframe | Workspace local desatualizado ou inexistente |
| SCM integrado (Endevor/SCLM) | Repositório SCM no mainframe | VisualAge e PDS podem estar desatualizados |
| Migração parcial | **Indefinido** — pode estar em qualquer lugar | Alto risco de versões conflitantes |

### Procedimento para localizar o código autoritativo

1. **Verificar** se existe SCM (Endevor, SCLM, ChangeMan) — se sim, a versão no SCM é autoritativa
2. **Comparar** fonte no workspace VisualAge com fonte no PDS do mainframe — se divergem, investigar qual é mais recente
3. **Verificar** a data de modificação do member no PDS (`ISPF statistics`)
4. **Verificar** a data do arquivo local no workspace
5. **Verificar** se o load module em produção corresponde ao fonte encontrado — compilar e comparar ou verificar timestamps de compilação no AMBLIST/listing
6. **Documentar** qual versão foi usada como base para modernização

---

## 7. Ciclo de compilação e linkedit

O VisualAge automatiza o processo de build que no mainframe nativo seria feito via JCL. Entender esse ciclo é essencial para saber quais artefatos são gerados e como chegam a produção.

### Pipeline de build

```
Fonte COBOL (.cbl)
    │
    ▼
┌──────────────────────────────────────────────────┐
│  1. PRÉ-COMPILAÇÃO (se usa DB2)                  │
│     Input:  fonte COBOL com EXEC SQL             │
│     Output: fonte COBOL modificado + DBRM         │
│     Tool:   DSNHPC (DB2 Pre-compiler)            │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  2. COMPILAÇÃO                                    │
│     Input:  fonte COBOL (+ copybooks via SYSLIB)  │
│     Output: object module (.OBJ)                  │
│     Tool:   IGYCRCTL (Enterprise COBOL Compiler)  │
│     Opções: LIST, MAP, XREF, OPTIMIZE             │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  3. LINKEDIT                                      │
│     Input:  object module + sub-rotinas            │
│     Output: load module (executável)               │
│     Tool:   IEWL / IEWBLINK (Binder)              │
│     Opções: RENT, REUS, AMODE, RMODE              │
└──────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────┐
│  4. BIND (se usa DB2)                             │
│     Input:  DBRM (do passo 1)                     │
│     Output: package/plan no DB2                    │
│     Tool:   DSNTIAD / BIND PACKAGE               │
└──────────────────────────────────────────────────┘
    │
    ▼
Load module em LOADLIB → pronto para execução
```

### Artefatos gerados em cada passo

| Passo | Artefato | PDS destino | Para que serve |
|---|---|---|---|
| Pré-compilação | DBRM | `*.DBRMLIB` | Contém SQL preparado para BIND no DB2 |
| Pré-compilação | Fonte modificado | temporário | Fonte com EXEC SQL substituído por CALLs |
| Compilação | Object module | `*.OBJLIB` | Código máquina relocável, sem resolver referências externas |
| Compilação | Listing | `*.LISTLIB` ou SYSOUT | Diagnóstico: mapa de dados, referência cruzada, erros |
| Linkedit | Load module | `*.LOADLIB` | Executável final, com todas as referências resolvidas |
| BIND | DB2 Package/Plan | Catálogo DB2 | Plano de acesso otimizado para os SQLs do programa |

### Como o VisualAge gerencia o build

O VisualAge configura o build através de **perfis de compilação** (build profiles ou build descriptors) que definem:

```
Build Profile (exemplo):
  Compilador:        IGYCRCTL
  Opções COBOL:      LIB,RENT,RES,APOST,MAP,XREF
  SYSLIB (copybooks): DESENV.PROJCONT.COPYLIB
                       DESENV.SHARED.COPYLIB
                       PROD.SYSTEM.COPYLIB
  Pre-compiler:       DSNHPC (DB2 V12)
  Linkedit options:    RENT,REUS,AMODE(31),RMODE(ANY)
  SYSLIB (linkedit):   CEE.SCEELKED (Language Environment)
                        DESENV.PROJCONT.OBJLIB
  Target LOADLIB:      DESENV.PROJCONT.LOADLIB
```

### Implicações para modernização

1. **SYSLIB do compilador** revela todas as dependências de copybook — seguir essa cadeia para encontrar todos os includes
2. **SYSLIB do linkedit** revela sub-rotinas linkadas estaticamente — são dependências de código que não aparecem como `CALL` dinâmico
3. **Opções do compilador** podem afetar o comportamento (ex.: `NUMPROC(NOPFD)` muda a interpretação de campos numéricos)
4. **DBRM** contém os SQLs reais executados — comparar com o fonte para validar
5. **Load module** é o artefato que realmente roda em produção — se o fonte não gera o mesmo load module, há divergência

---

## 8. Versões e variantes de programas

### O problema das múltiplas versões

No ambiente VisualAge + mainframe, é comum existirem **múltiplas versões do mesmo programa** em locais diferentes. Isso é um dos maiores riscos na modernização.

### Cenários de divergência

```
CALCFOLH (programa de cálculo de folha)
├── Workspace VisualAge (local)     → versão 2023-03-15 (desenvolvedor saiu da empresa)
├── DESENV.SRCLIB (PDS de dev)      → versão 2023-08-20 (correção via ISPF)
├── HOMOL.SRCLIB (PDS de homolog)   → versão 2023-07-10 (versão em teste)
├── PROD.SRCLIB (PDS de produção)   → versão 2023-06-01 (versão em execução)
├── Endevor baseline               → versão 2023-06-01 (mesma da produção, confirmado)
└── PROD.LOADLIB (load compilado)   → compilado em 2023-06-01 (corresponde ao fonte?)
```

### Como o VisualAge gerencia versões

O VisualAge em si **não é um SCM** (Software Configuration Management). Ele mantém a versão corrente no workspace local e pode sincronizar com o mainframe, mas não mantém histórico de versões. O versionamento depende de ferramentas externas:

| Ferramenta | Como versiona | Integração com VisualAge |
|---|---|---|
| Endevor | Ambientes com promoção (DEV→QA→PROD) | Via plugin ou manual (upload/download) |
| SCLM | Hierarquia de bibliotecas com controle de mudanças | Integração direta em alguns casos |
| ChangeMan ZMF | Packages com workflow de aprovação | Via plugin ou manual |
| ISPF direto (sem SCM) | Nenhum controle — sobrescreve o member | Manual (copy/paste) |
| PDS members manuais | Sufixos como CALCFOLH, CALCFOL2, CALCFOLH.BAK | Não há controle real |

### Variantes de programas

Além de versões temporais, podem existir **variantes** — versões paralelas do mesmo programa para diferentes contextos:

```
CALCFOLH   → versão padrão (São Paulo)
CALCFOLHM  → variante Minas Gerais (regras estaduais diferentes)
CALCFOLHR  → variante Rio de Janeiro
CALCFOLHT  → versão de teste com logs extras
CALCFOLHD  → versão debug com DISPLAY em todos os parágrafos
```

### Riscos para modernização

1. **Fonte ≠ executável:** O load module em produção pode ter sido compilado de um fonte que não existe mais ou foi modificado depois
2. **Correções fora do VisualAge:** Desenvolvedores podem ter corrigido bugs diretamente no ISPF sem atualizar o projeto VisualAge
3. **Variantes não documentadas:** Podem existir versões regionais ou de teste que divergem sem documentação
4. **Copybooks desatualizados:** O copybook local pode ser diferente do que está na SYSLIB usada na compilação real
5. **Linkedit com módulos diferentes:** O load module pode incluir object modules de versões diferentes dos fontes disponíveis

### Procedimento para validar a versão correta

1. **Identificar o load module em produção** — verificar em qual LOADLIB o CICS ou JCL de produção aponta
2. **Verificar o timestamp de compilação** do load module (via AMBLIST ou listagem)
3. **Localizar o fonte candidato** — buscar no SCM, PDS de produção, PDS de desenvolvimento, workspace VisualAge
4. **Compilar o fonte candidato** com as mesmas opções e SYSLIB e comparar o object code (ou pelo menos o listing)
5. **Se houver divergência**, rastrear qual fonte gerou o load module em produção — pode ser necessário verificar logs de build, JCLs de compilação ou registros do SCM
6. **Documentar** a versão confirmada e desconsiderar as demais para fins de modernização

---

# PARTE 4 — GUIA PRÁTICO DE ANÁLISE

---

## 9. Procedimento de análise de projeto VisualAge para modernização

### Fase 1 — Inventário

1. **Listar todos os programas** do projeto VisualAge (`.cbl`, `.cpy`, `.bms`)
2. **Classificar cada programa:**
   - Batch (executado via JCL) vs Online (CICS) vs Sub-programa (CALL/LINK)
   - Gerado pelo VisualAge vs codificado manualmente
   - Ativo (tem correspondente em produção) vs inativo (código morto)
3. **Listar todos os copybooks** referenciados e verificar sua localização
4. **Documentar os build profiles** — opções de compilação, SYSLIB, targets

### Fase 2 — Rastreamento de dependências

1. **Construir grafo de chamadas** (CALL, LINK, XCTL) entre programas
2. **Mapear copybooks** para programas que os usam
3. **Identificar dependências de dados** — quais programas acessam os mesmos datasets/tabelas
4. **Cruzar com JCL/CICS** — quais programas são invocados por quais jobs/transações
5. **Identificar dependências externas** — programas de outros projetos, utilitários IBM, sub-rotinas de biblioteca

### Fase 3 — Validação de fontes

1. **Comparar fontes** do workspace VisualAge com PDSs do mainframe
2. **Identificar a versão autoritativa** para cada programa
3. **Verificar correspondência fonte ↔ load module** para programas críticos
4. **Documentar divergências** e decidir qual versão usar para modernização

### Fase 4 — Triagem para modernização

1. **Separar código gerado** (descartar — reconstruir com ferramentas modernas)
2. **Separar código de interface** (redesenhar — não traduzir tela 3270)
3. **Separar código de acesso a dados** (substituir por repositório/DAO)
4. **Isolar código de negócio** (preservar — extrair regras com cuidado)
5. **Priorizar** por criticidade de negócio e risco técnico

---

## 10. Antipadrões e armadilhas comuns

### Armadilha 1: Confiar no workspace local

**Erro:** Assumir que o código no workspace VisualAge é a versão em produção.
**Realidade:** O workspace pode estar anos desatualizado. Sempre validar contra o mainframe.

### Armadilha 2: Ignorar código gerado

**Erro:** Tentar modernizar código gerado pelo VisualAge linha por linha.
**Realidade:** Código gerado deve ser entendido no nível de **o que o gerador fazia**, não no nível de cada linha COBOL. A modernização deve recriar a funcionalidade com ferramentas modernas equivalentes.

### Armadilha 3: Grafo de dependências incompleto

**Erro:** Considerar apenas `CALL` literal para dependências.
**Realidade:** Dependências incluem `CALL` dinâmico, `LINK/XCTL` CICS, copybooks, datasets compartilhados, MQ messages, DB2 stored procedures e programas invocados via scheduler (CA-7, Control-M).

### Armadilha 4: Copybooks locais divergentes

**Erro:** Usar o copybook que está na pasta do projeto VisualAge.
**Realidade:** O compilador no mainframe usa a SYSLIB configurada no JCL, que pode apontar para um PDS diferente com uma versão diferente do copybook.

### Armadilha 5: Variantes não identificadas

**Erro:** Modernizar um programa sem verificar se existem variantes regionais ou de teste.
**Realidade:** Podem existir N versões do mesmo programa com diferenças sutis. A modernização precisa consolidar ou manter as variantes de forma explícita.

### Armadilha 6: Build profile desatualizado

**Erro:** Usar as configurações de build do VisualAge para entender como o programa é compilado.
**Realidade:** Se o VisualAge foi abandonado, a compilação real pode usar JCLs e PROCs diferentes das configuradas no IDE. Verificar o JCL de compilação usado em produção.

---

## Checklist geral — Análise de projeto VisualAge para modernização

### Inventário de projeto

- [ ] Listar todos os programas COBOL do projeto VisualAge
- [ ] Classificar programas: batch / online (CICS) / sub-programa
- [ ] Identificar programas gerados vs manuais
- [ ] Listar todos os copybooks referenciados
- [ ] Documentar build profiles (opções de compilação, SYSLIB, targets)
- [ ] Identificar mapeamentos de PDS (workspace → mainframe)

### Dependências

- [ ] Extrair todos os `CALL` (literal e dinâmico) de cada programa
- [ ] Extrair todos os `EXEC CICS LINK/XCTL` de cada programa
- [ ] Extrair todos os `COPY` statements de cada programa
- [ ] Construir grafo dirigido de dependências
- [ ] Identificar pontos de entrada (programas raiz)
- [ ] Identificar programas órfãos (nunca chamados — possível código morto)
- [ ] Mapear dependências de dados (datasets/tabelas compartilhados)

### Validação de fontes

- [ ] Comparar fontes locais (workspace) com fontes no mainframe (PDS)
- [ ] Identificar versão autoritativa para cada programa
- [ ] Verificar correspondência fonte ↔ load module em produção
- [ ] Documentar divergências encontradas
- [ ] Verificar copybooks: versão local vs SYSLIB real

### Triagem para modernização

- [ ] Separar código gerado (descartar/reconstruir)
- [ ] Separar código de interface (redesenhar)
- [ ] Separar código de acesso a dados (substituir por DAO/repositório)
- [ ] Isolar e preservar código de negócio
- [ ] Priorizar por criticidade e risco

---

## Definition of Done (Análise de projeto VisualAge)

- [ ] Inventário completo de programas e copybooks
- [ ] Grafo de dependências reconstruído e validado
- [ ] Versão autoritativa identificada para cada programa
- [ ] Código gerado separado de código manual
- [ ] Regras de negócio isoladas e documentadas
- [ ] Divergências de versão documentadas e resolvidas
- [ ] Build pipeline entendido (compilação, linkedit, BIND)
- [ ] Mapeamentos PDS documentados (workspace ↔ mainframe)
