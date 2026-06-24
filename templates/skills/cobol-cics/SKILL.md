---
name: cobol-cics
description: Skill para leitura, interpretação e modernização de programas COBOL e COBOL CICS em ambiente mainframe IBM z/OS. Use quando a tarefa envolver análise de código legado COBOL, extração de regras de negócio, mapeamento de estruturas de dados, identificação de dependências e planejamento de modernização.
---

# COBOL & COBOL CICS — Leitura, Interpretação e Modernização

## Objetivo desta skill

Capacitar o agente a **ler, interpretar semanticamente e modernizar** programas COBOL batch e COBOL CICS online executados em ambiente mainframe IBM z/OS. O foco é extrair significado de negócio — não apenas traduzir sintaxe.

---

## Contexto do ambiente

| Componente | Tecnologia |
|---|---|
| Plataforma | IBM z/OS |
| Linguagem | COBOL 85 / Enterprise COBOL |
| Subsistema online | CICS Transaction Server |
| Acesso a dados | VSAM (KSDS, ESDS, RRDS), DB2, arquivos sequenciais |
| Apresentação | BMS Maps (3270 terminals) |
| Controle de jobs | JCL (Job Control Language) |
| Copybooks | COPY members em PDS (Partitioned Data Set) |

---

# PARTE 1 — COBOL BATCH

---

## 1. Estrutura de DIVISIONS — significado semântico

Um programa COBOL é dividido em 4 DIVISIONS obrigatórias. Cada uma tem um papel semântico distinto que mapeia diretamente para conceitos modernos:

### IDENTIFICATION DIVISION
```cobol
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CALC-FOLHA.
       AUTHOR. EQUIPE-RH.
```
**Significado:** Metadados do programa — equivalente a um header de módulo, `package-info.java` ou docblock de arquivo. O `PROGRAM-ID` é o identificador único usado em chamadas `CALL`, `LINK` e `XCTL`.

### ENVIRONMENT DIVISION
```cobol
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       SPECIAL-NAMES.
           DECIMAL-POINT IS COMMA.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ARQ-CLIENTES ASSIGN TO ARQCLI
               ORGANIZATION IS INDEXED
               ACCESS MODE IS DYNAMIC
               RECORD KEY IS CLI-CPF
               FILE STATUS IS WS-FILE-STATUS.
```
**Significado:** Configuração de infraestrutura — mapeia recursos externos (arquivos, impressoras, character sets). Equivale a configuração de datasources, connection strings e variáveis de ambiente. O `FILE-CONTROL` é o ponto onde se declaram **todas as dependências de I/O** do programa.

**Na modernização:** Cada `SELECT` representa uma dependência de dados que precisa ser mapeada para um repositório, tabela ou serviço externo.

### DATA DIVISION
```cobol
       DATA DIVISION.
       FILE SECTION.
       FD ARQ-CLIENTES.
       01 REG-CLIENTE.
           05 CLI-CPF        PIC 9(11).
           05 CLI-NOME        PIC X(40).
           05 CLI-SALDO       PIC S9(13)V99 COMP-3.
       WORKING-STORAGE SECTION.
       01 WS-CONTADORES.
           05 WS-TOTAL-LIDOS  PIC 9(7) VALUE ZEROS.
           05 WS-TOTAL-ERROS  PIC 9(5) VALUE ZEROS.
```
**Significado:** Modelo de dados completo do programa — define **todas** as estruturas de dados usadas. É o equivalente a declarações de classes/records/DTOs, variáveis de estado e constantes. A `FILE SECTION` descreve o layout dos registros de I/O. A `WORKING-STORAGE` é o estado mutável do programa.

### PROCEDURE DIVISION
```cobol
       PROCEDURE DIVISION.
       0000-PRINCIPAL.
           PERFORM 1000-INICIALIZAR
           PERFORM 2000-PROCESSAR UNTIL WS-FIM-ARQUIVO = 'S'
           PERFORM 3000-FINALIZAR
           STOP RUN.
```
**Significado:** Lógica de execução — equivale ao corpo de métodos, funções e fluxo de controle. Os parágrafos e seções são **unidades de código** (não são funções com escopo isolado — compartilham todo o estado da WORKING-STORAGE).

**Atenção na modernização:** Parágrafos COBOL **não têm escopo léxico**. Todo dado é global. Ao extrair para funções/métodos modernos, é preciso identificar quais variáveis cada parágrafo realmente usa e passá-las como parâmetros ou encapsulá-las.

---

## 2. PIC Clauses — inferência de tipo de dado real

A cláusula `PIC` (PICTURE) define o formato de armazenamento. O agente deve saber inferir o tipo semântico real:

### Tabela de mapeamento PIC → tipo moderno

