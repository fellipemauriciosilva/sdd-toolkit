---
name: db2-sql-cobol
description: "Skill para leitura, interpretação e modernização de SQL embutido DB2 em programas COBOL e utilitários batch no ambiente mainframe IBM z/OS. Use quando a tarefa envolver análise de blocos EXEC SQL, host variables, cursores, SQLCA, DCLGEN, planos/packages BIND e utilitários DB2 (DSNUTILB)."
---

# SQL Embutido DB2 em COBOL — Leitura, Interpretação e Modernização

## Objetivo desta skill

Capacitar o agente a **ler, interpretar semanticamente e modernizar** código SQL embutido DB2 z/OS presente em programas COBOL batch e online, incluindo utilitários batch executados via JCL. O foco é entender como o programa interage com o banco de dados, extrair a lógica de acesso a dados e traduzir para plataformas modernas — não apenas converter sintaxe SQL.

---

## Contexto do ambiente

| Componente | Tecnologia |
|---|---|
| Plataforma | IBM z/OS |
| Banco de dados | IBM DB2 for z/OS |
| Linguagem host | COBOL 85 / Enterprise COBOL |
| Pré-compilador | DB2 Precompiler (DSNHPC) / DB2 Coprocessor |
| Controle de acesso | BIND PLAN / BIND PACKAGE |
| Catálogo de metadados | SYSIBM.SYSTABLES, SYSIBM.SYSCOLUMNS, etc. |
| Utilitários batch | DSNUTILB (LOAD, UNLOAD, REORG, COPY, RUNSTATS, etc.) |
| Gerador de declarações | DCLGEN (Declarations Generator) |
| Comunicação de erros | SQLCA (SQL Communication Area) |

---

# PARTE 1 — SQL EMBUTIDO EM COBOL

---

## 1. Blocos EXEC SQL ... END-EXEC — identificação e extração

Todo acesso a DB2 dentro de um programa COBOL é delimitado por `EXEC SQL ... END-EXEC`. Esses blocos podem aparecer em duas seções do programa:

### Na DATA DIVISION (declarações)

```cobol
       WORKING-STORAGE SECTION.

      * Include da SQLCA para tratamento de erros
           EXEC SQL
               INCLUDE SQLCA
           END-EXEC.

      * Include do DCLGEN — layout da tabela CLIENTES
           EXEC SQL
               INCLUDE DCLCLIENTE
           END-EXEC.

      * Declaração de cursor
           EXEC SQL
               DECLARE CSR-CLIENTES CURSOR FOR
               SELECT CLI_CPF, CLI_NOME, CLI_SALDO
               FROM CLIENTES
               WHERE CLI_STATUS = :WS-STATUS
               ORDER BY CLI_NOME
           END-EXEC.
```

### Na PROCEDURE DIVISION (comandos DML e controle)

```cobol
       PROCEDURE DIVISION.

           EXEC SQL
               SELECT CLI_NOME, CLI_SALDO
               INTO :WS-NOME, :WS-SALDO
               FROM CLIENTES
               WHERE CLI_CPF = :WS-CPF
           END-EXEC

           EXEC SQL
               INSERT INTO LOG_ACESSO
               (LOG_DATA, LOG_USUARIO, LOG_ACAO)
               VALUES
               (CURRENT TIMESTAMP, :WS-USUARIO, :WS-ACAO)
           END-EXEC

           EXEC SQL
               UPDATE CLIENTES
               SET CLI_SALDO = :WS-NOVO-SALDO
               WHERE CLI_CPF = :WS-CPF
           END-EXEC

           EXEC SQL
               DELETE FROM TEMP_PROCESSADOS
               WHERE PROC_DATA < CURRENT DATE - 30 DAYS
           END-EXEC
```

### Como o agente deve extrair blocos EXEC SQL

1. **Varrer o programa** de cima para baixo, identificando todo par `EXEC SQL` / `END-EXEC`
2. **Classificar cada bloco** por tipo:
   - `INCLUDE` → dependência (SQLCA, DCLGEN)
   - `DECLARE CURSOR` → definição de cursor (iteração)
   - `SELECT INTO` → leitura de registro único
   - `INSERT`, `UPDATE`, `DELETE` → modificação de dados
   - `OPEN`, `FETCH`, `CLOSE` → operações de cursor
   - `COMMIT`, `ROLLBACK` → controle transacional
3. **Mapear host variables** (variáveis prefixadas com `:`) usadas em cada bloco
4. **Registrar a posição** de cada bloco em relação ao fluxo do programa (em qual parágrafo/seção aparece)

### Pré-compilação — o que acontece antes da execução

O pré-compilador DB2 (`DSNHPC`) ou o coprocessor processa os blocos `EXEC SQL` e:
1. **Substitui** cada `EXEC SQL` por `CALL` statements para módulos de interface DB2
2. **Extrai** os SQL statements e os armazena em um DBRM (Database Request Module)
3. **O DBRM** é usado no `BIND` para criar o plano ou package de acesso

O programa COBOL compilado **não contém SQL** — contém chamadas ao runtime DB2. O SQL real está no plano/package.

---

## 2. Host variables — a ponte entre COBOL e SQL

Host variables são variáveis COBOL referenciadas dentro de blocos `EXEC SQL` com o prefixo `:`. São o mecanismo de passagem de dados entre o programa e o banco.

### Declaração e uso

```cobol
       WORKING-STORAGE SECTION.
       01 WS-PARAMETROS.
           05 WS-CPF           PIC X(11).
           05 WS-NOME          PIC X(40).
           05 WS-SALDO         PIC S9(13)V99 COMP-3.
           05 WS-STATUS        PIC X(1).
           05 WS-DATA-NASC     PIC X(10).

       PROCEDURE DIVISION.
           EXEC SQL
               SELECT CLI_NOME, CLI_SALDO
               INTO :WS-NOME, :WS-SALDO
               FROM CLIENTES
               WHERE CLI_CPF = :WS-CPF
           END-EXEC
```

### Direção do fluxo de dados

| Contexto SQL | Direção | Papel da host variable |
|---|---|---|
| `INTO :var` | DB2 → COBOL | Recebe valor retornado pelo SELECT |
| `WHERE col = :var` | COBOL → DB2 | Fornece parâmetro de filtro |
| `VALUES (:var)` | COBOL → DB2 | Fornece valor para INSERT |
| `SET col = :var` | COBOL → DB2 | Fornece valor para UPDATE |

### Mapeamento para queries modernas

| SQL embutido com host variables | Equivalente moderno |
|---|---|
| `:WS-CPF` no `WHERE` | Parâmetro de query / bind parameter (`?`, `$1`, `:cpf`) |
| `INTO :WS-NOME, :WS-SALDO` | Mapeamento de resultado (DTO, `ResultSet.getString()`, ORM field) |
| Host variable em `VALUES` | Parâmetro de INSERT / `repository.save(entity)` |

### Indicator variables — tratamento de NULLs

```cobol
       01 WS-DADOS-CLIENTE.
           05 WS-EMAIL          PIC X(50).
           05 WS-EMAIL-IND      PIC S9(4) COMP.

           EXEC SQL
               SELECT CLI_EMAIL
               INTO :WS-EMAIL :WS-EMAIL-IND
               FROM CLIENTES
               WHERE CLI_CPF = :WS-CPF
           END-EXEC

           IF WS-EMAIL-IND < 0
               MOVE 'SEM EMAIL' TO WS-MSG
           ELSE
               MOVE WS-EMAIL TO WS-MSG
           END-IF
```

