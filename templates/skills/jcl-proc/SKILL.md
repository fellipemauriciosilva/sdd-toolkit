---
name: jcl-proc
description: Skill para leitura, interpretação e modernização de jobs JCL e Procedures (PROCs) em ambiente mainframe IBM z/OS. Use quando a tarefa envolver análise de JCL, extração de fluxos de execução, mapeamento de datasets, interpretação de dependências entre steps e planejamento de modernização para orquestradores modernos.
---

# JCL & PROCs — Leitura, Interpretação e Modernização

## Objetivo desta skill

Capacitar o agente a **ler, interpretar semanticamente e modernizar** jobs JCL (Job Control Language) e Procedures (PROCs) executados em ambiente mainframe IBM z/OS. O foco é reconstruir o fluxo de execução, entender dependências entre steps, mapear datasets para conceitos modernos e traduzir a orquestração para plataformas atuais.

---

## Contexto do ambiente

| Componente | Tecnologia |
|---|---|
| Plataforma | IBM z/OS |
| Linguagem de controle | JCL (Job Control Language) |
| Subsistema de execução | JES2 / JES3 (Job Entry Subsystem) |
| Bibliotecas de PROCs | PROCLIBs (PDS — Partitioned Data Set) |
| Datasets | Sequenciais, PDS, VSAM, GDG (Generation Data Group) |
| Programas executados | COBOL, PL/I, Assembler, utilitários IBM (SORT, IDCAMS, IEBGENER, DFSORT) |
| Schedulers | CA-7, TWS (Tivoli Workload Scheduler), Control-M |

---

# PARTE 1 — JCL (Job Control Language)

---

## 1. Estrutura de um job completo — reconstrução do fluxo de execução

Um job JCL é composto por statements que seguem uma hierarquia fixa. Cada statement começa na coluna 1 com `//` (exceto delimitadores de dados).

### Anatomia de um job

```jcl
//JOBCALC  JOB (CONTA,INFO),'CALC FOLHA',
//             CLASS=A,MSGCLASS=X,
//             MSGLEVEL=(1,1),NOTIFY=&SYSUID
//*------------------------------------------------------------
//* STEP 1 - EXTRAIR DADOS DE FUNCIONARIOS
//*------------------------------------------------------------
//STEP010  EXEC PGM=EXTFUNC
//ENTRADA  DD   DSN=PROD.RH.FUNCIONARIOS,DISP=SHR
//SAIDA    DD   DSN=&&TEMPFUNC,DISP=(NEW,PASS),
//              UNIT=SYSDA,SPACE=(CYL,(50,10),RLSE),
//              DCB=(RECFM=FB,LRECL=200,BLKSIZE=0)
//SYSPRINT DD   SYSOUT=*
//*------------------------------------------------------------
//* STEP 2 - CALCULAR FOLHA DE PAGAMENTO
//*------------------------------------------------------------
//STEP020  EXEC PGM=CALCFOLH,COND=(4,LT)
//FUNCION  DD   DSN=&&TEMPFUNC,DISP=(OLD,DELETE)
//TABELAS  DD   DSN=PROD.RH.TAB.INSS,DISP=SHR
//         DD   DSN=PROD.RH.TAB.IRRF,DISP=SHR
//RESULTADO DD  DSN=PROD.RH.FOLHA.D&LYYMMDD,
//              DISP=(NEW,CATLG,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(100,20),RLSE),
//              DCB=(RECFM=FB,LRECL=300,BLKSIZE=0)
//SYSPRINT DD   SYSOUT=*
//SYSOUT   DD   SYSOUT=*
//*------------------------------------------------------------
//* STEP 3 - GERAR RELATORIO
//*------------------------------------------------------------
//STEP030  EXEC PGM=RELFOLH,COND=(4,LT)
//FOLHA    DD   DSN=PROD.RH.FOLHA.D&LYYMMDD,DISP=SHR
//RELAT    DD   SYSOUT=A,DCB=(RECFM=FBA,LRECL=133)
//SYSPRINT DD   SYSOUT=*
//
```

### Fluxo de execução implícito

```
STEP010 (EXTFUNC) ──dados──▶ &&TEMPFUNC ──dados──▶ STEP020 (CALCFOLH) ──dados──▶ PROD.RH.FOLHA.D... ──dados──▶ STEP030 (RELFOLH)
```

**Regra fundamental:** Steps executam **sequencialmente**, de cima para baixo. Não há paralelismo dentro de um job. As dependências entre steps são **implícitas** — determinadas pelos datasets que um step cria e outro consome.

### Como reconstruir o fluxo

1. **Listar todos os steps** na ordem em que aparecem
2. **Para cada step**, identificar o programa executado (`EXEC PGM=`)
3. **Mapear datasets de saída** (DISP=NEW/MOD) de cada step
4. **Mapear datasets de entrada** (DISP=SHR/OLD) de cada step
5. **Conectar** saídas de um step com entradas de steps posteriores — essas são as dependências de dados
6. **Identificar datasets temporários** (`&&`) — existem apenas durante o job e representam dados intermediários

### Mapeamento moderno

| JCL | Orquestrador moderno |
|---|---|
| Job completo | DAG (Directed Acyclic Graph) em Airflow / Step Functions |
| Step (EXEC) | Task / State / Step |
| Sequência de steps | Dependência sequencial entre tasks |
| Dataset intermediário (`&&`) | Dado temporário entre tasks (S3, /tmp, message) |
| Dataset permanente | Tabela de banco, arquivo em storage (S3/GCS/Blob) |

---

## 2. JOB Statement — controle de execução e recursos

```jcl
//JOBNAME  JOB (accounting-info),'programmer-name',
//             CLASS=A,
//             MSGCLASS=X,
//             MSGLEVEL=(1,1),
//             NOTIFY=&SYSUID,
//             TIME=(1,30),
//             REGION=0M,
//             TYPRUN=SCAN,
//             RESTART=STEP020,
//             COND=((4,LT),(8,EQ,STEP010))
```

### Parâmetros do JOB statement

| Parâmetro | Significado | Equivalente moderno |
|---|---|---|
| `JOBNAME` (posição) | Identificador único do job (1-8 chars) | Job ID / Pipeline name |
| `(accounting-info)` | Informações de contabilização — centro de custo, projeto | Tags de billing / cost allocation |
| `'programmer-name'` | Nome do responsável (informativo) | Owner / maintainer |
| `CLASS=A` | Classe de execução — define fila de processamento e prioridade | Queue / priority tier |
| `MSGCLASS=X` | Classe de saída para mensagens do JES | Log level / log destination |
| `MSGLEVEL=(stmt,msg)` | Controle de verbosidade: `(1,1)` = máximo, `(0,0)` = mínimo | Log verbosity setting |
| `NOTIFY=&SYSUID` | Enviar notificação ao submeter — `&SYSUID` = usuário corrente | Notification / webhook callback |
| `TIME=(min,seg)` | Tempo máximo de CPU para o job inteiro | Timeout / deadline |
| `REGION=0M` | Memória máxima — `0M` = sem limite (usa toda disponível) | Memory limit / resource allocation |
| `TYPRUN=SCAN` | Apenas valida a sintaxe sem executar | Dry run / --plan |
| `TYPRUN=HOLD` | Submete mas não executa até ser liberado | Queued / paused state |
| `RESTART=stepname` | Reinicia execução a partir de um step específico | Retry from step / checkpoint |
| `COND` | Condição global de execução (ver seção 6) | Global guard / precondition |

### Variáveis simbólicas do sistema