| PIC Clause | USAGE | Tipo real | Equivalente moderno | Bytes |
|---|---|---|---|---|
| `PIC X(30)` | DISPLAY | Alfanumérico | `string` (30 chars) | 30 |
| `PIC 9(5)` | DISPLAY | Numérico zoned decimal | `int` (0-99999) | 5 |
| `PIC S9(5)` | DISPLAY | Numérico com sinal (zoned) | `int` (-99999 a 99999) | 5 |
| `PIC S9(7)V99` | DISPLAY | Decimal com 2 casas (zoned) | `decimal(9,2)` | 9 |
| `PIC S9(7)V99 COMP-3` | COMP-3 | Decimal compactado (packed) | `decimal(9,2)` | 5 |
| `PIC S9(9) COMP` / `COMP-4` | COMP | Binário com sinal | `int` / `long` | 4 |
| `PIC S9(18) COMP` | COMP | Binário longo | `long` | 8 |
| `PIC 9(4) COMP` | COMP | Binário sem sinal | `unsigned short` | 2 |

### Regras de interpretação

- **`V` implícito:** `PIC 9(5)V99` tem 2 casas decimais, mas **não há ponto no armazenamento**. O valor `0012345` representa `123.45`. Na modernização, esse ponto decimal precisa ser explicitado.
- **`S` (sinal):** Sem `S`, o campo é **sempre positivo**. Com `S` em DISPLAY, o sinal fica embutido no último byte (overpunch). Com `COMP-3`, o último nibble é o sinal.
- **`COMP-3` (packed decimal):** Cada byte armazena 2 dígitos, exceto o último que tem 1 dígito + sinal. Fórmula de bytes: `(n + 2) / 2` arredondado para baixo, onde n = total de dígitos.
- **`COMP` / `COMP-4` (binário):** Armazenado em 2, 4 ou 8 bytes conforme a faixa de dígitos declarada.

### Exemplo de análise

```cobol
       05 VALOR-TOTAL    PIC S9(13)V99 COMP-3.
```
**Análise:** Campo numérico com sinal, 13 dígitos inteiros e 2 decimais, armazenado em packed decimal. Ocupa `(15 + 2) / 2 = 8` bytes (arredondado). Tipo moderno: `decimal(15,2)` ou `BigDecimal`. Faixa: -9999999999999.99 a +9999999999999.99.

---

## 3. REDEFINES — múltiplas interpretações do mesmo espaço de memória

```cobol
       01 REG-TRANSACAO.
           05 TRANS-TIPO          PIC X(1).
           05 TRANS-DADOS         PIC X(100).
           05 TRANS-DEBITO REDEFINES TRANS-DADOS.
               10 DEB-CONTA       PIC 9(10).
               10 DEB-VALOR       PIC S9(11)V99 COMP-3.
               10 DEB-DATA        PIC 9(8).
               10 FILLER          PIC X(75).
           05 TRANS-CREDITO REDEFINES TRANS-DADOS.
               10 CRED-CONTA-ORIG PIC 9(10).
               10 CRED-CONTA-DEST PIC 9(10).
               10 CRED-VALOR      PIC S9(11)V99 COMP-3.
               10 FILLER          PIC X(73).
```

### Significado semântico

`REDEFINES` é uma **union** — o mesmo bloco de memória física é interpretado de formas diferentes conforme o contexto. Geralmente, há um campo discriminador (como `TRANS-TIPO`) que indica qual interpretação é válida.

### Riscos na modernização

1. **Leitura sem discriminador:** Se o código lê `TRANS-DEBITO` sem verificar `TRANS-TIPO`, pode estar interpretando dados de crédito como débito — lixo semântico.
2. **Sobreposição parcial:** Os campos podem se sobrepor parcialmente. Mudanças em um campo via um REDEFINES afetam campos do outro.
3. **Mapeamento moderno:** Traduzir para **herança ou tipos discriminados** (discriminated unions, sealed classes, enums com data):
   ```typescript
   type Transacao =
     | { tipo: 'D'; conta: string; valor: number; data: string }
     | { tipo: 'C'; contaOrigem: string; contaDestino: string; valor: number }
   ```

---

## 4. PERFORM — loops e controle de fluxo

### PERFORM simples (chamada de parágrafo)

```cobol
           PERFORM 2000-VALIDAR-CPF
```
Equivalente a uma chamada de função/método (mas sem escopo isolado).

### PERFORM UNTIL (while loop)

```cobol
           PERFORM 2000-PROCESSAR-REGISTRO
               UNTIL WS-FIM-ARQUIVO = 'S'
```
Equivalente moderno:
```python
while not fim_arquivo:
    processar_registro()
```

### PERFORM VARYING (for loop)

```cobol
           PERFORM 3000-CALCULAR
               VARYING WS-IDX FROM 1 BY 1
               UNTIL WS-IDX > WS-TOTAL-ITENS
```
Equivalente moderno:
```python
for idx in range(1, total_itens + 1):
    calcular(idx)
```

### PERFORM ... TIMES

```cobol
           PERFORM 4000-RETRY 3 TIMES
```
Equivalente moderno:
```python
for _ in range(3):
    retry()
```

### PERFORM THRU (range de parágrafos)

```cobol
           PERFORM 2000-INICIO THRU 2999-FIM
```
**Atenção:** Executa todos os parágrafos no range sequencial. Isso cria acoplamento implícito pela posição física do código. Na modernização, é preciso identificar quais parágrafos estão no range e extrair cada um explicitamente.