**Regras de indicator variables:**

| Valor do indicator | Significado |
|---|---|
| `0` | Valor não é NULL, dado recebido normalmente |
| `-1` | Valor é NULL no banco |
| `> 0` | Valor foi truncado; o indicator contém o tamanho original |

**Na modernização:** Indicator variables mapeiam diretamente para `Optional<T>`, `null`, `None` ou tipos nullable. Toda lógica que testa `IND < 0` equivale a `if (value == null)`.

### Tabela de mapeamento PIC COBOL → tipo DB2 → tipo moderno

| PIC COBOL | Tipo DB2 | Tipo Java | Tipo C# | Tipo Python |
|---|---|---|---|---|
| `PIC X(n)` | `CHAR(n)` / `VARCHAR(n)` | `String` | `string` | `str` |
| `PIC S9(n) COMP` | `INTEGER` / `SMALLINT` | `int` / `long` | `int` / `long` | `int` |
| `PIC S9(n)V9(m) COMP-3` | `DECIMAL(n+m, m)` | `BigDecimal` | `decimal` | `Decimal` |
| `PIC X(10)` (data) | `DATE` | `LocalDate` | `DateOnly` | `date` |
| `PIC X(26)` (timestamp) | `TIMESTAMP` | `LocalDateTime` | `DateTime` | `datetime` |

---

## 3. SQLCA — comunicação de erros entre DB2 e COBOL

A SQLCA (SQL Communication Area) é uma estrutura incluída via `EXEC SQL INCLUDE SQLCA END-EXEC` que o DB2 preenche após **cada** comando SQL. É o mecanismo central de tratamento de erros.

### Estrutura da SQLCA

```cobol
       01 SQLCA.
           05 SQLCAID      PIC X(8).      *> Sempre 'SQLCA   '
           05 SQLCABC      PIC S9(9) COMP.*> Tamanho da SQLCA (136)
           05 SQLCODE      PIC S9(9) COMP.*> Código de retorno principal
           05 SQLERRML     PIC S9(4) COMP.*> Tamanho da mensagem
           05 SQLERRMC     PIC X(70).     *> Texto da mensagem de erro
           05 SQLERRP      PIC X(8).      *> Produto (DSN para DB2)
           05 SQLERRD      OCCURS 6       *> Array de 6 inteiros
                           PIC S9(9) COMP.
           05 SQLWARN.
               10 SQLWARN0  PIC X(1).     *> 'W' se algum warning
               10 SQLWARN1  PIC X(1).     *> Truncamento de string
               10 SQLWARN2  PIC X(1).     *> NULLs eliminados em função
               10 SQLWARN3  PIC X(1).     *> Colunas > host variables
               10 SQLWARN4  PIC X(1).     *> UPDATE/DELETE sem WHERE
               10 SQLWARN5  PIC X(1).     *> Reservado
               10 SQLWARN6  PIC X(1).     *> Ajuste de data inválida
               10 SQLWARN7  PIC X(1).     *> Reservado
           05 SQLEXT       PIC X(8).      *> Extensão
```

### SQLCODE — o campo mais importante

| SQLCODE | Significado | Ação típica no programa | Equivalente moderno |
|---|---|---|---|
| `0` | Sucesso | Continua processamento normal | 200 OK / resultado válido |
| `+100` | Não encontrou dados (SELECT) ou fim de cursor (FETCH) | Seta flag de fim, encerra loop | `null` / `Optional.empty()` / `StopIteration` |
| `-803` | Violação de chave única (INSERT/UPDATE) | Trata duplicidade | `DuplicateKeyException` / 409 Conflict |
| `-805` | Package/plano não encontrado (BIND) | Erro de deploy — programa não foi bindado | Deployment error |
| `-811` | SELECT INTO retornou mais de uma linha | Erro de lógica — query deveria retornar 1 | `NonUniqueResultException` |
| `-818` | Timestamp mismatch (DBRM ≠ plano) | Recompilar + rebind | Build/deploy version mismatch |
| `-904` | Recurso indisponível (tablespace, lock) | Retry ou abend | `ServiceUnavailableException` / 503 |
| `-911` | Deadlock ou timeout | Rollback e retry | `DeadlockException` / retry logic |
| `-913` | Deadlock (recurso não disponível) | Rollback e retry | `LockTimeoutException` |
| `-922` | Autorização insuficiente | Abend — sem permissão | `AccessDeniedException` / 403 |
| `-180` / `-181` | Valor de data/hora inválido | Validação de input | `DateTimeParseException` |
| `-302` | Valor muito grande para host variable | Truncamento | `DataTruncation` |
| `-530` | Violação de foreign key (INSERT/UPDATE) | Integridade referencial | `ForeignKeyViolationException` |
| `-532` | Violação de foreign key (DELETE) | Restrição de exclusão | `ForeignKeyViolationException` |

### SQLERRD — informações adicionais

| Campo | Significado |
|---|---|
| `SQLERRD(1)` | Reservado |
| `SQLERRD(2)` | Reservado |
| `SQLERRD(3)` | Número de linhas afetadas pelo último INSERT/UPDATE/DELETE |
| `SQLERRD(4)` | Estimativa de custo (em timerons) — usado pelo otimizador |
| `SQLERRD(5)` | Posição do erro na string SQL (para SQL dinâmico) |
| `SQLERRD(6)` | Reservado |

**`SQLERRD(3)` é especialmente importante:** Após um `INSERT`, `UPDATE` ou `DELETE`, contém o número de linhas afetadas. Programas frequentemente verificam esse valor para validar que a operação afetou exatamente o número esperado de registros.

### Padrão típico de tratamento de erros

```cobol
       2000-CONSULTAR-CLIENTE.
           EXEC SQL
               SELECT CLI_NOME, CLI_SALDO
               INTO :WS-NOME, :WS-SALDO
               FROM CLIENTES
               WHERE CLI_CPF = :WS-CPF
           END-EXEC

           EVALUATE SQLCODE
               WHEN 0
                   PERFORM 3000-PROCESSAR-DADOS
               WHEN +100
                   MOVE 'CLIENTE NAO ENCONTRADO' TO WS-MSG-ERRO
                   SET WS-NOT-FOUND TO TRUE
               WHEN -803
                   MOVE 'CPF DUPLICADO' TO WS-MSG-ERRO
                   SET WS-DUPLICADO TO TRUE
               WHEN -911
                   MOVE 'DEADLOCK - TENTANDO NOVAMENTE' TO WS-MSG
                   PERFORM 2000-CONSULTAR-CLIENTE
               WHEN OTHER
                   MOVE SQLCODE TO WS-SQLCODE-DISPLAY
                   STRING 'ERRO DB2: ' WS-SQLCODE-DISPLAY
                       ' - ' SQLERRMC
                       DELIMITED BY SIZE
                       INTO WS-MSG-ERRO
                   PERFORM 9000-ERRO-GRAVE
           END-EVALUATE
```

### Como interpretar o tratamento de erros para modernização