| Variável | Significado | Exemplo de valor |
|---|---|---|
| `&SYSUID` | User ID do submitter | `USRPROD1` |
| `&LYYMMDD` | Data no formato AAMMDD | `260514` |
| `&LDATE` | Data no formato local | `05/14/26` |
| `&LTIME` | Hora no formato local | `14:30:00` |
| `&SYSDATE` | Data no formato MM/DD/YY | `05/14/26` |
| `&SYSJOBNAME` | Nome do job em execução | `JOBCALC` |

---

## 3. DD Statement — entradas e saídas de dados

O DD (Data Definition) statement é o **coração do JCL** — define **todos** os recursos de dados que um programa acessa. Cada DD associa um **nome lógico** (ddname) a um recurso físico (dataset, dispositivo, spool).

### Anatomia de um DD statement

```jcl
//ddname   DD   DSN=dataset.name,
//              DISP=(status,normal-disp,abnormal-disp),
//              UNIT=device,
//              SPACE=(unit,(primary,secondary,directory),RLSE),
//              DCB=(RECFM=xx,LRECL=nnn,BLKSIZE=nnn),
//              VOL=SER=volume
```

### Tipos de DD e mapeamento moderno

#### a) Dataset em disco (input ou output)

```jcl
//ENTRADA  DD   DSN=PROD.VENDAS.DIARIO,DISP=SHR
```
**Significado:** Arquivo existente, aberto para leitura compartilhada.
**Equivalente moderno:** `open("s3://bucket/vendas/diario.csv", "r")` ou query a uma tabela.

#### b) Dataset temporário

```jcl
//TEMPDATA DD   DSN=&&TEMP,DISP=(NEW,PASS),
//              UNIT=SYSDA,SPACE=(CYL,(10,5),RLSE)
```
**Significado:** Dataset que existe apenas durante o job. Criado no step atual, passado para steps seguintes, destruído ao final do job.
**Equivalente moderno:** Arquivo temporário, staging area, fila intermediária.

#### c) Saída para spool (SYSOUT)

```jcl
//SYSPRINT DD   SYSOUT=*
//RELAT    DD   SYSOUT=A,DCB=(RECFM=FBA,LRECL=133)
```
**Significado:** Direciona a saída para o spool do JES — é como um print/log.
- `SYSOUT=*` → usa a classe definida em `MSGCLASS` do JOB
- `SYSOUT=A` → classe específica (normalmente impressora)
**Equivalente moderno:** `stdout`, log file, print queue, log aggregator (CloudWatch, ELK).

#### d) Dados inline (SYSIN com *)

```jcl
//SYSIN    DD   *
  SORT FIELDS=(1,10,CH,A)
  INCLUDE COND=(15,2,CH,EQ,C'SP')
/*
```
**Significado:** Dados embutidos diretamente no JCL — terminam com `/*`. Usado para passar parâmetros de controle a utilitários.
**Equivalente moderno:** Heredoc, stdin, configuration block inline, command parameters.

#### e) Dados inline com delimitador customizado (DLM)

```jcl
//SQLSTMT  DD   *,DLM=$$
  SELECT COUNT(*) FROM CLIENTES
  WHERE STATUS = 'A';
$$
```
**Significado:** Mesmo que `DD *`, mas o delimitador é `$$` em vez de `/*`. Necessário quando o conteúdo inline contém `/*`.

#### f) Concatenação de datasets

```jcl
//TABELAS  DD   DSN=PROD.RH.TAB.INSS,DISP=SHR
//         DD   DSN=PROD.RH.TAB.IRRF,DISP=SHR
//         DD   DSN=PROD.RH.TAB.FGTS,DISP=SHR
```
**Significado:** Múltiplos datasets associados a um único ddname. O programa os lê como se fossem um único arquivo concatenado (fim de um = início do próximo).
**Equivalente moderno:** `cat file1 file2 file3 | program`, merge de múltiplos inputs, array de sources.

#### g) Dummy (sem dados)

```jcl
//LOGFILE  DD   DUMMY
```
**Significado:** O ddname existe mas não aponta para nenhum recurso real. Reads retornam EOF imediatamente, writes são descartados.
**Equivalente moderno:** `/dev/null`, mock de I/O, noop sink.

#### h) GDG — Generation Data Group

```jcl
//ATUAL    DD   DSN=PROD.VENDAS.GDG(0),DISP=SHR
//ANTERIOR DD   DSN=PROD.VENDAS.GDG(-1),DISP=SHR
//NOVO     DD   DSN=PROD.VENDAS.GDG(+1),DISP=(NEW,CATLG,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(50,10),RLSE),
//              DCB=(RECFM=FB,LRECL=200,BLKSIZE=0)
```
**Significado:** GDG é um grupo de datasets versionados. `(0)` = geração atual, `(-1)` = anterior, `(+1)` = nova geração a ser criada.
**Equivalente moderno:** Versionamento de arquivos, snapshots, tabelas particionadas por data, git versions.

### DDnames convencionais

| DDname | Significado típico | Equivalente moderno |
|---|---|---|
| `SYSIN` | Parâmetros de controle / input do utilitário | stdin / config input |
| `SYSPRINT` | Log/mensagens do programa | stdout / application log |
| `SYSOUT` | Saída adicional / relatórios | log file / report output |
| `SYSUT1` | Input de utilitários (IEBGENER, SORT) | source file |
| `SYSUT2` | Output de utilitários | target file |
| `SORTIN` | Input do SORT | unsorted data source |
| `SORTOUT` | Output do SORT | sorted data target |
| `SORTWK01-nn` | Work areas do SORT | temp space for sorting |
| `SYSUDUMP` / `SYSABEND` | Dump de memória em caso de abend | core dump / crash report |
| `STEPLIB` / `JOBLIB` | Biblioteca de load modules | classpath / PATH / LD_LIBRARY_PATH |

---

## 4. DISP — disposição do dataset (ciclo de vida dos dados)

O parâmetro `DISP` é um dos mais críticos do JCL — define o **estado inicial** do dataset e o que acontece com ele **ao final do step** (sucesso ou falha).

### Sintaxe

```
DISP=(status,normal-disp,abnormal-disp)
```

### Status inicial (primeiro subparâmetro)

| Status | Significado | Comportamento |
|---|---|---|
| `NEW` | Dataset não existe — será criado neste step | Aloca espaço e cria o dataset. Erro se já existir |
| `OLD` | Dataset existe — acesso exclusivo | Lock exclusivo — nenhum outro job pode acessá-lo simultaneamente |
| `SHR` | Dataset existe — acesso compartilhado | Múltiplos jobs podem ler simultaneamente |
| `MOD` | Se existe, posiciona no final (append); se não existe, cria como `NEW` | **Comportamento dual silencioso** — pode criar ou appendar sem aviso |

### Disposição normal (segundo subparâmetro — step termina com sucesso)

| Disposição | Significado |
|---|---|
| `DELETE` | Apaga o dataset após o step |
| `KEEP` | Mantém o dataset (sem catalogar) |
| `CATLG` | Mantém e registra no catálogo do sistema (equivalente a salvar permanentemente) |
| `PASS` | Passa o dataset para o próximo step do mesmo job (sem catalogar ainda) |
| `UNCATLG` | Remove do catálogo mas mantém no volume |

### Disposição anormal (terceiro subparâmetro — step falha/abend)

Mesmo conjunto de opções que a disposição normal. Define o que acontecer com o dataset **se o step falhar**.

### Cenários comuns e significado