---

## 5. Copybooks (COPY) — inclusão de código e dependências externas

```cobol
       COPY REGCLIENTE.
       COPY WSCOMUNS REPLACING ==:PREFIX:== BY ==WS-==.
```

### Significado

`COPY` é equivalente a `#include` em C ou `import` — insere literalmente o conteúdo de um member de uma PDS no ponto da inclusão. Copybooks tipicamente contêm:

- **Layouts de registro** (01-level com campos) — contratos de dados
- **Constantes e tabelas** (88-levels, VALUES)
- **Working-storage comuns** — variáveis compartilhadas entre programas

### Identificação de dependências

Todo `COPY` é uma **dependência externa**. Para modernizar um programa, é necessário:

1. Listar todos os `COPY` statements
2. Localizar os members correspondentes nas PDSs
3. Analisar o conteúdo de cada copybook — eles definem os contratos de dados compartilhados
4. Identificar quais outros programas usam os mesmos copybooks (acoplamento)

### REPLACING

```cobol
       COPY REGBASE REPLACING ==:TAG:== BY ==CLI-==.
```
Funciona como um **template com substituição de texto**. O copybook usa placeholders (`:TAG:`) que são substituídos na inclusão. Na modernização, isso se traduz para generics, type parameters ou factories.

---

## 6. Truncamento silencioso em MOVE

```cobol
       05 CAMPO-ORIGEM   PIC X(20) VALUE 'TEXTO MUITO GRANDE XX'.
       05 CAMPO-DESTINO  PIC X(10).
       ...
           MOVE CAMPO-ORIGEM TO CAMPO-DESTINO
```

### Comportamento

COBOL **não emite erro** ao mover dados entre campos de tamanhos diferentes:

- **Alfanumérico (PIC X):** Trunca pela **direita**, preenche com espaços pela direita se menor.
- **Numérico (PIC 9):** Trunca pela **esquerda** (dígitos mais significativos), preenche com zeros pela esquerda se menor.

### Risco na modernização

```cobol
       05 WS-VALOR-GRANDE  PIC S9(11)V99 COMP-3.
       05 WS-VALOR-PEQUENO PIC S9(5)V99 COMP-3.
       ...
           MOVE WS-VALOR-GRANDE TO WS-VALOR-PEQUENO
```
Se `WS-VALOR-GRANDE` contém `12345678.90`, após o MOVE `WS-VALOR-PEQUENO` terá `45678.90` — os dígitos `123` são **silenciosamente descartados**. Na modernização, esse comportamento deve ser substituído por **validação explícita** ou cast com verificação de overflow.

### Checklist para o agente

- Ao encontrar um `MOVE` entre campos de tamanhos diferentes, **alertar** sobre possível truncamento
- Verificar se o truncamento é intencional (ex: extrair parte de um campo) ou um bug latente
- Na tradução moderna, usar conversões explícitas com verificação de limites

---

## 7. FILE SECTION e FD — acesso a dados

### Arquivo sequencial

```cobol
       ENVIRONMENT DIVISION.
       FILE-CONTROL.
           SELECT ARQ-ENTRADA ASSIGN TO ARQENT
               FILE STATUS IS WS-FS-ENTRADA.

       DATA DIVISION.
       FILE SECTION.
       FD ARQ-ENTRADA
           RECORDING MODE IS F
           RECORD CONTAINS 150 CHARACTERS
           BLOCK CONTAINS 0 RECORDS.
       01 REG-ENTRADA          PIC X(150).
```

**Significado:** Arquivo sequencial com registros de tamanho fixo (150 bytes). `RECORDING MODE F` = fixo, `V` = variável. `BLOCK CONTAINS 0` = o sistema determina o bloco.

**Equivalente moderno:** Leitura de arquivo texto linha a linha ou stream de bytes com parsing posicional.

### Arquivo VSAM (KSDS — Key-Sequenced)

```cobol
       FILE-CONTROL.
           SELECT ARQ-CLIENTES ASSIGN TO ARQCLI
               ORGANIZATION IS INDEXED
               ACCESS MODE IS DYNAMIC
               RECORD KEY IS CLI-CPF
               ALTERNATE RECORD KEY IS CLI-NOME WITH DUPLICATES
               FILE STATUS IS WS-FS-CLI.
```

**Significado:**
- `ORGANIZATION IS INDEXED` → VSAM KSDS (key-value store com índices)
- `ACCESS MODE IS DYNAMIC` → permite acesso sequencial E randômico
- `RECORD KEY` → chave primária (equivalente a PK em banco relacional)
- `ALTERNATE RECORD KEY` → índice secundário (equivalente a índice em banco)

**Equivalente moderno:** Tabela de banco de dados com índices, ou um key-value store como DynamoDB/Redis.

### FILE STATUS — códigos de retorno de I/O

```cobol
       05 WS-FILE-STATUS   PIC X(2).
           88 WS-FS-OK         VALUE '00'.
           88 WS-FS-EOF        VALUE '10'.
           88 WS-FS-NOT-FOUND  VALUE '23'.
           88 WS-FS-DUPLICATE  VALUE '22'.
```