1. **Mapear cada `EVALUATE SQLCODE`** ou `IF SQLCODE` para um bloco `try/catch` ou pattern matching
2. **SQLCODE 0** → happy path (sem exceção)
3. **SQLCODE +100** → resultado vazio — decidir se é `Optional.empty()`, `null` ou exceção de negócio
4. **SQLCODEs negativos** → exceções tipadas, cada uma com tratamento específico
5. **`WHEN OTHER`** → catch genérico (`SQLException`, `DataAccessException`)
6. **Atenção a retries** em -911/-913 — indicam que o programa tem lógica de resiliência que deve ser preservada

### SQLWARN — warnings que podem afetar a migração

```cobol
           IF SQLWARN0 = 'W'
               IF SQLWARN1 = 'W'
                   MOVE 'DADOS TRUNCADOS' TO WS-MSG
               END-IF
           END-IF
```

| Warning | Significado | Impacto na migração |
|---|---|---|
| `SQLWARN1 = 'W'` | String truncada na atribuição | Campos no banco podem ser menores que o esperado |
| `SQLWARN2 = 'W'` | NULLs eliminados em função agregada | `SUM`, `AVG` ignoram NULLs — pode haver diferença com ANSI |
| `SQLWARN4 = 'W'` | UPDATE/DELETE sem WHERE | Query perigosa — afeta todas as linhas |
| `SQLWARN6 = 'W'` | Ajuste de data aritmética inválida | Datas calculadas foram ajustadas silenciosamente |

---

## 4. Cursores — iteração sobre conjuntos de resultados

Cursores são o mecanismo para processar **múltiplas linhas** retornadas por um SELECT. Seguem um ciclo de vida fixo: DECLARE → OPEN → FETCH (loop) → CLOSE.

### Ciclo completo de um cursor

```cobol
       WORKING-STORAGE SECTION.

      * Declaração do cursor
           EXEC SQL
               DECLARE CSR-PEDIDOS CURSOR FOR
               SELECT PED_NUMERO, PED_DATA, PED_VALOR
               FROM PEDIDOS
               WHERE PED_CLIENTE = :WS-CPF-CLIENTE
                 AND PED_STATUS = 'A'
               ORDER BY PED_DATA DESC
           END-EXEC.

       01 WS-PEDIDO.
           05 WS-PED-NUMERO    PIC S9(9) COMP.
           05 WS-PED-DATA      PIC X(10).
           05 WS-PED-VALOR     PIC S9(11)V99 COMP-3.
       01 WS-FLAGS.
           05 WS-FIM-CURSOR    PIC X(1) VALUE 'N'.
               88 WS-CURSOR-EOF    VALUE 'S'.
               88 WS-CURSOR-OPEN   VALUE 'N'.

       PROCEDURE DIVISION.

       2000-LISTAR-PEDIDOS.
      * Abrir o cursor (executa o SELECT)
           EXEC SQL
               OPEN CSR-PEDIDOS
           END-EXEC

           IF SQLCODE NOT = 0
               PERFORM 9000-ERRO-OPEN
               GO TO 2000-EXIT
           END-IF

      * Loop de FETCH
           SET WS-CURSOR-OPEN TO TRUE
           PERFORM 2100-FETCH-PEDIDO
               UNTIL WS-CURSOR-EOF

      * Fechar o cursor
           EXEC SQL
               CLOSE CSR-PEDIDOS
           END-EXEC

           .
       2000-EXIT.
           EXIT.

       2100-FETCH-PEDIDO.
           EXEC SQL
               FETCH CSR-PEDIDOS
               INTO :WS-PED-NUMERO,
                    :WS-PED-DATA,
                    :WS-PED-VALOR
           END-EXEC

           EVALUATE SQLCODE
               WHEN 0
                   PERFORM 3000-PROCESSAR-PEDIDO
               WHEN +100
                   SET WS-CURSOR-EOF TO TRUE
               WHEN OTHER
                   PERFORM 9000-ERRO-FETCH
                   SET WS-CURSOR-EOF TO TRUE
           END-EVALUATE
           .
```

### Mapeamento de cursores para modernização

| Operação de cursor | Java (JDBC) | C# (ADO.NET) | Python (DB-API) | ORM |
|---|---|---|---|---|
| `DECLARE CURSOR FOR SELECT ...` | `PreparedStatement` | `SqlCommand` | `cursor.execute()` | Query definition |
| `OPEN cursor` | `executeQuery()` | `ExecuteReader()` | `execute()` | `findAll()` / `stream()` |
| `FETCH INTO :vars` | `resultSet.next()` + `getXxx()` | `reader.Read()` + `GetXxx()` | `fetchone()` | Iteração sobre resultados |
| `CLOSE cursor` | `resultSet.close()` | `reader.Close()` | `cursor.close()` | Auto-close |
| Loop FETCH+PROCESS | `while (rs.next()) { ... }` | `while (reader.Read()) { ... }` | `for row in cursor:` | `.forEach()` / `for entity in` |

### Tradução completa para código moderno

```python
# Equivalente Python do cursor COBOL acima
pedidos = db.execute(
    """SELECT ped_numero, ped_data, ped_valor
       FROM pedidos
       WHERE ped_cliente = %s AND ped_status = 'A'
       ORDER BY ped_data DESC""",
    (cpf_cliente,)
)

for numero, data, valor in pedidos:
    processar_pedido(numero, data, valor)
```

```java
// Equivalente Java
List<Pedido> pedidos = repository.findByClienteAndStatus(cpfCliente, "A",
    Sort.by(Sort.Direction.DESC, "data"));

for (Pedido pedido : pedidos) {
    processarPedido(pedido);
}
```

### Tipos especiais de cursor

#### Cursor WITH HOLD — sobrevive ao COMMIT

```cobol
           EXEC SQL
               DECLARE CSR-BATCH CURSOR WITH HOLD FOR
               SELECT ...
           END-EXEC
```

**Significado:** O cursor permanece aberto após um `COMMIT`. Sem `WITH HOLD`, um `COMMIT` fecha todos os cursores abertos. Usado em processamento batch que faz commits periódicos (a cada N registros) para liberar locks.

**Na modernização:** Implica que o programa processa grandes volumes e faz commits intermediários. Traduzir para batch processing com chunk/commit-interval (como Spring Batch).

#### Cursor FOR UPDATE — permite atualização posicional

```cobol
           EXEC SQL
               DECLARE CSR-ATUALIZA CURSOR FOR
               SELECT CLI_SALDO
               FROM CLIENTES
               WHERE CLI_STATUS = 'A'
               FOR UPDATE OF CLI_SALDO
           END-EXEC

           EXEC SQL
               FETCH CSR-ATUALIZA INTO :WS-SALDO
           END-EXEC

           COMPUTE WS-NOVO-SALDO = WS-SALDO * 1.05

           EXEC SQL
               UPDATE CLIENTES
               SET CLI_SALDO = :WS-NOVO-SALDO
               WHERE CURRENT OF CSR-ATUALIZA
           END-EXEC
```

**Significado:** O `FOR UPDATE` trava cada linha lida. O `WHERE CURRENT OF` atualiza a linha na posição corrente do cursor sem precisar repetir a cláusula WHERE.

**Na modernização:** Traduzir para `SELECT ... FOR UPDATE` + `UPDATE ... WHERE pk = :pk` ou uso de optimistic locking (`@Version`). O padrão `WHERE CURRENT OF` não existe em ORMs — usar chave primária explícita.