```jcl
DISP=SHR                        → (SHR,KEEP,KEEP)   — leitura compartilhada, mantém
DISP=(NEW,CATLG,DELETE)          → cria, cataloga se OK, apaga se falhar
DISP=(NEW,PASS)                  → cria, passa para próximo step, apaga ao final do job se não for catalogado
DISP=(OLD,DELETE)                → acesso exclusivo, apaga após o step
DISP=(MOD,CATLG,DELETE)          → append se existe OU cria se não existe; cataloga se OK
DISP=(OLD,KEEP,KEEP)             → acesso exclusivo, mantém em qualquer caso
```

### Armadilhas do MOD

```jcl
//OUTPUT   DD   DSN=PROD.LOG.DIARIO,DISP=(MOD,CATLG,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(10,5),RLSE),
//              DCB=(RECFM=FB,LRECL=200,BLKSIZE=0)
```

**Perigo:** `MOD` tem dois comportamentos completamente diferentes:
1. **Dataset existe** → abre e posiciona no final (append). Os parâmetros `UNIT`, `SPACE`, `DCB` são **ignorados**
2. **Dataset não existe** → cria como `NEW` usando `UNIT`, `SPACE`, `DCB`

Na modernização, `MOD` deve ser traduzido para lógica explícita:
```python
if dataset_exists("PROD.LOG.DIARIO"):
    open("PROD.LOG.DIARIO", mode="a")  # append
else:
    create("PROD.LOG.DIARIO")          # create
```

### Ciclo de vida de um dataset temporário

```
STEP010: DISP=(NEW,PASS)     → cria &&TEMP, passa para frente
STEP020: DISP=(OLD,PASS)     → usa exclusivo, passa adiante
STEP030: DISP=(OLD,DELETE)   → usa exclusivo, apaga ao final
```

Se nenhum step posterior referenciar um dataset com `PASS`, ele é automaticamente **apagado ao final do job**.

---

## 5. Datasets temporários — prefixo && e ciclo de vida

```jcl
//TEMPFILE DD   DSN=&&EXTRACT,DISP=(NEW,PASS),
//              UNIT=SYSDA,SPACE=(CYL,(20,5),RLSE),
//              DCB=(RECFM=FB,LRECL=150,BLKSIZE=0)
```

### Características

| Aspecto | Comportamento |
|---|---|
| Nomenclatura | Prefixo `&&` (ex: `&&TEMP`, `&&EXTRACT`, `&&SORTED`) |
| Escopo | Existem **apenas durante o job** |
| Visibilidade | Apenas steps dentro do **mesmo job** podem acessá-los |
| Catalogação | **Nunca** são catalogados — não aparecem no catálogo do sistema |
| Destruição | Apagados automaticamente ao final do job (ou quando `DISP=DELETE`) |
| Persistência entre restarts | **Perdem-se** se o job for cancelado e resubmetido |

### Fluxo de vida

```
Step A: DISP=(NEW,PASS)     → dataset nasce
Step B: DISP=(OLD,PASS)     → dataset é usado e repassado
Step C: DISP=(OLD,DELETE)   → dataset é consumido e destruído
--- Fim do job ---          → qualquer &&TEMP não deletado é destruído
```

### Sem DSN explícito (dataset anônimo)

```jcl
//WORKFILE DD   UNIT=SYSDA,SPACE=(CYL,(5,1)),
//              DCB=(RECFM=FB,LRECL=80,BLKSIZE=0)
```
Dataset temporário **sem nome** — automaticamente recebe nome gerado pelo sistema. Só pode ser usado no step que o criou.

### Na modernização

| Dataset temporário | Equivalente moderno |
|---|---|
| `&&TEMP` com `PASS` | Arquivo temporário passado entre tasks (ex: S3 staging, /tmp) |
| `&&TEMP` sem `PASS` | Buffer local dentro de uma task |
| Dataset anônimo (sem DSN) | Variável/stream in-memory dentro de uma função |

**Regra:** Se um dataset temporário é consumido por um único step subsequente, na modernização pode ser eliminado — basta passar os dados diretamente (pipe, mensagem, parâmetro). Se é consumido por múltiplos steps, considerar um staging area ou cache intermediário.

---

## 6. COND e IF/THEN/ELSE — execução condicional

### COND no EXEC statement (lógica invertida — "skip if")

```jcl
//STEP020  EXEC PGM=CALCFOLH,COND=(4,LT)
```

**Semântica invertida (atenção!):** COND define quando o step **NÃO** deve executar. A condição testa os return codes de steps anteriores.

Formato: `COND=(code,operator)` ou `COND=(code,operator,stepname)`

**A leitura correta é:** "Pular este step SE `code operator return-code-anterior` for verdadeiro."

| COND | Leitura | Significado |
|---|---|---|
| `COND=(4,LT)` | Skip se `4 < RC` (algum RC anterior > 4) | Não executa se houve erro (RC > 4) |
| `COND=(0,NE)` | Skip se `0 ≠ RC` (algum RC anterior ≠ 0) | Só executa se todos os anteriores deram RC=0 |
| `COND=(8,EQ,STEP010)` | Skip se `8 = RC do STEP010` | Não executa se STEP010 retornou RC=8 |
| `COND=EVEN` | Executa **mesmo** se step anterior abendou | Execução incondicional (cleanup) |
| `COND=ONLY` | Executa **apenas** se step anterior abendou | Execução apenas em falha (error handler) |

### Múltiplas condições no COND

```jcl
//STEP030  EXEC PGM=RELAT,COND=((4,LT),(8,EQ,STEP010))
```
**Significado:** Skip se **qualquer** condição for verdadeira (OR lógico). No exemplo: pular se algum RC > 4 **OU** se STEP010 retornou exatamente 8.

### Tabela de return codes convencionais

| RC | Significado convencional | Equivalente moderno |
|---|---|---|
| `0` | Sucesso total | Exit code 0 / HTTP 200 |
| `4` | Sucesso com warnings | Partial success / HTTP 200 com warnings |
| `8` | Erro tratável | Controlled error / HTTP 4xx |
| `12` | Erro grave | Severe error / HTTP 500 |
| `16` | Erro fatal | Fatal / crash |

### IF/THEN/ELSE/ENDIF (JCL moderno — z/OS 1.4+)

```jcl
//         IF (STEP010.RC = 0) THEN
//STEP020  EXEC PGM=CALCFOLH
//ENTRADA  DD   DSN=&&TEMP,DISP=(OLD,DELETE)
//SAIDA    DD   DSN=PROD.RESULTADO,DISP=(NEW,CATLG,DELETE)
//         ENDIF
//
//         IF (STEP010.RC > 4) THEN
//STEPERR  EXEC PGM=NOTIFICA
//MSGERR   DD   *
  STEP010 FALHOU COM RC > 4
/*
//         ELSE
//STEP030  EXEC PGM=RELAT
//INPUT    DD   DSN=PROD.RESULTADO,DISP=SHR
//         ENDIF
```

### Operadores disponíveis no IF

| Operador | Significado |
|---|---|
| `=` / `EQ` | Igual |
| `<>` / `NE` | Diferente |
| `>` / `GT` | Maior que |
| `<` / `LT` | Menor que |
| `>=` / `GE` | Maior ou igual |
| `<=` / `LE` | Menor ou igual |
| `NOT` | Negação |
| `AND` / `&` | E lógico |
| `OR` / <code>&#124;</code> | OU lógico |

### Condições especiais no IF

```jcl
//         IF (STEP010.ABEND) THEN           → step abendou
//         IF (STEP010.ABENDCC = S0C7) THEN  → abend específico (data exception)
//         IF (STEP010.RUN) THEN             → step executou (não foi skipado)
//         IF (NOT STEP010.RUN) THEN         → step foi skipado
```