| Código | Significado | Equivalente moderno |
|---|---|---|
| `00` | Operação OK | Sucesso (200) |
| `10` | End of file | EOF / `StopIteration` |
| `22` | Duplicate key | `DuplicateKeyException` (409) |
| `23` | Record not found | `NotFoundException` (404) |
| `35` | File not found | `FileNotFoundException` |
| `39` | Conflito de atributos | Erro de configuração |

---

## 8. EVALUATE — switch/case

```cobol
           EVALUATE TRANS-TIPO
               WHEN 'D'
                   PERFORM 5000-PROCESSAR-DEBITO
               WHEN 'C'
                   PERFORM 5100-PROCESSAR-CREDITO
               WHEN 'T'
                   PERFORM 5200-PROCESSAR-TRANSFERENCIA
               WHEN OTHER
                   MOVE 'TIPO INVALIDO' TO WS-MSG-ERRO
                   PERFORM 9000-TRATAR-ERRO
           END-EVALUATE
```

### Formas avançadas

```cobol
           EVALUATE TRUE
               WHEN WS-IDADE < 18
                   MOVE 'MENOR' TO WS-CATEGORIA
               WHEN WS-IDADE < 60
                   MOVE 'ADULTO' TO WS-CATEGORIA
               WHEN WS-IDADE >= 60
                   MOVE 'IDOSO' TO WS-CATEGORIA
           END-EVALUATE
```

```cobol
           EVALUATE TRANS-TIPO ALSO WS-STATUS
               WHEN 'D'     ALSO 'A'
                   PERFORM 5000-DEBITO-ATIVO
               WHEN 'D'     ALSO 'I'
                   PERFORM 5010-DEBITO-INATIVO
               WHEN 'C'     ALSO ANY
                   PERFORM 5100-CREDITO
               WHEN OTHER
                   PERFORM 9000-ERRO
           END-EVALUATE
```

### Mapeamento moderno

- `EVALUATE` simples → `switch/case` ou `match`
- `EVALUATE TRUE` → cadeia `if/else if` ou pattern matching com guardas
- `EVALUATE ... ALSO ...` → pattern matching com tuplas ou múltiplos critérios

```python
match (trans_tipo, status):
    case ('D', 'A'): debito_ativo()
    case ('D', 'I'): debito_inativo()
    case ('C', _):   credito()
    case _:          erro()
```

---

## 9. Padrões de tratamento de erros

### 88-levels (condition names)

```cobol
       05 WS-STATUS-PROC     PIC X(2).
           88 WS-PROC-OK         VALUE '00'.
           88 WS-PROC-ERRO       VALUE '99'.
           88 WS-PROC-WARNING    VALUE '04'.
```

**Significado:** `88-levels` são **condições nomeadas** — aliases booleanos para valores específicos de um campo. São o equivalente a enums ou constantes nomeadas.

```cobol
           IF WS-PROC-OK
               PERFORM 3000-CONTINUAR
           END-IF
```
Equivale a:
```python
if status_proc == StatusProc.OK:
    continuar()
```

### Flags de controle

```cobol
       01 WS-FLAGS.
           05 WS-FIM-ARQUIVO     PIC X(1) VALUE 'N'.
               88 WS-EOF             VALUE 'S'.
               88 WS-NOT-EOF         VALUE 'N'.
           05 WS-ERRO-GRAVE      PIC X(1) VALUE 'N'.
               88 WS-TEM-ERRO        VALUE 'S'.
               88 WS-SEM-ERRO        VALUE 'N'.
```

**Padrão:** Flags `PIC X(1)` com `88-levels` são o equivalente a variáveis booleanas. O idioma `SET WS-EOF TO TRUE` equivale a `fim_arquivo = True`.

### RETURN-CODE (código de retorno do programa)

```cobol
           MOVE 0 TO RETURN-CODE     *> sucesso
           MOVE 8 TO RETURN-CODE     *> erro tratável
           MOVE 16 TO RETURN-CODE    *> erro fatal
           STOP RUN.
```

**Convenção de mainframe:**
- `0` = sucesso
- `4` = warning
- `8` = erro
- `12`/`16` = erro grave/fatal

O JCL que chama o programa testa esse código via `COND` ou `IF` para decidir se executa os próximos steps.

**Equivalente moderno:** Exit codes de processo ou códigos de status HTTP.

---

# PARTE 2 — COBOL CICS

---

## 10. Programação pseudoconversacional

### O que é

Em um mainframe CICS, o terminal 3270 conecta centenas/milhares de usuários simultâneos. Para economizar recursos, CICS **não mantém o programa na memória** enquanto o usuário digita. O fluxo é:

```
1. Programa envia tela (SEND MAP) → programa TERMINA (RETURN TRANSID)
2. Usuário preenche dados e tecla ENTER
3. CICS inicia NOVA instância do programa
4. Programa recebe dados (RECEIVE MAP) → processa → envia nova tela → TERMINA
```

### Implicações para o estado