#### Cursor SENSITIVE / INSENSITIVE

```cobol
           EXEC SQL
               DECLARE CSR-SNAP INSENSITIVE SCROLL CURSOR FOR
               SELECT ...
           END-EXEC
```

- `INSENSITIVE` → O cursor vê um snapshot dos dados no momento do OPEN (mudanças por outras transações não são visíveis)
- `SENSITIVE` → O cursor vê mudanças feitas por outros (default)

**Na modernização:** `INSENSITIVE` mapeia para isolation level `REPEATABLE READ` ou snapshot isolation.

---

## 5. DCLGEN — mapeamento de schema de tabela para COBOL

DCLGEN (Declarations Generator) é um utilitário DB2 que gera automaticamente:
1. Uma declaração SQL da tabela (`EXEC SQL DECLARE TABLE`)
2. Uma estrutura COBOL correspondente (host variable structure)

### Exemplo de DCLGEN gerado

```cobol
      *****************************************************
      * DCLGEN TABLE(CLIENTES)                            *
      *        LIBRARY(PROJDB2.DCLGEN(DCLCLI))            *
      *        LANGUAGE(COBOL)                            *
      *        QUOTE                                      *
      * ... IS THE DCLGEN COMMAND THAT MADE THE FOLLOWING *
      * ... COBOL DECLARATION.                            *
      *****************************************************

           EXEC SQL DECLARE CLIENTES TABLE
           ( CLI_CPF             CHAR(11) NOT NULL,
             CLI_NOME            VARCHAR(40) NOT NULL,
             CLI_DATA_NASC       DATE,
             CLI_SALDO           DECIMAL(15,2) NOT NULL WITH DEFAULT,
             CLI_STATUS          CHAR(1) NOT NULL WITH DEFAULT,
             CLI_EMAIL           VARCHAR(50),
             CLI_DT_CADASTRO     TIMESTAMP NOT NULL WITH DEFAULT,
             CLI_COD_AGENCIA     SMALLINT
           ) IN DBCLI.TSCLI
           END-EXEC.

      *****************************************************
      * COBOL DECLARATION FOR TABLE CLIENTES              *
      *****************************************************
       01 DCLCLIENTES.
           10 CLI-CPF          PIC X(11).
           10 CLI-NOME.
               49 CLI-NOME-LEN PIC S9(4) COMP.
               49 CLI-NOME-TEXT PIC X(40).
           10 CLI-DATA-NASC    PIC X(10).
           10 CLI-SALDO        PIC S9(13)V9(2) COMP-3.
           10 CLI-STATUS       PIC X(1).
           10 CLI-EMAIL.
               49 CLI-EMAIL-LEN PIC S9(4) COMP.
               49 CLI-EMAIL-TEXT PIC X(50).
           10 CLI-DT-CADASTRO  PIC X(26).
           10 CLI-COD-AGENCIA  PIC S9(4) COMP.

      *****************************************************
      * INDICATOR VARIABLE STRUCTURE                      *
      *****************************************************
       01 ICLCLIENTES.
           10 INDNULL          PIC S9(4) COMP
                               OCCURS 8 TIMES.
```

### Como usar DCLGEN para inferir o schema real

1. **A declaração `DECLARE TABLE`** mostra a DDL real da tabela — tipos, NOT NULL, defaults
2. **A estrutura COBOL** mostra o mapeamento host variable esperado
3. **VARCHAR em COBOL** é representado como estrutura de 2 campos:
   - `LEN` (PIC S9(4) COMP) → tamanho efetivo do conteúdo
   - `TEXT` (PIC X(n)) → conteúdo em si
4. **O array de indicators** (`ICLCLIENTES`) permite testar NULL para cada coluna

### Tabela de inferência de schema a partir do DCLGEN

| Tipo DB2 no DECLARE | PIC COBOL gerado | Tipo moderno inferido | Nullable? |
|---|---|---|---|
| `CHAR(n) NOT NULL` | `PIC X(n)` | `string` (fixed length) | Não |
| `VARCHAR(n)` | `49 LEN PIC S9(4) COMP` + `49 TEXT PIC X(n)` | `string` (variable) | Sim (se não NOT NULL) |
| `DECIMAL(p,s) NOT NULL` | `PIC S9(p-s)V9(s) COMP-3` | `decimal(p,s)` / `BigDecimal` | Não |
| `INTEGER` | `PIC S9(9) COMP` | `int` | Depende |
| `SMALLINT` | `PIC S9(4) COMP` | `short` / `int` | Depende |
| `DATE` | `PIC X(10)` | `LocalDate` / `DateOnly` / `date` | Depende |
| `TIMESTAMP` | `PIC X(26)` | `LocalDateTime` / `DateTime` / `datetime` | Depende |
| `WITH DEFAULT` | — | Campo tem default no banco | — |

### Regras para o agente

- **Se o DCLGEN está disponível**, usá-lo como **fonte primária** para inferir o schema — é gerado diretamente do catálogo DB2
- **Se não está disponível**, inferir o schema a partir dos SELECTs, INSERTs e host variables no programa
- **`WITH DEFAULT`** significa que o DB2 atribui um valor padrão (0 para numéricos, espaços para CHAR, data/hora corrente para TIMESTAMP) se a coluna não for especificada no INSERT
- **`NOT NULL`** sem `WITH DEFAULT` = o INSERT obrigatoriamente deve fornecer o valor
- **VARCHAR** no DCLGEN sempre gera a estrutura de 2 níveis (49) — na modernização, tratar como `String` simples

---

## 6. Diferenças entre SQL DB2 z/OS e SQL ANSI

O DB2 z/OS implementa SQL com extensões e comportamentos específicos que podem causar problemas na migração para bancos ANSI (PostgreSQL, MySQL, SQL Server, etc.).

### Tipos de dados

| DB2 z/OS | ANSI / Banco alvo | Diferença / Risco |
|---|---|---|
| `DECIMAL(p,s)` | `NUMERIC(p,s)` / `DECIMAL(p,s)` | Compatível na maioria dos bancos |
| `CHAR(n) FOR SBCS DATA` | `CHAR(n)` | SBCS/DBCS é específico do DB2 — remover qualificador |
| `VARCHAR(n) FOR MIXED DATA` | `VARCHAR(n)` | MIXED DATA permite EBCDIC + DBCS — converter encoding |
| `TIMESTAMP` (26 chars) | `TIMESTAMP` | DB2 tem 6 dígitos de microsecond por padrão; outros bancos variam |
| `DATE` | `DATE` | Formato DB2: `YYYY-MM-DD` (ISO) — compatível |
| `TIME` | `TIME` | Formato DB2: `HH.MM.SS` (com ponto) — ANSI usa `:` |
| `GRAPHIC(n)` / `VARGRAPHIC(n)` | `NCHAR(n)` / `NVARCHAR(n)` | Tipo DBCS do DB2 — mapear para Unicode |
| `ROWID` | `UUID` / `SERIAL` | Tipo gerado pelo DB2 — substituir por equivalente |
| `BLOB` / `CLOB` | `BYTEA` / `TEXT` (PostgreSQL) | Compatível em conceito, API diferente |

### Funções e expressões