### Mapeamento para orquestradores modernos

```python
# JCL COND=(4,LT) traduzido para Airflow
@task
def step020():
    # Só executa se todos os anteriores tiveram RC <= 4
    ...

step010_task >> step020_task  # dependência sequencial

# JCL IF/THEN/ELSE traduzido para Step Functions
{
  "Type": "Choice",
  "Choices": [
    {
      "Variable": "$.step010.rc",
      "NumericEquals": 0,
      "Next": "Step020-Calculo"
    },
    {
      "Variable": "$.step010.rc",
      "NumericGreaterThan": 4,
      "Next": "StepErr-Notifica"
    }
  ],
  "Default": "Step030-Relat"
}
```

---

## 7. SYSOUT e SYSPRINT — logs e saídas

### SYSOUT (System Output)

```jcl
//SYSPRINT DD   SYSOUT=*
//RELAT    DD   SYSOUT=A
//LOG      DD   SYSOUT=X,HOLD=YES
```

| Parâmetro | Significado |
|---|---|
| `SYSOUT=*` | Classe padrão (definida em `MSGCLASS` do JOB) |
| `SYSOUT=A` | Classe A (tipicamente impressora) |
| `SYSOUT=X` | Classe X (tipicamente held output — fica no spool para consulta) |
| `HOLD=YES` | Mantém no spool — não imprime automaticamente |

### O que cada ddname de saída tipicamente contém

| DDname | Conteúdo típico | O que capturar na modernização |
|---|---|---|
| `SYSPRINT` | Mensagens do programa (log de execução) | Application log (INFO, WARN, ERROR) |
| `SYSOUT` | Saídas adicionais do programa | Log secundário ou output de dados |
| `SYSUDUMP` | Dump de memória em caso de abend | Stack trace / crash dump |
| `SYSABEND` | Dump formatado em caso de abend | Formatted crash report |
| `CEEDUMP` | Dump do Language Environment (LE) | Runtime exception details |
| `JESMSGLG` | Log de mensagens do JES | Orchestrator execution log |
| `JESJCL` | JCL expandido (com PROCs resolvidas) | Resolved pipeline definition |
| `JESYSMSG` | Mensagens do sistema (alocação, I/O) | Infrastructure/resource logs |

### Impacto na modernização

**Tudo que vai para SYSOUT/SYSPRINT é informação que alguém consome.** Ao modernizar:

1. **Identificar** quais saídas são logs operacionais (descartáveis) vs relatórios de negócio (precisam ser preservados)
2. **Logs operacionais** → substituir por logging estruturado (JSON logs, CloudWatch, ELK)
3. **Relatórios** → substituir por geração de arquivos (CSV, PDF) ou dashboards
4. **Dumps** → substituir por exception handling com stack traces e error reporting (Sentry, Datadog)

### SYSOUT com formulários e controle de carriage

```jcl
//RELAT    DD   SYSOUT=A,DCB=(RECFM=FBA,LRECL=133)
```

`RECFM=FBA` → Fixed Blocked com ASA control characters. O primeiro byte de cada registro é um **carriage control**:

| Byte 1 | Significado |
|---|---|
| ` ` (espaço) | Single space (nova linha normal) |
| `0` | Double space (pula uma linha) |
| `-` | Triple space |
| `1` | Form feed (nova página) |
| `+` | Overprint (sobrescrever linha anterior) |

Na modernização, esses caracteres de controle devem ser traduzidos para formatação de relatório (page breaks, line spacing) ou simplesmente removidos se o output for para log.

---

## 8. EXEC PGM= — identificação do programa executado

### Programas custom (aplicação)

```jcl
//STEP010  EXEC PGM=CALCFOLH
```
**Significado:** Executa o programa `CALCFOLH` — um load module compilado (tipicamente COBOL, PL/I ou Assembler) localizado em uma biblioteca de load modules (STEPLIB, JOBLIB ou LNKLST).

### Localização do programa

A busca pelo load module segue esta ordem:
1. `STEPLIB` DD (se presente no step)
2. `JOBLIB` DD (se presente no JOB)
3. `LNKLST` (concatenação de bibliotecas do sistema)

```jcl
//STEPLIB  DD   DSN=PROD.LOADLIB,DISP=SHR
//         DD   DSN=PROD.LOADLIB.UTILS,DISP=SHR
```

### Utilitários IBM comuns e o que fazem

| Programa | Função | Equivalente moderno |
|---|---|---|
| `IEFBR14` | Não faz nada (usado só para alocar/deletar datasets via DD) | No-op / `touch` / `rm` |
| `IEBGENER` | Copia dataset sequencial | `cp`, `aws s3 cp` |
| `IEBCOPY` | Copia members de PDS | `cp -r`, `rsync` |
| `IDCAMS` | Gerencia VSAM (define, delete, repro, listcat) | DDL / admin CLI para key-value stores |
| `SORT` / `DFSORT` / `SYNCSORT` | Ordena, filtra e transforma dados | `sort`, `awk`, SQL `ORDER BY`, ETL transform |
| `IKJEFT01` | TSO em batch (executa REXX, CLIST, comandos TSO) | Shell script / CLI executor |
| `IRXJCL` | Executa REXX em batch | Script executor |
| `DSNUTILB` | Utilitário DB2 (LOAD, UNLOAD, REORG, RUNSTATS) | `pg_dump`, `pg_restore`, `VACUUM ANALYZE` |
| `IKJEFT1B` | TSO em batch (sem prompt) | Script executor (non-interactive) |
| `HEWLKED` / `IEWL` | Linkage editor (linker) | `ld`, `gcc -o` |
| `IEBUPDTE` | Atualiza members de PDS | Patch / file update |
| `ADRDSSU` | Backup e restore de datasets | `tar`, `dump/restore` |

### SORT — o utilitário mais comum

```jcl
//STEP020  EXEC PGM=SORT
//SORTIN   DD   DSN=PROD.VENDAS.DIARIO,DISP=SHR
//SORTOUT  DD   DSN=&&SORTED,DISP=(NEW,PASS),
//              UNIT=SYSDA,SPACE=(CYL,(20,5),RLSE)
//SORTWK01 DD   UNIT=SYSDA,SPACE=(CYL,(10,5))
//SORTWK02 DD   UNIT=SYSDA,SPACE=(CYL,(10,5))
//SORTWK03 DD   UNIT=SYSDA,SPACE=(CYL,(10,5))
//SYSIN    DD   *
  SORT FIELDS=(1,10,CH,A,11,8,PD,D)
  INCLUDE COND=(25,2,CH,EQ,C'SP')
  SUM FIELDS=(35,8,PD)
  OUTREC FIELDS=(1,10,25,2,35,8)
/*
//SYSOUT   DD   SYSOUT=*
```

**Tradução dos parâmetros do SORT:**

| SORT Statement | Significado | Equivalente SQL |
|---|---|---|
| `SORT FIELDS=(1,10,CH,A,11,8,PD,D)` | Ordena por pos 1-10 (char asc), depois 11-18 (packed desc) | `ORDER BY col1 ASC, col2 DESC` |
| `INCLUDE COND=(25,2,CH,EQ,C'SP')` | Inclui apenas registros onde pos 25-26 = 'SP' | `WHERE estado = 'SP'` |
| `SUM FIELDS=(35,8,PD)` | Soma o campo packed nas pos 35-42 quando chaves iguais | `SUM(valor) GROUP BY ...` |
| `OUTREC FIELDS=(1,10,25,2,35,8)` | Seleciona campos para saída | `SELECT col1, col3, col5` |