```cobol
           EXEC CICS RETURN
               TRANSID('TRNS')
               COMMAREA(WS-COMMAREA)
               LENGTH(LENGTH OF WS-COMMAREA)
           END-EXEC
```

- **Não há estado em memória** entre interações — tudo que precisa sobreviver deve ir para o `COMMAREA` ou ser gravado em arquivo/DB2.
- O `COMMAREA` é o **único mecanismo de estado** entre "telas" do mesmo programa.
- Cada `RETURN TRANSID` é equivalente a um **response HTTP** — o programa morre após enviar.

### Como detectar no código

```cobol
           EVALUATE TRUE
               WHEN EIBCALEN = 0
                   PERFORM 1000-PRIMEIRA-VEZ
               WHEN OTHER
                   PERFORM 2000-RETORNO-USUARIO
           END-EVALUATE
```

- `EIBCALEN = 0` → primeira execução (não há COMMAREA anterior)
- `EIBCALEN > 0` → retorno do usuário (há COMMAREA com estado da interação anterior)

### Mapeamento moderno

| CICS Pseudoconversacional | Equivalente moderno |
|---|---|
| `RETURN TRANSID` com COMMAREA | Response HTTP + session token / JWT |
| COMMAREA como estado | Session storage / estado no client / Redis |
| `EIBCALEN = 0` (primeira vez) | GET na rota inicial |
| `EIBCALEN > 0` (retorno) | POST com payload do form |
| Programa termina e reinicia | Stateless request-response |

---

## 11. EXEC CICS READ/WRITE/REWRITE/DELETE — operações CRUD

### READ (Read)

```cobol
           EXEC CICS READ
               FILE('ARQCLI')
               INTO(WS-REG-CLIENTE)
               RIDFLD(WS-CPF-BUSCA)
               RESP(WS-RESP)
           END-EXEC
```
Equivalente: `SELECT * FROM clientes WHERE cpf = :cpf` ou `repository.findById(cpf)`

### READ com UPDATE (Read for Update — lock pessimista)

```cobol
           EXEC CICS READ
               FILE('ARQCLI')
               INTO(WS-REG-CLIENTE)
               RIDFLD(WS-CPF-BUSCA)
               UPDATE
               RESP(WS-RESP)
           END-EXEC
```
Equivalente: `SELECT ... FOR UPDATE` — bloqueia o registro para outros. O REWRITE ou DELETE subsequente libera o lock.

### WRITE (Create)

```cobol
           EXEC CICS WRITE
               FILE('ARQCLI')
               FROM(WS-REG-CLIENTE)
               RIDFLD(WS-CPF-NOVO)
               RESP(WS-RESP)
           END-EXEC
```
Equivalente: `INSERT INTO clientes ...` ou `repository.save(cliente)`

### REWRITE (Update)

```cobol
           EXEC CICS REWRITE
               FILE('ARQCLI')
               FROM(WS-REG-CLIENTE)
               RESP(WS-RESP)
           END-EXEC
```
Equivalente: `UPDATE clientes SET ... WHERE cpf = :cpf` ou `repository.update(cliente)`.
**Precondição:** Deve ter sido precedido por `READ ... UPDATE`.

### DELETE

```cobol
           EXEC CICS DELETE
               FILE('ARQCLI')
               RIDFLD(WS-CPF-DELETE)
               RESP(WS-RESP)
           END-EXEC
```
Equivalente: `DELETE FROM clientes WHERE cpf = :cpf` ou `repository.delete(cpf)`

### Mapeamento CRUD consolidado

| CICS Command | SQL Equivalente | REST Equivalente | Repository Pattern |
|---|---|---|---|
| `READ` | `SELECT` | `GET` | `findById()` |
| `READ UPDATE` | `SELECT FOR UPDATE` | — | `findByIdForUpdate()` |
| `WRITE` | `INSERT` | `POST` | `save()` |
| `REWRITE` | `UPDATE` | `PUT` | `update()` |
| `DELETE` | `DELETE` | `DELETE` | `delete()` |

---

## 12. SEND MAP / RECEIVE MAP — camada de apresentação

### SEND MAP (renderizar tela)

```cobol
           MOVE 'CLIENTE NAO ENCONTRADO' TO MSGO
           MOVE WS-NOME TO NOMEO
           MOVE WS-SALDO TO SALDOO

           EXEC CICS SEND
               MAP('MAPCLI')
               MAPSET('MSCLI')
               FROM(MAPCLIO)
               ERASE
           END-EXEC
```

**Significado:**
- `MAP` → nome do mapa (tela) dentro do mapset
- `MAPSET` → conjunto de mapas (equivalente a um módulo de views)
- `FROM(MAPCLIO)` → estrutura de dados com os valores dos campos da tela (sufixo `O` = output)
- `ERASE` → limpa a tela antes de desenhar

### RECEIVE MAP (ler dados do usuário)

```cobol
           EXEC CICS RECEIVE
               MAP('MAPCLI')
               MAPSET('MSCLI')
               INTO(MAPCLIO)
           END-EXEC

           MOVE CPFI TO WS-CPF-BUSCA
           MOVE NOMEI TO WS-NOME-BUSCA
```