| DB2 z/OS | ANSI / PostgreSQL | Observação |
|---|---|---|
| `CURRENT DATE` | `CURRENT_DATE` | DB2 sem underscore |
| `CURRENT TIME` | `CURRENT_TIME` | DB2 sem underscore |
| `CURRENT TIMESTAMP` | `CURRENT_TIMESTAMP` / `NOW()` | DB2 sem underscore |
| `VALUE(a, b)` | `COALESCE(a, b)` | `VALUE` é alias DB2 para COALESCE — não existe em ANSI |
| `STRIP(col)` | `TRIM(col)` | DB2 usa STRIP; ANSI usa TRIM |
| `SUBSTR(col, start, len)` | `SUBSTRING(col FROM start FOR len)` | DB2 usa sintaxe de função; ANSI pode usar `FROM ... FOR` |
| `DIGITS(col)` | `CAST(col AS CHAR)` | Converte numérico para string de dígitos — específico DB2 |
| `HEX(col)` | `ENCODE(col, 'hex')` | Representação hexadecimal — sintaxe varia |
| `CHAR(date, ISO)` | `TO_CHAR(date, 'YYYY-MM-DD')` | Formatação de data — sintaxe totalmente diferente |
| `DATE(expr)` | `CAST(expr AS DATE)` | Conversão para data |
| `DAYS(date)` | Não existe diretamente | Retorna número de dias desde 01/01/0001 — calcular com funções |
| `JULIAN_DAY(date)` | Não existe diretamente | Dia Juliano — usar cálculo equivalente |
| `col CONCAT col2` | `col \|\| col2` | DB2 aceita CONCAT como operador infixo |
| `RAISE_ERROR(sqlstate, msg)` | `RAISE EXCEPTION` (PostgreSQL) | Sintaxe diferente por banco |

### Comportamentos de NULL

| Comportamento DB2 | ANSI | Risco |
|---|---|---|
| `''` (string vazia) ≠ NULL | Idem em PostgreSQL, Oracle trata `''` como NULL | Oracle → DB2 pode introduzir NULLs inesperados |
| `ORDER BY` coloca NULLs no final (ASC) | Varia por banco — PostgreSQL coloca no final, Oracle no início | Usar `NULLS FIRST`/`NULLS LAST` explicitamente |
| `CONCAT` com NULL → NULL | Idem em ANSI | Mas programas DB2 podem depender do `VALUE()` para evitar |
| `COUNT(*)` inclui NULLs; `COUNT(col)` exclui | Padrão ANSI — compatível | — |
| Comparação `col = NULL` → always false | Idem ANSI (`IS NULL` correto) | Mas programas legados podem conter esse bug |

### Sintaxe de JOIN

```sql
-- DB2 z/OS aceita ambas as formas:

-- Estilo implícito (old-style, DB2 original)
SELECT A.COL1, B.COL2
FROM TABELA_A A, TABELA_B B
WHERE A.CHAVE = B.CHAVE

-- Estilo ANSI (suportado em DB2 V8+)
SELECT A.COL1, B.COL2
FROM TABELA_A A
INNER JOIN TABELA_B B ON A.CHAVE = B.CHAVE
```

**Na modernização:** Sempre converter JOINs implícitos (estilo comma) para JOINs explícitos ANSI. Programas legados frequentemente usam o estilo implícito, que dificulta a identificação de OUTER JOINs e pode mascarar cross-joins acidentais.

### Paginação

```sql
-- DB2 z/OS (V12+)
SELECT * FROM CLIENTES
ORDER BY CLI_NOME
FETCH FIRST 10 ROWS ONLY
OFFSET 20 ROWS

-- DB2 z/OS (versões antigas — sem OFFSET)
SELECT * FROM CLIENTES
ORDER BY CLI_NOME
FETCH FIRST 10 ROWS ONLY
-- Paginação feita via ROW_NUMBER() ou cursor + FETCH NEXT
```

**Na modernização:** `FETCH FIRST n ROWS ONLY` é compatível com muitos bancos. Se o programa usa cursor para simular paginação, converter para `LIMIT/OFFSET` ou `FETCH FIRST/OFFSET`.

---

## 7. Planos e packages (BIND) — impacto na portabilidade

### O que é BIND

O `BIND` é o processo que transforma SQL estático (extraído pelo pré-compilador no DBRM) em um plano de acesso otimizado armazenado no catálogo DB2.

```
Fonte COBOL → Precompile → DBRM + COBOL modificado → BIND → Package/Plan
                                                              (no catálogo DB2)
```

### Plano vs Package

| Conceito | Escopo | Uso típico |
|---|---|---|
| **Package** | Um programa (DBRM) | Unidade de compilação — 1 package por programa |
| **Plan** | Coleção de packages | Agrupa packages — 1 plan pode conter vários packages |

### O que o BIND define

```jcl
//BIND     EXEC PGM=IKJEFT01
//SYSTSPRT DD   SYSOUT=*
//SYSTSIN  DD   *
  DSN SYSTEM(DB2P)
  BIND PACKAGE(COLPROD) -
       MEMBER(PGMCLI01) -
       LIBRARY('PROJ.DBRMLIB') -
       OWNER(USRPROD) -
       QUALIFIER(SCHMPROD) -
       ISOLATION(CS) -
       VALIDATE(BIND) -
       EXPLAIN(YES) -
       ACTION(REPLACE)
  END
/*
```

| Parâmetro BIND | Significado | Impacto na modernização |
|---|---|---|
| `PACKAGE(collection)` | Coleção onde o package será armazenado | Equivale a schema/namespace |
| `MEMBER(dbrm)` | Nome do DBRM (programa fonte) | Vincula SQL ao programa compilado |
| `OWNER(userid)` | Dono do package — define permissões de execução | Service account / connection user |
| `QUALIFIER(schema)` | Schema default para tabelas não qualificadas | `search_path` (PostgreSQL) / default schema |
| `ISOLATION(CS\|RR\|UR\|RS)` | Nível de isolamento transacional | `READ COMMITTED`, `SERIALIZABLE`, etc. |
| `VALIDATE(BIND\|RUN)` | Quando validar referências a objetos | Compile-time vs runtime checks |
| `EXPLAIN(YES)` | Gera plano de acesso no catálogo | Equivalente a `EXPLAIN ANALYZE` |
| `ACTION(REPLACE)` | Substitui package existente | Redeploy |

### Níveis de isolamento

| DB2 | ANSI | Comportamento |
|---|---|---|
| `UR` (Uncommitted Read) | `READ UNCOMMITTED` | Lê dados não commitados (dirty reads) |
| `CS` (Cursor Stability) | `READ COMMITTED` | Lê apenas dados commitados; lock na linha corrente do cursor |
| `RS` (Read Stability) | `REPEATABLE READ` | Lock em todas as linhas lidas — sem phantom na releitura |
| `RR` (Repeatable Read) | `SERIALIZABLE` | Lock em toda a faixa — sem phantom reads |

### Impacto na portabilidade

1. **SQL estático vs dinâmico:** SQL em `EXEC SQL` de COBOL é **estático** — o plano de acesso é decidido no BIND, não em runtime. Em bancos modernos, o plano é calculado em runtime (prepare/execute). Queries que performam bem no DB2 por causa do plano de BIND podem ter comportamento diferente sem pré-otimização.