### IDCAMS — gerenciamento de VSAM

```jcl
//STEP010  EXEC PGM=IDCAMS
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   *
  DELETE PROD.VSAM.CLIENTES CLUSTER PURGE
  SET MAXCC = 0
  DEFINE CLUSTER (                      -
      NAME(PROD.VSAM.CLIENTES)          -
      INDEXED                           -
      KEYS(11 0)                        -
      RECORDSIZE(200 200)               -
      SHAREOPTIONS(2 3)                 -
    ) DATA (                            -
      NAME(PROD.VSAM.CLIENTES.DATA)     -
      CYLINDERS(50 10)                  -
    ) INDEX (                           -
      NAME(PROD.VSAM.CLIENTES.INDEX)    -
      CYLINDERS(5 2)                    -
    )
/*
```

**Tradução:**
- `DELETE ... PURGE` → `DROP TABLE IF EXISTS clientes`
- `SET MAXCC = 0` → ignora erro do DELETE se não existir
- `DEFINE CLUSTER INDEXED` → `CREATE TABLE clientes (... PRIMARY KEY ...)`
- `KEYS(11 0)` → chave primária de 11 bytes na posição 0
- `RECORDSIZE(200 200)` → registro fixo de 200 bytes
- `SHAREOPTIONS(2 3)` → controle de concorrência (equivalente a isolation level)

---

## 9. DCB — Data Control Block (formato dos dados)

```jcl
//OUTPUT   DD   DSN=PROD.DADOS.SAIDA,
//              DISP=(NEW,CATLG,DELETE),
//              UNIT=SYSDA,
//              SPACE=(CYL,(50,10),RLSE),
//              DCB=(RECFM=FB,LRECL=200,BLKSIZE=27800)
```

### RECFM — Record Format

| RECFM | Significado | Equivalente moderno |
|---|---|---|
| `F` | Fixed — todos os registros têm o mesmo tamanho | CSV com colunas fixas / struct binário |
| `FB` | Fixed Blocked — registros fixos agrupados em blocos | Arquivo binário com registros fixos |
| `V` | Variable — registros de tamanho variável (4 bytes de header) | JSON lines / delimited records |
| `VB` | Variable Blocked — variáveis agrupados em blocos | Arquivo com registros variáveis |
| `FBA` | Fixed Blocked ASA — com carriage control no byte 1 | Report / formatted output |
| `U` | Undefined — sem formato definido (load modules) | Binary blob |

### LRECL — Logical Record Length

Tamanho de cada registro lógico em bytes. Para `RECFM=V`, é o tamanho **máximo** (incluindo 4 bytes de RDW — Record Descriptor Word).

### BLKSIZE — Block Size

Tamanho do bloco físico em disco. `BLKSIZE=0` = o sistema calcula automaticamente o bloco ótimo.

### SPACE — alocação de espaço

```jcl
SPACE=(CYL,(50,10),RLSE)     → 50 cilindros primários, 10 secundários, libera não-usado
SPACE=(TRK,(100,20))          → 100 trilhas primárias, 20 secundárias
SPACE=(nnnnn,(100,20))        → em blocos de nnnnn bytes
```

| Componente | Significado |
|---|---|
| Unidade (`CYL`/`TRK`/bytes) | Granularidade de alocação |
| Primário | Espaço inicial alocado |
| Secundário | Extensão adicional quando esgota (até 15 extensões) |
| `RLSE` | Libera espaço não utilizado após CLOSE |

---

## 10. STEPLIB e JOBLIB — localização de programas

### JOBLIB (escopo do job inteiro)

```jcl
//JOBCALC  JOB ...
//JOBLIB   DD   DSN=PROD.LOADLIB,DISP=SHR
//         DD   DSN=PROD.LOADLIB.UTILS,DISP=SHR
```
Todos os steps do job buscam programas nestas bibliotecas (a menos que tenham STEPLIB próprio).

### STEPLIB (escopo de um step)

```jcl
//STEP010  EXEC PGM=CALCFOLH
//STEPLIB  DD   DSN=PROD.LOADLIB.RH,DISP=SHR
//         DD   DSN=PROD.LOADLIB,DISP=SHR
```
Sobrepõe o JOBLIB apenas para este step. A busca é feita na ordem de concatenação.

### Equivalente moderno

| JCL | Equivalente |
|---|---|
| `JOBLIB` | `PATH` global, `CLASSPATH`, container image base |
| `STEPLIB` | `PATH` local, `CLASSPATH` de task, sidecar container |
| Ordem de concatenação | Precedência em PATH (primeiro encontrado vence) |

---

# PARTE 2 — PROCEDURES (PROCs)

---

## 11. O que é uma PROC e como é expandida

Uma PROC (Procedure) é um **bloco reutilizável de JCL** — um template de steps que pode ser invocado múltiplas vezes com diferentes parâmetros.

### Invocação de PROC

```jcl
//STEP010  EXEC PROC=COPYDATA,
//              DSIN='PROD.ENTRADA',
//              DSOUT='PROD.SAIDA',
//              RECLEN=200
```
ou equivalentemente:
```jcl
//STEP010  EXEC COPYDATA,
//              DSIN='PROD.ENTRADA',
//              DSOUT='PROD.SAIDA',
//              RECLEN=200
```

### Definição da PROC (em PROCLIB ou inline)

```jcl
//COPYDATA PROC DSIN=,DSOUT=,RECLEN=80
//*------------------------------------------------------------
//* PROC: COPYDATA - COPIA DATASET COM VALIDACAO
//*------------------------------------------------------------
//VALID    EXEC PGM=VALIDAR
//INPUT    DD   DSN=&DSIN,DISP=SHR
//SYSPRINT DD   SYSOUT=*
//COPY     EXEC PGM=IEBGENER,COND=(0,NE,VALID)
//SYSUT1   DD   DSN=&DSIN,DISP=SHR
//SYSUT2   DD   DSN=&DSOUT,DISP=(NEW,CATLG,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(10,5),RLSE),
//              DCB=(RECFM=FB,LRECL=&RECLEN,BLKSIZE=0)
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   DUMMY
//         PEND
```

### Expansão — o que o JES realmente executa

Quando o JES encontra `EXEC COPYDATA`, ele **substitui** os parâmetros simbólicos e expande os steps da PROC como se estivessem escritos diretamente no JCL:

```jcl
//* --- EXPANSÃO REAL ---
//STEP010.VALID  EXEC PGM=VALIDAR
//STEP010.VALID.INPUT DD DSN=PROD.ENTRADA,DISP=SHR
//STEP010.VALID.SYSPRINT DD SYSOUT=*
//STEP010.COPY   EXEC PGM=IEBGENER,COND=(0,NE,STEP010.VALID)
//STEP010.COPY.SYSUT1 DD DSN=PROD.ENTRADA,DISP=SHR
//STEP010.COPY.SYSUT2 DD DSN=PROD.SAIDA,DISP=(NEW,CATLG,DELETE),...
//STEP010.COPY.SYSPRINT DD SYSOUT=*
//STEP010.COPY.SYSIN DD DUMMY
```

**Nota:** Os nomes dos steps na PROC são qualificados com o nome do step que invocou a PROC (`STEP010.VALID`, `STEP010.COPY`). Isso é importante para referências a return codes: `COND=(0,NE,STEP010.VALID)`.

---

## 12. Parâmetros simbólicos — rastreamento de valores