**Significado:**
- `INTO(MAPCLIO)` → preenche a estrutura com dados digitados pelo usuário
- Campos com sufixo `I` = input (o que o usuário digitou)
- Campos com sufixo `O` = output (o que será exibido na tela)

### Estrutura de um mapa (gerada pelo BMS)

```cobol
       01 MAPCLIO.
           05 FILLER              PIC X(12).
           05 CPFL                PIC S9(4) COMP.    *> comprimento
           05 CPFF                PIC X.              *> flag de atributo
           05 FILLER REDEFINES CPFF.
               10 CPFA            PIC X.              *> atributo modificado
           05 CPFI                PIC X(11).          *> input (do usuário)
           05 CPFO REDEFINES CPFI PIC X(11).          *> output (para tela)
```

Cada campo do mapa tem 3 subcampos:
- `L` (length) — quantos caracteres o usuário digitou
- `F`/`A` (flag/attribute) — se o campo foi modificado
- `I`/`O` (input/output) — dado digitado / dado a exibir

### Como extrair a lógica de apresentação

1. **Identificar todos os `SEND MAP` e `RECEIVE MAP`** — esses são os pontos de interação com o usuário
2. **Mapear campos do mapa para campos de formulário** — `CPFI` → `<input name="cpf">`
3. **Extrair validações feitas após `RECEIVE MAP`** — são validações de front-end que podem ir para o client
4. **Separar formatação de dados** — MOVEs que apenas formatam para exibição (`MOVE WS-SALDO TO SALDOO`) são lógica de view

---

## 13. EXEC CICS LINK e XCTL — chamadas entre programas

### LINK (call com retorno)

```cobol
           EXEC CICS LINK
               PROGRAM('PGMVALID')
               COMMAREA(WS-DADOS-VALIDACAO)
               LENGTH(LENGTH OF WS-DADOS-VALIDACAO)
               RESP(WS-RESP)
           END-EXEC
```

**Significado:** Chama outro programa CICS e **aguarda o retorno**. O programa chamado recebe o COMMAREA, processa e devolve o controle ao chamador. É equivalente a:
- Chamada de método síncrono
- Request HTTP síncrono para um microserviço
- `await service.validate(dados)`

O programa chamado acessa os dados via:
```cobol
       LINKAGE SECTION.
       01 DFHCOMMAREA.
           05 LK-CPF        PIC 9(11).
           05 LK-RESULTADO   PIC X(2).
```

### XCTL (transfer of control — sem retorno)

```cobol
           EXEC CICS XCTL
               PROGRAM('PGMMENU')
               COMMAREA(WS-DADOS-MENU)
               LENGTH(LENGTH OF WS-DADOS-MENU)
           END-EXEC
```

**Significado:** Transfere controle para outro programa **sem retorno** — o programa atual é descarregado da memória. É equivalente a:
- `redirect` HTTP (302/303)
- Navegação de rota em SPA
- `goto` de programa (o contexto do chamador é perdido)

### Diferença crítica

| | LINK | XCTL |
|---|---|---|
| Retorno | Sim — volta ao chamador | Não — o chamador é destruído |
| Analogia | Function call / HTTP request | Redirect / Route navigation |
| Stack | Empilha | Substitui |
| Uso típico | Validação, cálculo, consulta | Navegação entre telas/módulos |

---

## 14. COMMAREA — contrato de dados entre programas

```cobol
       01 WS-COMMAREA.
           05 CA-OPERACAO         PIC X(1).
               88 CA-INCLUIR         VALUE 'I'.
               88 CA-ALTERAR         VALUE 'A'.
               88 CA-CONSULTAR       VALUE 'C'.
               88 CA-EXCLUIR         VALUE 'E'.
           05 CA-CPF              PIC 9(11).
           05 CA-NOME             PIC X(40).
           05 CA-SALDO            PIC S9(13)V99 COMP-3.
           05 CA-RETORNO          PIC X(2).
               88 CA-RET-OK          VALUE '00'.
               88 CA-RET-NOT-FOUND   VALUE '01'.
               88 CA-RET-DUPLICADO   VALUE '02'.
               88 CA-RET-ERRO        VALUE '99'.
```

### Significado

O COMMAREA é o **contrato de dados** (DTO/payload) entre programas CICS. Ele serve como:

1. **Request/Response body** — o chamador preenche os campos de entrada, o chamado preenche os campos de saída
2. **Estado entre interações** — no pseudoconversacional, é o "session state"
3. **Contrato de API** — define exatamente quais dados transitam entre programas

### Características

- Tamanho máximo: 32.763 bytes (CICS TS 5.x) — mas na prática limita-se a poucos KB
- É uma **área de memória contígua** — sem ponteiros, sem referências
- O layout é definido por convenção (copybook compartilhado), não por schema formal
- Alterações no layout são **breaking changes** — todos os programas que usam precisam ser recompilados

### Mapeamento moderno