2. **QUALIFIER define o schema:** Se as queries no programa não qualificam tabelas (`SELECT FROM CLIENTES` em vez de `SELECT FROM SCHMPROD.CLIENTES`), o schema é definido pelo BIND. Na migração, é preciso qualificar as tabelas ou configurar o schema padrão da conexão.

3. **ISOLATION afeta locks:** Mudar de `CS` para `READ COMMITTED` é direto, mas se o programa depende de `RR` (SERIALIZABLE), reduzir o isolamento pode introduzir anomalias.

4. **VALIDATE(RUN):** Se o BIND usa `VALIDATE(RUN)`, tabelas podem não existir no momento do BIND — são validadas só na execução. Isso pode mascarar erros de referência.

---

## 8. Queries problemáticas para modernização

### Table scans (falta de índice)

```cobol
           EXEC SQL
               SELECT COUNT(*)
               INTO :WS-TOTAL
               FROM PEDIDOS
               WHERE YEAR(PED_DATA) = :WS-ANO
           END-EXEC
```

**Problema:** `YEAR(PED_DATA)` aplica uma função sobre a coluna, impedindo o uso de índice em `PED_DATA`. No DB2 z/OS com um plano bindado, o DBA pode ter criado um índice de expressão ou ajustado o acesso. Em outro banco, isso resulta em table scan.

**Solução moderna:**
```sql
WHERE PED_DATA >= :ano_inicio AND PED_DATA < :ano_fim
```

### Lógica procedural em SQL (cursores com atualização linha a linha)

```cobol
      * Anti-pattern: atualizar registro por registro via cursor
           EXEC SQL OPEN CSR-ATUALIZA END-EXEC
           PERFORM UNTIL SQLCODE = +100
               EXEC SQL FETCH CSR-ATUALIZA
                   INTO :WS-SALDO END-EXEC
               IF SQLCODE = 0
                   COMPUTE WS-NOVO-SALDO = WS-SALDO * 1.05
                   EXEC SQL UPDATE CLIENTES
                       SET CLI_SALDO = :WS-NOVO-SALDO
                       WHERE CURRENT OF CSR-ATUALIZA
                   END-EXEC
               END-IF
           END-PERFORM
           EXEC SQL CLOSE CSR-ATUALIZA END-EXEC
```

**Problema:** Atualização RBAR (Row By Agonizing Row). No DB2 z/OS pode ser aceitável pelo volume e otimização do plano, mas em bancos modernos será lento.

**Solução moderna:**
```sql
UPDATE CLIENTES SET CLI_SALDO = CLI_SALDO * 1.05 WHERE CLI_STATUS = 'A';
```

### Dependência de ordenação implícita

```cobol
           EXEC SQL
               DECLARE CSR-SEQ CURSOR FOR
               SELECT CLI_CPF, CLI_NOME
               FROM CLIENTES
               WHERE CLI_STATUS = 'A'
           END-EXEC
```

**Problema:** Sem `ORDER BY`, a ordenação depende do plano de acesso do DB2 (que pode usar o índice de chave primária, dando uma ordem previsível). Em outro banco, a ordem é **indeterminada**. Se o programa depende da ordem dos resultados, pode apresentar comportamento diferente.

**Solução:** Sempre adicionar `ORDER BY` explícito quando a ordem importa.

### Uso de registros especiais DB2

```cobol
           EXEC SQL
               SET :WS-TIMESTAMP = CURRENT TIMESTAMP
           END-EXEC

           EXEC SQL
               INSERT INTO LOG (LOG_USER, LOG_TIME)
               VALUES (USER, CURRENT TIMESTAMP)
           END-EXEC
```

| Registro especial DB2 | Equivalente ANSI | Equivalente PostgreSQL |
|---|---|---|
| `CURRENT DATE` | `CURRENT_DATE` | `CURRENT_DATE` |
| `CURRENT TIME` | `CURRENT_TIME` | `CURRENT_TIME` |
| `CURRENT TIMESTAMP` | `CURRENT_TIMESTAMP` | `NOW()` / `CURRENT_TIMESTAMP` |
| `USER` | `CURRENT_USER` | `CURRENT_USER` |
| `CURRENT SQLID` | Não existe | `current_schema` (PostgreSQL) |
| `CURRENT SERVER` | Não existe | `inet_server_addr()` |
| `CURRENT PACKAGESET` | Não existe | Sem equivalente |

### Uso de temporary tables específicas do DB2

```cobol
           EXEC SQL
               DECLARE GLOBAL TEMPORARY TABLE SESSION.TEMP_CALC
               (CALC_ID INTEGER, CALC_VALOR DECIMAL(15,2))
               ON COMMIT PRESERVE ROWS
           END-EXEC
```

**Na modernização:** Mapeado para `CREATE TEMPORARY TABLE` (PostgreSQL), `#temp` (SQL Server) ou tabela temporária de sessão no banco alvo. A cláusula `ON COMMIT PRESERVE ROWS` mantém os dados entre commits — verificar se o banco alvo suporta ou se precisa de workaround.

---

## 9. Controle transacional em programas COBOL + DB2

### COMMIT e ROLLBACK explícitos

```cobol
       5000-ATUALIZAR-LOTE.
           MOVE 0 TO WS-CONTADOR-COMMIT

           EXEC SQL OPEN CSR-BATCH END-EXEC

           PERFORM UNTIL WS-CURSOR-EOF
               EXEC SQL FETCH CSR-BATCH
                   INTO :WS-REGISTRO END-EXEC

               IF SQLCODE = 0
                   PERFORM 5100-PROCESSAR-REGISTRO
                   ADD 1 TO WS-CONTADOR-COMMIT

                   IF WS-CONTADOR-COMMIT >= 1000
                       EXEC SQL COMMIT END-EXEC
                       MOVE 0 TO WS-CONTADOR-COMMIT
                   END-IF
               ELSE IF SQLCODE = +100
                   SET WS-CURSOR-EOF TO TRUE
               ELSE
                   EXEC SQL ROLLBACK END-EXEC
                   PERFORM 9000-ERRO-BATCH
                   SET WS-CURSOR-EOF TO TRUE
               END-IF
           END-PERFORM

           EXEC SQL COMMIT END-EXEC
           EXEC SQL CLOSE CSR-BATCH END-EXEC
           .
```

### Padrões transacionais comuns

| Padrão | Descrição | Equivalente moderno |
|---|---|---|
| Commit por registro | `COMMIT` após cada operação | Auto-commit / tx per request |
| Commit por lote | `COMMIT` a cada N registros | Chunk-based processing (Spring Batch) |
| Commit no final | Um `COMMIT` ao final de todo processamento | Transação longa (arriscado) |
| Rollback em erro | `ROLLBACK` + abend/return-code | Exception → rollback (tx management) |
| Savepoint | `SAVEPOINT` + `ROLLBACK TO SAVEPOINT` | Nested transactions / savepoints |

### Em CICS — controle via SYNCPOINT

```cobol
           EXEC CICS SYNCPOINT END-EXEC          *> COMMIT
           EXEC CICS SYNCPOINT ROLLBACK END-EXEC  *> ROLLBACK
```

**Importante:** Em CICS, `EXEC SQL COMMIT/ROLLBACK` **não é permitido**. O controle transacional é feito via `SYNCPOINT` do CICS, que coordena tanto DB2 quanto outros recursos (VSAM RLS, MQ).

---

# PARTE 2 — UTILITÁRIOS BATCH DB2 (DSNUTILB)