### Declaração de parâmetros

```jcl
//PROCNAME PROC PARAM1=default1,PARAM2=,PARAM3='valor com espaco'
```

| Aspecto | Sintaxe | Significado |
|---|---|---|
| Com default | `PARAM1=default1` | Usa `default1` se não for fornecido na invocação |
| Sem default (obrigatório) | `PARAM2=` | **Deve** ser fornecido na invocação — erro se ausente |
| Com espaços | `PARAM3='valor com espaco'` | Valor com caracteres especiais entre aspas |
| Referência no corpo | `&PARAM1` ou `&PARAM1.` | Ponto final delimita o nome quando seguido de texto |

### Resolução de parâmetros — rastreamento completo

```jcl
//* --- Na PROCLIB (definição da PROC) ---
//CALCPROC PROC ENV=PROD,TABLIB=,LRECL=200

//STEP01   EXEC PGM=CALCPGM
//INPUT    DD   DSN=&ENV..RH.DADOS,DISP=SHR
//TABELA   DD   DSN=&TABLIB,DISP=SHR
//OUTPUT   DD   DSN=&ENV..RH.RESULTADO,
//              DISP=(NEW,CATLG,DELETE),
//              DCB=(RECFM=FB,LRECL=&LRECL,BLKSIZE=0)
```

```jcl
//* --- No JCL chamador ---
//STEPCALC EXEC CALCPROC,ENV=HLG,TABLIB='HLG.RH.TAB.INSS',LRECL=300
```

**Resolução:**

| Simbólico | Valor na PROC | Override no JCL | Valor final |
|---|---|---|---|
| `&ENV` | `PROD` | `HLG` | `HLG` (override vence) |
| `&TABLIB` | ` ` (vazio) | `HLG.RH.TAB.INSS` | `HLG.RH.TAB.INSS` |
| `&LRECL` | `200` | `300` | `300` (override vence) |

**DSN resolvido:** `&ENV..RH.DADOS` → `HLG.RH.DADOS` (o `..` se torna `.` porque `&ENV.` usa o ponto como delimitador do simbólico).

### Armadilhas de parâmetros simbólicos

1. **Ponto delimitador vs ponto literal:** `&ENV.RH` resolve para `HLGRH` (ponto consumido). Para obter `HLG.RH`, usar `&ENV..RH` (dois pontos — um delimitador, um literal).
2. **Simbólico em subparâmetro:** `DISP=(NEW,&DISP2)` — funciona, mas dificulta a leitura. Rastrear de onde vem `&DISP2`.
3. **Simbólicos aninhados:** Não suportados nativamente. `&&VAR` não é um simbólico de simbólico — `&&` é prefixo de dataset temporário.
4. **SET statement:** `// SET ENV=PROD` define simbólicos no escopo do JCL chamador, podendo sobrepor defaults da PROC.

### SET statement

```jcl
// SET ENV=PROD
// SET DATALIB=&ENV..DADOS      *> DATALIB = PROD.DADOS
//STEP010  EXEC PROCX,LIBRARY=&DATALIB
```

`SET` define variáveis simbólicas no nível do JCL. São resolvidas **antes** da expansão da PROC. Útil para parametrização centralizada.

---

## 13. Overrides de DD em PROC — comportamento alterado

### Override de DD existente na PROC

```jcl
//* --- PROC CALCPROC tem: ---
//STEP01   EXEC PGM=CALCPGM
//INPUT    DD   DSN=&ENV..RH.DADOS,DISP=SHR
//OUTPUT   DD   DSN=&ENV..RH.RESULTADO,DISP=(NEW,CATLG,DELETE)

//* --- JCL chamador faz override: ---
//STEPCALC EXEC CALCPROC,ENV=PROD
//STEP01.INPUT DD DSN=PROD.RH.DADOS.ESPECIAL,DISP=OLD
//STEP01.OUTPUT DD DSN=PROD.RH.RESULTADO.V2,DISP=(NEW,CATLG,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(200,50),RLSE)
```

**Efeito:** O override **substitui completamente** o DD da PROC. Todos os subparâmetros do DD original são perdidos — o override precisa especificar tudo.

### Adição de DD que não existe na PROC

```jcl
//STEPCALC EXEC CALCPROC,ENV=PROD
//STEP01.DEBUGLOG DD SYSOUT=*
```

**Efeito:** Adiciona o ddname `DEBUGLOG` ao step `STEP01` da PROC. O programa pode usar esse ddname se souber que ele existe.

### Onde overrides escondem lógica importante

**Overrides são uma das maiores fontes de "lógica invisível" em JCL.** O analista que lê apenas a PROC não vê o comportamento real:

1. **Mudança de dataset:** O JCL chamador aponta `INPUT` para um dataset diferente do padrão da PROC — o fluxo de dados real é diferente do documentado na PROC.

2. **Mudança de DISP:** O JCL chamador muda `DISP=SHR` para `DISP=OLD` — obtém lock exclusivo que a PROC original não pedia. Pode causar contenção.

3. **Adição de SYSUDUMP:** JCL chamador adiciona `STEP01.SYSUDUMP DD SYSOUT=*` — ativa dump em caso de abend que a PROC não previa.

4. **Override de SYSIN:** JCL chamador sobrescreve parâmetros de controle de utilitários:
   ```jcl
   //STEP01.SYSIN DD *
     SORT FIELDS=(1,20,CH,A)   *> diferente do SORT original na PROC
   /*
   ```
   Isso pode mudar completamente o comportamento de um step de SORT.

### Estratégia de análise

**Sempre analisar PROC + JCL chamador juntos.** Para cada DD da PROC:
1. Verificar se há override no JCL chamador
2. Se houver, documentar a diferença
3. Avaliar se o override muda o comportamento semântico (ex: dataset diferente, parâmetros de controle diferentes)

---

## 14. PROC inline vs PROCLIB — localização e escopo

### PROC de PROCLIB (catalogada)

```jcl
//STEP010  EXEC CALCPROC,ENV=PROD
```

A PROC `CALCPROC` é buscada na concatenação de **PROCLIBs** definida na configuração do JES. O analista precisa saber em qual PDS ela está:

- `SYS1.PROCLIB` — PROCs do sistema
- `PROD.PROCLIB` — PROCs de produção
- `DEV.PROCLIB` — PROCs de desenvolvimento

**Para localizar:** Verificar o `JCLLIB ORDER` no JCL (se presente) ou consultar a configuração do JES.

```jcl
//JOBCALC  JOB ...
//         JCLLIB ORDER=(PROD.PROCLIB,SYS1.PROCLIB)
//STEP010  EXEC CALCPROC
```

`JCLLIB ORDER` define a ordem de busca — funciona como `PATH`. A primeira PROCLIB que contiver o member `CALCPROC` é usada.

### PROC inline (embutida no JCL)

```jcl
//JOBCALC  JOB ...
//*
//COPYDATA PROC DSIN=,DSOUT=
//STEP01   EXEC PGM=IEBGENER
//SYSUT1   DD   DSN=&DSIN,DISP=SHR
//SYSUT2   DD   DSN=&DSOUT,DISP=(NEW,CATLG,DELETE),
//              UNIT=SYSDA,SPACE=(CYL,(10,5),RLSE),
//              DCB=(RECFM=FB,LRECL=80,BLKSIZE=0)
//SYSPRINT DD   SYSOUT=*
//SYSIN    DD   DUMMY
//         PEND
//*
//COPY1    EXEC COPYDATA,DSIN='PROD.ARQ1',DSOUT='PROD.ARQ1.COPY'
//COPY2    EXEC COPYDATA,DSIN='PROD.ARQ2',DSOUT='PROD.ARQ2.COPY'
//COPY3    EXEC COPYDATA,DSIN='PROD.ARQ3',DSOUT='PROD.ARQ3.COPY'
//
```