| Aspecto COMMAREA | Equivalente moderno |
|---|---|
| Layout do COMMAREA | DTO / Schema (JSON, Protobuf, Avro) |
| Copybook compartilhado | Biblioteca de contratos / OpenAPI spec |
| COMMAREA de request | Request body / Command object |
| COMMAREA de response | Response body / Result object |
| Versionamento por tamanho (`EIBCALEN`) | API versioning |

---

## 15. HANDLE CONDITION e RESP/EIBRESP — tratamento de erros CICS

### Estilo legado: HANDLE CONDITION (obsoleto mas presente)

```cobol
           EXEC CICS HANDLE CONDITION
               NOTFND(9100-NAO-ENCONTRADO)
               DUPREC(9200-DUPLICADO)
               ERROR(9900-ERRO-GERAL)
           END-EXEC
```

**Significado:** Registra **handlers globais** para condições de erro — quando a condição ocorre, o controle salta para o parágrafo indicado. É equivalente a `try/catch` global ou `on error goto` (Visual Basic).

**Problema:** É um mecanismo de `GOTO` disfarçado — o fluxo de controle fica difícil de rastrear. Código moderno deve evitar esse padrão.

### Estilo moderno: RESP / RESP2

```cobol
           EXEC CICS READ
               FILE('ARQCLI')
               INTO(WS-REG-CLIENTE)
               RIDFLD(WS-CPF-BUSCA)
               RESP(WS-RESP)
               RESP2(WS-RESP2)
           END-EXEC

           EVALUATE WS-RESP
               WHEN DFHRESP(NORMAL)
                   PERFORM 3000-PROCESSAR-CLIENTE
               WHEN DFHRESP(NOTFND)
                   MOVE 'CLIENTE NAO ENCONTRADO' TO WS-MSG
                   PERFORM 8000-EXIBIR-ERRO
               WHEN DFHRESP(DISABLED)
                   MOVE 'ARQUIVO INDISPONIVEL' TO WS-MSG
                   PERFORM 9000-ERRO-GRAVE
               WHEN OTHER
                   MOVE WS-RESP TO WS-MSG-RESP
                   PERFORM 9900-ERRO-INESPERADO
           END-EVALUATE
```

### EIBRESP — via EIB (Execute Interface Block)

```cobol
           IF EIBRESP = DFHRESP(NORMAL)
               CONTINUE
           ELSE
               PERFORM 9000-TRATAR-ERRO
           END-IF
```

O EIB é um bloco de contexto que o CICS disponibiliza automaticamente para cada programa. Campos relevantes:

| Campo EIB | Significado | Equivalente moderno |
|---|---|---|
| `EIBCALEN` | Tamanho do COMMAREA recebido | `Content-Length` |
| `EIBTRNID` | ID da transação | `X-Request-ID` |
| `EIBRESP` | Código de resposta do último comando | HTTP status code |
| `EIBRESP2` | Código de detalhe do erro | Error detail / sub-code |
| `EIBDATE` | Data (0CYYDDD packed) | `Date` header |
| `EIBTIME` | Hora (0HHMMSS packed) | `Timestamp` |
| `EIBTASKN` | Número da task | `Thread ID` / `Request ID` |

### Códigos DFHRESP comuns

| DFHRESP | Valor | Significado | Equivalente moderno |
|---|---|---|---|
| `NORMAL` | 0 | Sucesso | 200 OK |
| `NOTFND` | 13 | Registro não encontrado | 404 Not Found |
| `DUPREC` | 14 | Chave duplicada | 409 Conflict |
| `INVREQ` | 16 | Requisição inválida | 400 Bad Request |
| `LENGERR` | 22 | Erro de tamanho | 413 Payload Too Large |
| `DISABLED` | 84 | Recurso desabilitado | 503 Service Unavailable |
| `NOTAUTH` | 70 | Não autorizado | 403 Forbidden |

### Mapeamento para exceções modernas

```python
# Equivalente moderno do padrão RESP/EVALUATE
try:
    cliente = repository.find_by_id(cpf)
except NotFoundException:
    return ErrorResponse("Cliente não encontrado", 404)
except DuplicateKeyException:
    return ErrorResponse("CPF já cadastrado", 409)
except ServiceUnavailableException:
    return ErrorResponse("Serviço indisponível", 503)
```

---

## 16. Identificação da lógica de negócio em programas CICS

Um programa CICS típico mistura 3 tipos de lógica:

### a) Lógica de apresentação (UI)

```cobol
      * >>> APRESENTAÇÃO — separar para camada de view <<<
           MOVE WS-NOME TO NOMEO
           MOVE WS-SALDO TO SALDOO
           EXEC CICS SEND MAP('MAPCLI') MAPSET('MSCLI') ... END-EXEC
           EXEC CICS RECEIVE MAP('MAPCLI') MAPSET('MSCLI') ... END-EXEC
```

**Indicadores:**
- `SEND MAP` / `RECEIVE MAP`
- MOVEs de/para campos do mapa (sufixo `I`/`O`)
- Formatação de dados para exibição
- Validação de formato de campos de tela

### b) Lógica de controle de transação (infraestrutura)