---

## 10. Execução de utilitários DB2 via JCL

Utilitários DB2 são executados através do programa `DSNUTILB` em jobs JCL. Eles operam diretamente em tablespaces, tabelas e índices para manutenção e movimentação de dados.

### Estrutura padrão de um job de utilitário DB2

```jcl
//UTILDB2  JOB (CONTA),'DBA-MANUT',CLASS=A,MSGCLASS=X,
//             NOTIFY=&SYSUID
//*------------------------------------------------------------
//* UTILITÁRIO DB2 — RUNSTATS + REORG
//*------------------------------------------------------------
//STEP010  EXEC PGM=DSNUTILB,
//             PARM='DB2P,UTILID01'
//STEPLIB  DD   DSN=DB2.SDSNLOAD,DISP=SHR
//SYSPRINT DD   SYSOUT=*
//SYSUDUMP DD   SYSOUT=*
//SYSIN    DD   *
  RUNSTATS TABLESPACE DBCLI.TSCLI
           TABLE(CLIENTES)
           INDEX(ALL)
           SHRLEVEL CHANGE
           REPORT YES
/*
```

**Elementos chave:**
- `PGM=DSNUTILB` → programa executor de utilitários DB2
- `PARM='subsistema,utilid'` → identifica o subsistema DB2 e o ID do utilitário (para controle e restart)
- `SYSIN` → contém os comandos de controle do utilitário

### Utilitários DB2 e seus significados

#### LOAD — carga de dados em tabela

```jcl
//SYSIN    DD   *
  LOAD DATA INDDN SYSREC LOG YES
       RESUME NO REPLACE
       INTO TABLE CLIENTES
       (CLI_CPF    POSITION(1:11)   CHAR(11),
        CLI_NOME   POSITION(12:51)  CHAR(40),
        CLI_SALDO  POSITION(52:66)  PACKED DECIMAL,
        CLI_STATUS POSITION(67:67)  CHAR(1))
/*
//SYSREC   DD   DSN=STAGE.CLIENTES.CARGA,DISP=SHR
//SYSUT1   DD   DSN=&&SORTOUT,DISP=(NEW,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(50,10))
//SORTOUT  DD   DSN=&&SORTOUT2,DISP=(NEW,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(50,10))
//SYSERR   DD   DSN=&&SYSERR,DISP=(NEW,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(5,2))
//SYSMAP   DD   DSN=&&SYSMAP,DISP=(NEW,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(5,2))
//SYSDISC  DD   SYSOUT=*
```

| Opção LOAD | Significado | Impacto |
|---|---|---|
| `REPLACE` | Apaga todos os dados existentes antes de carregar | Carga destrutiva — equivale a `TRUNCATE` + `INSERT` |
| `RESUME YES` | Adiciona aos dados existentes (append) | Carga incremental — equivale a `INSERT` em massa |
| `RESUME NO` | Requer tabela vazia (sem REPLACE = erro se tiver dados) | Carga em tabela nova |
| `LOG YES` | Gera log para recovery | Mais lento, mas recuperável |
| `LOG NO` | Não gera log — mais rápido, mas sem recovery | Requer backup (COPY) após |
| `ENFORCE CONSTRAINTS` | Verifica foreign keys durante a carga | Garante integridade referencial |
| `INDDN SYSREC` | DDname do dataset de entrada de dados | Fonte dos dados a carregar |

**Inferência de volume:** Se o LOAD usa `SPACE=(CYL,(500,100))` para SYSREC e datasets de sort, a tabela contém **grande volume de dados** (centenas de milhares a milhões de registros).

**Equivalente moderno:** `COPY FROM` (PostgreSQL), `BULK INSERT` (SQL Server), `LOAD DATA INFILE` (MySQL), ETL pipeline.

#### UNLOAD — exportação de dados de tabela

```jcl
//SYSIN    DD   *
  UNLOAD TABLESPACE DBCLI.TSCLI
         FROM TABLE CLIENTES
         HEADER NONE
         (CLI_CPF    CHAR(11),
          CLI_NOME   CHAR(40),
          CLI_SALDO  DECIMAL EXTERNAL,
          CLI_STATUS CHAR(1))
/*
//SYSREC   DD   DSN=EXPORT.CLIENTES.D&LYYMMDD,
//              DISP=(NEW,CATLG,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(100,20),RLSE),
//              DCB=(RECFM=FB,LRECL=100,BLKSIZE=0)
```

**Significado:** Extrai dados da tabela para um dataset sequencial. O output é posicional (flat file) com layout definido pela cláusula de colunas.

**Inferências:**
- **Se o dataset de saída contém data** (`D&LYYMMDD`) → é uma exportação diária/periódica
- **Se o SPACE é grande** → alto volume de dados
- **`DECIMAL EXTERNAL`** → exporta decimal como texto legível (em vez de packed)

**Equivalente moderno:** `COPY TO` (PostgreSQL), `SELECT INTO OUTFILE` (MySQL), export para CSV/Parquet, `pg_dump --data-only`.

#### REORG — reorganização de tablespace

```jcl
//SYSIN    DD   *
  REORG TABLESPACE DBCLI.TSCLI
        UNLOAD CONTINUE
        LOG YES
        SORTDATA YES
        SORTKEYS YES
        STATISTICS TABLE(ALL) INDEX(ALL)
/*
//SYSUT1   DD   DSN=&&UT1,DISP=(NEW,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(200,50))
```

**Significado:** Reorganiza fisicamente os dados no tablespace — desfragmenta, reordena por chave de clustering, reconstrói índices e atualiza estatísticas.

**Inferências de criticidade:**
- **REORG frequente** → tabela com muito INSERT/DELETE/UPDATE, fragmentação alta
- **SPACE grande para SYSUT1** → tablespace grande, dados críticos
- **`STATISTICS TABLE(ALL)`** → atualiza estatísticas do otimizador após a reorganização
- **Tablespace com REORG programado** → tabela de produção com SLA de performance

**Equivalente moderno:** `VACUUM FULL` + `REINDEX` (PostgreSQL), `ALTER INDEX REBUILD` (SQL Server), `OPTIMIZE TABLE` (MySQL).

#### COPY — backup de tablespace

```jcl
//SYSIN    DD   *
  COPY TABLESPACE DBCLI.TSCLI
       FULL YES
       SHRLEVEL REFERENCE
       DSNUM ALL
/*
//SYSCOPY  DD   DSN=BKUP.DBCLI.TSCLI.D&LYYMMDD,
//              DISP=(NEW,CATLG,DELETE),
//              UNIT=TAPE
```

**Significado:** Cria uma cópia de backup (image copy) do tablespace. Pode ser full ou incremental.

| Opção COPY | Significado |
|---|---|
| `FULL YES` | Backup completo de todo o tablespace |
| `FULL NO` | Backup incremental (apenas páginas alteradas desde o último full) |
| `SHRLEVEL REFERENCE` | Tablespace é colocado em read-only durante o backup |
| `SHRLEVEL CHANGE` | Backup online — tablespace permanece acessível para write |
| `DSNUM ALL` | Copia todas as partições (para tablespaces particionados) |