### Diferenças entre inline e PROCLIB

| Aspecto | PROC de PROCLIB | PROC inline |
|---|---|---|
| Definição | Em PDS separada (PROCLIB) | Dentro do próprio JCL |
| Escopo | Disponível para qualquer job | Apenas no job que a contém |
| Reutilização | Centralizada — mudança afeta todos os jobs | Local — mudança afeta apenas este job |
| Delimitador | N/A (é um member de PDS) | `PEND` marca o fim da PROC |
| Localização | `JCLLIB ORDER` ou config do JES | Antes do primeiro EXEC que a invoca |
| Manutenção | Versionada separadamente | Versionada junto com o JCL |

### Como identificar

| Pista | Tipo |
|---|---|
| `PROC` e `PEND` visíveis no JCL | Inline |
| `EXEC PROCNAME` sem `PROC`/`PEND` no JCL | PROCLIB (buscar na PDS) |
| `JCLLIB ORDER` presente | Indica de qual PROCLIB buscar |

---

## 15. PROC como componente reutilizável — mapeamento moderno

### Analogia com orquestradores

| Conceito PROC | Airflow | Step Functions | GitHub Actions | Kubernetes |
|---|---|---|---|---|
| PROC (definição) | DAG/TaskGroup reutilizável | Nested state machine | Reusable workflow / composite action | Helm chart / Job template |
| Parâmetros simbólicos | `params` / `op_kwargs` | Input parameters | `inputs` | Values / env vars |
| Invocação (`EXEC PROC=`) | `TriggerDagRunOperator` / `TaskGroup()` | `"Type": "Task"` com resource ARN | `uses: ./.github/workflows/x.yml` | `helm install` / apply |
| Override de DD | Override de connection/variable | Override input/output | `with:` parameters | ConfigMap / volume mount override |
| Steps dentro da PROC | Tasks dentro do TaskGroup | States dentro do nested workflow | Steps dentro do composite action | Containers dentro do Job |
| PROCLIB | DAG repository / package | Definition ARN | Workflow file in repo | Chart repository |

### Exemplo de tradução: PROC → Airflow TaskGroup

**PROC original:**
```jcl
//ETLPROC  PROC SRCDS=,TGTDS=,SORTKEY='1,10,CH,A'
//EXTRACT  EXEC PGM=EXTPGM
//INPUT    DD   DSN=&SRCDS,DISP=SHR
//OUTPUT   DD   DSN=&&RAWDATA,DISP=(NEW,PASS)
//SORT     EXEC PGM=SORT,COND=(4,LT,EXTRACT)
//SORTIN   DD   DSN=&&RAWDATA,DISP=(OLD,DELETE)
//SORTOUT  DD   DSN=&&SORTED,DISP=(NEW,PASS)
//SYSIN    DD   *,SYMBOLS=JCLONLY
  SORT FIELDS=(&SORTKEY)
/*
//LOAD     EXEC PGM=LOADPGM,COND=(4,LT)
//INPUT    DD   DSN=&&SORTED,DISP=(OLD,DELETE)
//OUTPUT   DD   DSN=&TGTDS,DISP=(NEW,CATLG,DELETE)
//         PEND
```

**Tradução para Airflow:**
```python
from airflow.utils.task_group import TaskGroup

def etl_task_group(src_ds: str, tgt_ds: str, sort_key: str = "col1 ASC"):
    """Equivalente à PROC ETLPROC"""
    with TaskGroup(group_id="etl") as etl:
        
        @task
        def extract(source: str) -> str:
            """Equivalente ao step EXTRACT (PGM=EXTPGM)"""
            raw_data = extract_data(source)
            return save_to_staging(raw_data)  # &&RAWDATA
        
        @task
        def sort_data(staging_path: str, sort_key: str) -> str:
            """Equivalente ao step SORT (PGM=SORT)"""
            data = load_from_staging(staging_path)
            sorted_data = sort(data, key=sort_key)
            return save_to_staging(sorted_data)  # &&SORTED
        
        @task
        def load(staging_path: str, target: str):
            """Equivalente ao step LOAD (PGM=LOADPGM)"""
            data = load_from_staging(staging_path)
            write_to_target(data, target)
        
        raw = extract(src_ds)
        sorted_path = sort_data(raw, sort_key)
        load(sorted_path, tgt_ds)
    
    return etl

# Invocações (equivalente a múltiplos EXEC ETLPROC)
with DAG("job_etl_diario"):
    etl_vendas = etl_task_group("PROD.VENDAS", "DW.VENDAS", "data ASC")
    etl_clientes = etl_task_group("PROD.CLIENTES", "DW.CLIENTES", "cpf ASC")
```

### Exemplo de tradução: PROC → AWS Step Functions

```json
{
  "Comment": "Equivalente à PROC ETLPROC",
  "StartAt": "Extract",
  "States": {
    "Extract": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:extract",
      "Parameters": {
        "source.$": "$.srcDs"
      },
      "ResultPath": "$.rawData",
      "Next": "SortData",
      "Catch": [{
        "ErrorEquals": ["ExtractError"],
        "Next": "HandleError"
      }]
    },
    "SortData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:sort",
      "Parameters": {
        "data.$": "$.rawData",
        "sortKey.$": "$.sortKey"
      },
      "ResultPath": "$.sortedData",
      "Next": "Load"
    },
    "Load": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:load",
      "Parameters": {
        "data.$": "$.sortedData",
        "target.$": "$.tgtDs"
      },
      "End": true
    },
    "HandleError": {
      "Type": "Fail",
      "Error": "ETLFailed"
    }
  }
}
```

---

## 16. INCLUDE e JCLLIB — inclusão de JCL externo

### INCLUDE statement

```jcl
//         JCLLIB ORDER=(PROD.JCLLIB,SYS1.JCLLIB)
//STEP010  EXEC PGM=MYPGM
//         INCLUDE MEMBER=DDALOC
```

**Significado:** Insere o conteúdo do member `DDALOC` da JCLLIB no ponto da inclusão. Equivalente ao `COPY` do COBOL ou `#include` do C.

**Uso típico:** Centralizar DDs comuns (STEPLIB, SYSPRINT, SYSOUT) que se repetem em muitos jobs.

### Armadilha

`INCLUDE` torna a leitura do JCL incompleta sem acesso à JCLLIB. O analista deve:
1. Identificar todos os `INCLUDE` statements
2. Localizar os members referenciados
3. Expandir mentalmente (ou documentar) o JCL completo com as inclusões

---

## 17. Tratamento de erros e restart em JCL

### Abend codes comuns

| Código | Tipo | Significado | Causa provável |
|---|---|---|---|
| `S0C7` | System | Data exception | Dados não-numéricos em campo numérico (COMP-3 corrompido) |
| `S0C4` | System | Protection exception | Acesso a memória inválida (subscript fora do range) |
| `S0C1` | System | Operation exception | Instrução inválida (load module corrompido) |
| `S222` | System | Job cancelado pelo operador | Timeout ou intervenção manual |
| `S322` | System | Tempo de CPU excedido | Loop infinito ou TIME insuficiente |
| `S806` | System | Programa não encontrado | Load module ausente na STEPLIB/JOBLIB |
| `S913` | System | Erro de segurança (RACF) | Sem permissão para acessar dataset |
| `Unnnn` | User | Abend de usuário | Programa executou `CALL ABEND(nnnn)` |