```cobol
      * >>> CONTROLE — separar para camada de infraestrutura <<<
           EXEC CICS READ FILE('ARQCLI') ... END-EXEC
           EXEC CICS REWRITE FILE('ARQCLI') ... END-EXEC
           EXEC CICS SYNCPOINT END-EXEC
           EXEC CICS RETURN TRANSID('TRNS') COMMAREA(...) END-EXEC
           EXEC CICS LINK PROGRAM('PGMLOG') ... END-EXEC
```

**Indicadores:**
- Todos os `EXEC CICS` de I/O (`READ`, `WRITE`, `REWRITE`, `DELETE`)
- `SYNCPOINT` (commit/rollback)
- `RETURN` / `LINK` / `XCTL`
- `START` / `CANCEL` (agendamento de transações)
- Tratamento de `RESP` / `EIBRESP`

### c) Lógica de negócio (o que importa preservar)

```cobol
      * >>> NEGÓCIO — preservar integralmente <<<
           COMPUTE WS-JUROS = WS-SALDO * WS-TAXA / 100
           IF WS-SALDO < 0
               MOVE 'INADIMPLENTE' TO WS-STATUS
           END-IF
           IF WS-IDADE >= 60
               COMPUTE WS-DESCONTO = WS-VALOR * 0.15
           END-IF
           EVALUATE WS-TIPO-CONTA
               WHEN 'CC'  PERFORM 5000-CALCULAR-CC
               WHEN 'CP'  PERFORM 5100-CALCULAR-CP
               WHEN 'CI'  PERFORM 5200-CALCULAR-CI
           END-EVALUATE
```

**Indicadores:**
- `COMPUTE`, `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE` com campos de negócio
- `IF`/`EVALUATE` com condições de negócio (não com `RESP` de CICS)
- Cálculos de juros, taxas, descontos, impostos
- Validações de regras (limites, elegibilidade, status)
- Transformações de dados de negócio

### Estratégia de separação

```
Programa CICS original
├── Apresentação (SEND/RECEIVE MAP)     → Frontend / API Controller
├── Controle (EXEC CICS I/O, RETURN)    → Repository / Infrastructure
└── Negócio (COMPUTE, regras, cálculos) → Domain Service / Use Case
```

### Checklist para extração de regras de negócio

1. **Ignorar** parágrafos `0000-*` (main), `1000-INICIALIZAR`, `9000-*` (erros) — são boilerplate
2. **Identificar** parágrafos com `COMPUTE`, `IF` de negócio, `EVALUATE` de negócio
3. **Rastrear** quais campos da WORKING-STORAGE esses parágrafos usam (são os inputs/outputs da regra)
4. **Verificar** se há dependências de dados de I/O (READ antes de cálculo) — separar o acesso a dados do cálculo
5. **Documentar** cada regra como: `DADO [inputs] QUANDO [condição] ENTÃO [resultado]`
6. **Validar** com exemplos: simular valores de entrada e conferir saída

---

## Checklist geral de modernização

### Análise do programa

- [ ] Identificar todas as 4 DIVISIONS e extrair metadados
- [ ] Listar todos os `COPY` statements (dependências externas)
- [ ] Mapear todos os `PIC` clauses para tipos modernos
- [ ] Identificar `REDEFINES` e documentar variantes
- [ ] Listar todas as operações de I/O (FILE, CICS READ/WRITE, DB2)
- [ ] Identificar o padrão de controle de fluxo (batch sequencial vs pseudoconversacional)

### Extração de lógica

- [ ] Separar lógica de apresentação (SEND/RECEIVE MAP)
- [ ] Separar lógica de infraestrutura (EXEC CICS, FILE I/O)
- [ ] Isolar regras de negócio (COMPUTE, IF/EVALUATE de negócio)
- [ ] Documentar cada regra no formato DADO/QUANDO/ENTÃO
- [ ] Identificar tratamento de erros e mapear para exceções modernas

### Mapeamento de dados

- [ ] Converter layouts de copybook para DTOs/schemas
- [ ] Tratar campos com `V` implícito (decimal ponto fixo)
- [ ] Resolver `REDEFINES` como tipos discriminados
- [ ] Identificar truncamentos em `MOVE` e adicionar validações
- [ ] Mapear FILE STATUS e DFHRESP para exceções/status codes

### Mapeamento de controle

- [ ] Mapear COMMAREA para request/response DTOs
- [ ] Mapear LINK para chamadas de serviço síncronas
- [ ] Mapear XCTL para navegação/redirect
- [ ] Mapear pseudoconversacional para stateless request-response
- [ ] Mapear PERFORM VARYING/UNTIL para loops modernos

---

## Definition of Done (Modernização COBOL)

- [ ] Todas as regras de negócio extraídas e documentadas
- [ ] Mapeamento completo de tipos PIC para tipos modernos
- [ ] REDEFINES resolvidos como tipos discriminados
- [ ] Dependências externas (COPY, LINK, XCTL) mapeadas
- [ ] Lógica de apresentação separada da lógica de negócio
- [ ] Truncamentos silenciosos identificados e tratados
- [ ] Códigos de erro (FILE STATUS, DFHRESP) mapeados
- [ ] COMMAREA convertido em contratos de API