**Inferências de criticidade:**
- **COPY diário** (`D&LYYMMDD` no dataset) → dados críticos com RPO baixo
- **`UNIT=TAPE`** → backup em fita — retenção de longo prazo
- **`SHRLEVEL REFERENCE`** → aceita janela de indisponibilidade para backup consistente
- **`SHRLEVEL CHANGE`** → não aceita downtime — sistema 24/7

**Equivalente moderno:** `pg_dump` / `pg_basebackup` (PostgreSQL), backup de banco, snapshot de storage.

#### RUNSTATS — atualização de estatísticas

```jcl
//SYSIN    DD   *
  RUNSTATS TABLESPACE DBCLI.TSCLI
           TABLE(CLIENTES)
           INDEX(ALL)
           SHRLEVEL CHANGE
           REPORT YES
           UPDATE ALL
/*
```

**Significado:** Coleta estatísticas de distribuição de dados (cardinalidade, distribuição de valores, clustering) para que o otimizador DB2 escolha planos de acesso eficientes.

**Inferências:**
- **RUNSTATS após LOAD ou REORG** → prática padrão de DBA
- **RUNSTATS agendado** → tabela com dados voláteis que precisam de reotimização frequente
- **Sem RUNSTATS** → planos de acesso podem estar usando estatísticas defasadas

**Equivalente moderno:** `ANALYZE` (PostgreSQL), `UPDATE STATISTICS` (SQL Server), `ANALYZE TABLE` (MySQL).

#### CHECK DATA — verificação de integridade

```jcl
//SYSIN    DD   *
  CHECK DATA TABLESPACE DBCLI.TSCLI
        FOR EXCEPTION IN CLIENTES
        USE ERRCLIENTES
/*
//SYSERR   DD   DSN=ERRCHECK.CLIENTES,DISP=(NEW,CATLG)
```

**Significado:** Verifica a integridade referencial dos dados — identifica registros que violam foreign keys, check constraints e índices inconsistentes. Registros com problemas são copiados para a tabela de exceção.

**Equivalente moderno:** Queries de validação de integridade, health checks de banco.

---

## 11. Inferência de volume e criticidade dos dados

A análise dos utilitários usados em jobs JCL revela características operacionais da tabela que não estão documentadas no código COBOL:

### Matriz de inferência

| Evidência no JCL | Inferência |
|---|---|
| `LOAD REPLACE` diário com alto volume | Tabela reconstruída diariamente — provavelmente staging/intermediária |
| `LOAD RESUME YES` periódico | Tabela com crescimento contínuo (log, histórico, transações) |
| `UNLOAD` diário para fita/GDG | Exportação para downstream systems — tabela é fonte de dados |
| `COPY FULL YES` diário | Dados críticos — RPO < 24h |
| `COPY SHRLEVEL CHANGE` | Sistema 24/7 — sem janela de downtime |
| `REORG` semanal | Tabela com alta volatilidade (muitos INSERTs/DELETEs) |
| `RUNSTATS` após cada LOAD | Volumes variáveis — otimizador precisa de estatísticas atuais |
| `CHECK DATA` periódico | Dados com relações de integridade críticas |
| `SPACE=(CYL,(500,100))` em datasets | Volume de dados alto — milhões de registros |
| `TIME=(2,0)` no JOB | Processamento pesado — até 2h de CPU |
| `REGION=0M` | Memória sem limite — processamento intensivo |

### Classificação de tabelas por criticidade

| Criticidade | Características dos utilitários |
|---|---|
| **Crítica** | COPY diário + REORG semanal + RUNSTATS frequente + LOAD com `LOG YES` |
| **Importante** | COPY semanal + REORG mensal + usado por múltiplos programas |
| **Operacional** | LOAD REPLACE diário + sem COPY independente (coberto por tablespace) |
| **Temporária** | LOAD REPLACE + sem COPY + sem REORG + tabelas com prefixo TEMP/WORK |

---

## Checklist geral de modernização — SQL DB2 em COBOL

### Análise do programa

- [ ] Identificar todos os blocos `EXEC SQL ... END-EXEC`
- [ ] Classificar cada bloco (INCLUDE, DECLARE, DML, cursor, transacional)
- [ ] Listar todas as host variables e mapear para tipos modernos
- [ ] Identificar indicator variables e mapear para tratamento de NULL

### Análise de acesso a dados

- [ ] Extrair todos os cursores e seu ciclo de vida (DECLARE/OPEN/FETCH/CLOSE)
- [ ] Identificar cursores `WITH HOLD` (batch com commit intermediário)
- [ ] Identificar cursores `FOR UPDATE` (lock pessimista)
- [ ] Detectar padrões RBAR (row-by-row) que podem ser convertidos em set operations

### Análise de erros

- [ ] Mapear todos os `EVALUATE SQLCODE` / `IF SQLCODE`
- [ ] Documentar tratamento para SQLCODE 0, +100 e cada negativo encontrado
- [ ] Identificar uso de SQLERRD(3) para validar linhas afetadas
- [ ] Identificar uso de SQLWARN para detectar truncamentos

### Compatibilidade SQL

- [ ] Listar funções DB2 específicas (VALUE, STRIP, DIGITS, CHAR, DAYS)
- [ ] Converter para equivalentes ANSI/banco alvo
- [ ] Converter JOINs implícitos para ANSI
- [ ] Adicionar `ORDER BY` explícito onde a ordem importa
- [ ] Substituir registros especiais (CURRENT DATE → CURRENT_DATE)
- [ ] Tratar diferenças de encoding (EBCDIC → UTF-8)

### Schema e metadados

- [ ] Localizar DCLGENs de todas as tabelas referenciadas
- [ ] Inferir schema completo a partir de DCLGEN + queries
- [ ] Documentar constraints (NOT NULL, defaults, foreign keys)
- [ ] Mapear tipos DB2 para tipos do banco alvo

### Planos e portabilidade

- [ ] Identificar parâmetros BIND relevantes (ISOLATION, QUALIFIER)
- [ ] Qualificar tabelas com schema explícito
- [ ] Documentar nível de isolamento requerido
- [ ] Identificar queries que dependem de plano otimizado

### Utilitários batch

- [ ] Listar todos os jobs com DSNUTILB
- [ ] Classificar utilitários usados (LOAD, UNLOAD, REORG, COPY, RUNSTATS)
- [ ] Inferir volume e criticidade de cada tabela
- [ ] Mapear LOAD/UNLOAD para processos ETL modernos
- [ ] Identificar janelas de manutenção e SLAs implícitos

### Transações

- [ ] Mapear padrão transacional (commit por registro/lote/fim)
- [ ] Identificar uso de SYNCPOINT em CICS
- [ ] Documentar lógica de retry (SQLCODE -911/-913)
- [ ] Tratar diferenças entre CICS SYNCPOINT e SQL COMMIT

---

## Definition of Done (Modernização SQL DB2 em COBOL)

- [ ] Todos os blocos EXEC SQL extraídos e documentados
- [ ] Host variables mapeadas para parâmetros/DTOs modernos
- [ ] Indicator variables convertidas para tratamento nullable
- [ ] Cursores traduzidos para queries modernas ou streams
- [ ] SQLCODE tratados e mapeados para exceções tipadas
- [ ] Funções DB2 convertidas para equivalentes do banco alvo
- [ ] JOINs convertidos para ANSI
- [ ] Schema inferido e documentado
- [ ] Utilitários batch mapeados para processos modernos
- [ ] Nível de isolamento e padrão transacional documentados