### Restart de jobs

```jcl
//JOBCALC  JOB ...,RESTART=STEP020
```

**Significado:** Reinicia a execução a partir de `STEP020`, pulando steps anteriores. Usado quando um job falha em um step intermediário e os steps anteriores já concluíram com sucesso.

**Cuidados no restart:**
1. Datasets criados por steps anteriores devem **ainda existir** (não foram deletados pelo operador)
2. Datasets temporários (`&&`) **não sobrevivem** a um restart — se um step posterior depende de `&&TEMP` criado por um step anterior, o restart falhará
3. O restart requer intervenção manual (operador ou scheduler)

### Na modernização

| Conceito JCL | Equivalente moderno |
|---|---|
| RESTART=stepname | Retry from checkpoint / resume pipeline |
| Abend | Exception / crash |
| COND=EVEN | `finally` / cleanup step |
| COND=ONLY | `except` / error handler |
| Return code | Exit code / status code |
| MAXCC (JES) | Aggregate exit code do pipeline |

---

## 18. Multi-step patterns — padrões comuns de jobs

### Pattern: ETL (Extract-Transform-Load)

```jcl
//JOBETL   JOB ...
//* --- EXTRACT ---
//STEP010  EXEC PGM=EXTPGM
//INPUT    DD   DSN=PROD.ORIGEM,DISP=SHR
//OUTPUT   DD   DSN=&&EXTRACT,DISP=(NEW,PASS)
//* --- TRANSFORM (SORT + FILTER) ---
//STEP020  EXEC PGM=SORT,COND=(4,LT)
//SORTIN   DD   DSN=&&EXTRACT,DISP=(OLD,DELETE)
//SORTOUT  DD   DSN=&&SORTED,DISP=(NEW,PASS)
//SYSIN    DD   *
  SORT FIELDS=(1,10,CH,A)
  INCLUDE COND=(20,1,CH,EQ,C'A')
/*
//* --- LOAD ---
//STEP030  EXEC PGM=LOADPGM,COND=(4,LT)
//INPUT    DD   DSN=&&SORTED,DISP=(OLD,DELETE)
//OUTPUT   DD   DSN=PROD.DESTINO,DISP=(NEW,CATLG,DELETE)
//* --- REPORT ---
//STEP040  EXEC PGM=RPTPGM,COND=(4,LT)
//INPUT    DD   DSN=PROD.DESTINO,DISP=SHR
//REPORT   DD   SYSOUT=A
```

**Tradução:** Pipeline de dados com stages: ingestão → transformação → carga → reporting.

### Pattern: Backup-Process-Verify

```jcl
//* --- BACKUP ---
//STEP010  EXEC PGM=IEBGENER
//SYSUT1   DD   DSN=PROD.DADOS.MASTER,DISP=SHR
//SYSUT2   DD   DSN=PROD.DADOS.MASTER.BKP,DISP=(NEW,CATLG,DELETE)
//* --- PROCESS ---
//STEP020  EXEC PGM=UPDTPGM,COND=(0,NE,STEP010)
//MASTER   DD   DSN=PROD.DADOS.MASTER,DISP=OLD
//* --- VERIFY ---
//STEP030  EXEC PGM=VERIFPGM,COND=(4,LT)
//MASTER   DD   DSN=PROD.DADOS.MASTER,DISP=SHR
//BACKUP   DD   DSN=PROD.DADOS.MASTER.BKP,DISP=SHR
//REPORT   DD   SYSOUT=*
//* --- CLEANUP (runs even if STEP020 fails) ---
//STEP040  EXEC PGM=CLEANUP,COND=EVEN
//TEMPDIR  DD   DSN=PROD.DADOS.TEMP,DISP=(OLD,DELETE)
```

**Tradução:** Padrão de segurança: backup antes de processar, verificação após, cleanup incondicional.

### Pattern: Conditional branching

```jcl
//STEP010  EXEC PGM=CHECKPGM
//*
//         IF (STEP010.RC = 0) THEN
//STEP020  EXEC PGM=NORMAL
//         ENDIF
//*
//         IF (STEP010.RC = 4) THEN
//STEP030  EXEC PGM=PARCIAL
//         ENDIF
//*
//         IF (STEP010.RC >= 8) THEN
//STEP040  EXEC PGM=NOTIFICA
//MSGDD    DD   *
  ERRO NO PROCESSAMENTO - ACIONAR SUPORTE
/*
//         ENDIF
//*
//STEP050  EXEC PGM=FINALPGM,COND=EVEN
```

**Tradução:** Branch por resultado do step de verificação + step final incondicional.

---

## Checklist geral de modernização JCL/PROC

### Análise do job

- [ ] Listar todos os steps na sequência de execução
- [ ] Identificar o programa executado em cada step (`EXEC PGM=`)
- [ ] Mapear datasets de entrada e saída de cada step
- [ ] Reconstruir o grafo de dependências (dataset compartilhados entre steps)
- [ ] Identificar datasets temporários (`&&`) e seu ciclo de vida
- [ ] Documentar condições de execução (`COND`, `IF/THEN/ELSE`)
- [ ] Identificar steps de cleanup (`COND=EVEN`) e error handling (`COND=ONLY`)

### Análise de PROCs

- [ ] Identificar se a PROC é inline ou de PROCLIB
- [ ] Listar parâmetros simbólicos e seus defaults
- [ ] Rastrear valores reais passados na invocação
- [ ] Identificar overrides de DD no JCL chamador
- [ ] Documentar diferenças entre comportamento da PROC e overrides
- [ ] Avaliar se a PROC pode ser traduzida como componente reutilizável

### Mapeamento de dados

- [ ] Classificar datasets: permanentes vs temporários vs spool
- [ ] Mapear datasets permanentes para storage moderno (tabelas, S3, etc.)
- [ ] Avaliar se datasets temporários podem ser eliminados (pipe direto)
- [ ] Documentar DCB (formato, LRECL) para cada dataset
- [ ] Identificar GDGs e traduzir para versionamento moderno
- [ ] Mapear concatenações de DD para múltiplos inputs

### Mapeamento de controle

- [ ] Traduzir COND para lógica de orquestração moderna
- [ ] Traduzir IF/THEN/ELSE para Choice states ou branches
- [ ] Mapear return codes para status/exit codes modernos
- [ ] Identificar padrão de restart e traduzir para checkpointing
- [ ] Mapear NOTIFY para alertas/webhooks
- [ ] Traduzir TIME para timeouts

### Mapeamento de SYSOUT/logs

- [ ] Classificar saídas: log operacional vs relatório de negócio
- [ ] Mapear SYSPRINT/SYSOUT para logging estruturado
- [ ] Mapear relatórios para geração de arquivos ou dashboards
- [ ] Identificar carriage control (FBA) e traduzir formatação

---

## Definition of Done (Modernização JCL/PROC)

- [ ] Fluxo de execução completo documentado como DAG
- [ ] Todos os programas executados identificados e categorizados (custom vs utilitário)
- [ ] Dependências de dados entre steps mapeadas
- [ ] Datasets temporários avaliados para eliminação ou substituição
- [ ] Condições de execução traduzidas para orquestração moderna
- [ ] PROCs decompostas em componentes reutilizáveis
- [ ] Overrides documentados com impacto semântico
- [ ] Parâmetros simbólicos rastreados até valores reais
- [ ] Saídas (SYSOUT/SYSPRINT) classificadas e mapeadas
- [ ] Estratégia de restart/recovery definida