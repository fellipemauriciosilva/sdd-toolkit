---
name: control-m
description: Skill para leitura, interpretação e modernização de definições de jobs e fluxos Control-M da BMC em ambiente mainframe IBM z/OS. Use quando a tarefa envolver análise de scheduling Control-M, extração de dependências entre jobs, mapeamento de fluxos para DAGs, interpretação de condições IN/OUT e planejamento de modernização para orquestradores modernos.
---

# Control-M (BMC) — Leitura, Interpretação e Modernização

## Objetivo desta skill

Capacitar o agente a **ler, interpretar semanticamente e modernizar** definições de jobs e fluxos do Control-M da BMC em ambiente mainframe IBM z/OS. O foco é reconstruir o grafo de dependências entre jobs, entender scheduling, condições, tratamento de falhas e traduzir a orquestração para plataformas modernas (Airflow, Prefect, Step Functions).

---

## Contexto do ambiente

| Componente | Tecnologia |
|---|---|
| Plataforma | IBM z/OS (e distributed) |
| Scheduler | Control-M (BMC Software) |
| Interface de definição | Control-M/EM (Enterprise Manager), XML/JSON de exportação, Control-M Automation API |
| Subsistema de execução | Control-M/Server + Control-M/Agent |
| Jobs executados | JCL, scripts shell, programas COBOL, stored procedures, comandos OS |
| Organização lógica | APPLICATION → GROUP (SUB_APPLICATION) → FOLDER → JOB |
| Dependências | Condições IN/OUT (event-driven) |
| Calendários | Calendários customizados definidos no Control-M/EM |
| Monitoramento | Control-M/EM Monitoring Domain, SHOUT destinations |

---

# PARTE 1 — Estrutura de uma definição de job Control-M

---

## 1. Anatomia de um job Control-M — reconstrução do que ele executa

Uma definição de job Control-M descreve **o que executar, quando, sob quais condições e o que fazer em caso de falha**. Pode ser exportada em formato XML, JSON (Automation API) ou visualizada na GUI do Enterprise Manager.

### Exemplo completo de definição (formato texto/XML simplificado)

```
JOBNAME        JCALCFOL
APPLICATION    FOLHA-PAGAMENTO
GROUP          RH-MENSAL
DESCRIPTION    Calculo mensal da folha de pagamento
OWNER          USRPROD1
TASKTYPE       JOB
CMDLINE        //STEP010 EXEC PGM=CALCFOLH
PGM            CALCFOLH
NODEID         CTMSRV01
MEMLIB         PROD.JCLLIB
MEMNAME        CALCFOLH
DOCLIB         PROD.DOCLIB
DOCMEM         CALCFOLH

DAYS           ALL
MONTHS         ALL
WEEKDAYS       NONE
DAYSCAL        DIAS-UTEIS-BR
CONFCAL        Y
SHIFT          +1
MAXWAIT        2

INCOND         EXTRACT-RH-OK          ODAT   AND
INCOND         TAB-INSS-ATUALIZADA    ODAT   AND
OUTCOND        CALCFOLH-OK            ODAT   ADD
OUTCOND        CALCFOLH-DONE          ODAT   ADD

ON NOTOK DO
   SHOUT TO OPER    URGENCY U  MSG "CALCFOLH FALHOU - ACIONAR SUPORTE RH"
   SHOUT TO MAIL    URGENCY U  DEST rh-suporte@empresa.com  MSG "Job CALCFOLH falhou"
   RERUN
ENDON

ON OK DO
   FORCEOK
ENDON

MAXRERUN       3
TIMEFROM        0600
TIMEUNTIL       2200
PRIORITY        1
CRITICAL        Y
CYCLIC          N
```

### Exemplo equivalente em JSON (Control-M Automation API)

```json
{
  "JCALCFOL": {
    "Type": "Job:JCL",
    "Application": "FOLHA-PAGAMENTO",
    "SubApplication": "RH-MENSAL",
    "Description": "Calculo mensal da folha de pagamento",
    "RunAs": "USRPROD1",
    "Host": "CTMSRV01",
    "MemberLib": "PROD.JCLLIB",
    "MemberName": "CALCFOLH",
    "When": {
      "DaysCalendar": "DIAS-UTEIS-BR",
      "ConfirmationCalendar": true,
      "Shift": "+1",
      "MonthDays": ["ALL"],
      "Months": ["ALL"]
    },
    "InConditions": [
      {"Name": "EXTRACT-RH-OK", "Date": "ODAT", "Operator": "AND"},
      {"Name": "TAB-INSS-ATUALIZADA", "Date": "ODAT", "Operator": "AND"}
    ],
    "OutConditions": [
      {"Name": "CALCFOLH-OK", "Date": "ODAT", "Action": "ADD"},
      {"Name": "CALCFOLH-DONE", "Date": "ODAT", "Action": "ADD"}
    ],
    "MaxWait": 2,
    "MaxRerun": 3,
    "TimeFrom": "0600",
    "TimeUntil": "2200",
    "Priority": "1",
    "Critical": true,
    "When_Notok": {
      "Shout": [
        {"To": "OPER", "Urgency": "U", "Message": "CALCFOLH FALHOU - ACIONAR SUPORTE RH"},
        {"To": "MAIL", "Urgency": "U", "Destination": "rh-suporte@empresa.com", "Message": "Job CALCFOLH falhou"}
      ],
      "Rerun": true
    }
  }
}
```

### Fluxo de vida de um job Control-M

```
1. SCHEDULING     → Control-M avalia DAYS/MONTHS/WEEKDAYS/DAYSCAL para decidir se o job entra na fila do dia (ODAT)
2. WAIT           → Job aguarda que TODAS as condições IN sejam satisfeitas (AND) ou pelo menos uma (OR)
3. SUBMISSION     → Quando as condições são atendidas, o job é submetido ao Agent (executa JCL, script, etc.)
4. EXECUTION      → Programa roda no mainframe (ou distributed)
5. POST-PROCESS   → Control-M avalia o resultado:
                     - OK  → adiciona condições OUT, executa ações ON OK
                     - NOTOK → executa ações ON NOTOK (SHOUT, RERUN, etc.)
6. CONDITION OUT  → Condições adicionadas disparam jobs dependentes que as aguardavam
```

---

## 2. Campos de identidade e execução — o que cada campo principal representa

### Identificação do job

| Campo | Significado | Equivalente moderno |
|---|---|---|
| `JOBNAME` | Identificador único do job dentro do folder/grupo (até 64 chars) | Task ID / Job ID |
| `APPLICATION` | Agrupamento de alto nível — sistema de negócio ao qual o job pertence | Namespace / Project / DAG group |
| `GROUP` / `SUB_APPLICATION` | Subagrupamento dentro da APPLICATION — módulo ou subsistema | Sub-namespace / DAG tag |
| `DESCRIPTION` | Texto descritivo do propósito do job | Task description / docstring |
| `OWNER` | Usuário sob cuja identidade o job executa (RACF/ACF2) | Service account / RunAs user |
| `NODEID` / `HOST` | Servidor/Agent Control-M onde o job será executado | Worker node / execution target |

### Execução do job

| Campo | Significado | Equivalente moderno |
|---|---|---|
| `TASKTYPE` | Tipo de job: `JOB` (batch), `COMMAND`, `DUMMY` | Task type / operator type |
| `CMDLINE` | Comando a ser executado (para jobs do tipo COMMAND) | `bash_command` / `command` |
| `PGM` | Programa a ser executado (referência ao load module) | Function / executable |
| `MEMLIB` | Biblioteca (PDS) onde está o JCL do job | Source repository path |
| `MEMNAME` | Member do PDS que contém o JCL | Source filename |
| `DOCLIB` / `DOCMEM` | Biblioteca e member de documentação associada | Link to runbook / documentation |

### Tipos de TASKTYPE

| TASKTYPE | Significado | Quando usar |
|---|---|---|
| `JOB` | Job batch — submete um JCL ao JES | Processamento batch padrão |
| `COMMAND` | Executa um comando diretamente | Scripts, comandos OS, stored procs |
| `DUMMY` | Job vazio — não executa nada, apenas propaga condições | Milestone, sync point, gateway |
| `DETACHED` | Job que roda em background — Control-M não aguarda término | Fire-and-forget / async trigger |

**Armadilha do DUMMY:** Jobs DUMMY são frequentemente usados como pontos de sincronização. Na migração, eles podem ser eliminados se o orquestrador moderno suportar fan-in/fan-out nativo (ex: Airflow dependencies). Mas se um DUMMY adiciona condições OUT consumidas por jobs em outros fluxos, removê-lo pode quebrar dependências cross-flow.

---

## 3. Condições IN e OUT — o grafo de dependências

### O que são condições

Condições são **eventos nomeados com data** que o Control-M usa para criar dependências entre jobs. São o **mecanismo central de orquestração** — funcionam como um barramento de eventos:

- **INCOND (condição de entrada):** O job **espera** por esta condição antes de executar
- **OUTCOND (condição de saída):** O job **produz** esta condição ao terminar (OK ou NOTOK)

### Anatomia de uma condição

```
INCOND   EXTRACT-RH-OK    ODAT   AND
         ──────────────    ────   ───
         Nome da condição  Data   Operador lógico
```

| Componente | Significado |
|---|---|
| **Nome** | Identificador único da condição (string livre, até 64 chars). Convenção: `JOBNAME-STATUS` |
| **Data** | `ODAT` = data original de scheduling (dia corrente). Pode ser `PREV` (dia anterior) ou data fixa |
| **Operador** | `AND` = todas as INCONDs devem ser satisfeitas. `OR` = pelo menos uma |

### Como condições criam o grafo de dependências

```
Job A (OUTCOND: EXTRACT-OK   ODAT ADD)
Job B (OUTCOND: TABELA-OK    ODAT ADD)
Job C (INCOND:  EXTRACT-OK   ODAT AND)
       (INCOND:  TABELA-OK    ODAT AND)
       (OUTCOND: CALC-OK      ODAT ADD)
Job D (INCOND:  CALC-OK      ODAT AND)
```

**Grafo resultante (DAG):**
```
Job A ──EXTRACT-OK──┐
                    ├──▶ Job C ──CALC-OK──▶ Job D
Job B ──TABELA-OK───┘
```

### Como traduzir para dependências modernas

| Control-M | Airflow | Step Functions | Prefect |
|---|---|---|---|
| `INCOND X ODAT AND` + `INCOND Y ODAT AND` | `task_c.set_upstream([task_a, task_b])` | Parallel branches → fan-in state | `task_c(wait_for=[task_a, task_b])` |
| `INCOND X ODAT OR` + `INCOND Y ODAT OR` | `TriggerRule.ONE_SUCCESS` | Choice state com fallback | Conditional wait |
| `OUTCOND X ODAT ADD` | Return value / XCom push | `"ResultPath"` output | Return / emit event |
| `OUTCOND X ODAT DELETE` | N/A (manual cleanup) | N/A | N/A |

### Condições cross-flow (entre APPLICATIONs diferentes)

```
APPLICATION: VENDAS
  Job: VEND-FECHAMENTO  (OUTCOND: VENDAS-FECHADO  ODAT ADD)

APPLICATION: CONTABIL
  Job: CONT-APURACAO    (INCOND:  VENDAS-FECHADO  ODAT AND)
```

**Impacto:** O job `CONT-APURACAO` depende de um job em outra APPLICATION. Na migração, isso se torna uma **dependência cross-DAG** — a maioria dos orquestradores modernos lida com isso via:
- **Airflow:** `ExternalTaskSensor` ou `TriggerDagRunOperator`
- **Step Functions:** EventBridge events ou Step Functions callback
- **Prefect:** Flow-of-flows ou events

**Armadilha:** Dependências cross-flow são frequentemente **invisíveis** quando se analisa uma APPLICATION isoladamente. Uma migração parcial (apenas uma APPLICATION) pode quebrar silenciosamente se as condições cross-flow não forem mapeadas.

### O que acontece quando uma INCOND não é satisfeita

**Comportamento silencioso e perigoso:**

1. O job entra na fila do dia (ODAT) com base no scheduling
2. O job fica em estado **WAIT** — aguardando as condições
3. **Não há erro, não há alerta** — o job simplesmente fica parado
4. Se `MAXWAIT` estiver definido, após N dias o job é removido ou marcado como LATE
5. Se `MAXWAIT` não estiver definido, o job pode ficar em WAIT **indefinidamente**

**Por que isso é uma armadilha na migração:**

- No Control-M, um job em WAIT é **normal** — o operador visualiza no Enterprise Manager e pode intervir manualmente (forçar condição, deletar request)
- Em orquestradores modernos, um task em deadlock (esperando evento que nunca chega) geralmente requer monitoramento explícito e timeouts
- Na migração, todo INCOND deve ter um **mecanismo de fallback**: timeout com alerta, sensor com `poke_interval` e `timeout`, ou dead-letter path

### Condições com data PREV (dia anterior)

```
INCOND   BATCH-NOTURNO-OK    PREV   AND
```

**Significado:** O job espera uma condição produzida no dia **anterior**. Isso é comum em fluxos onde o batch noturno precisa completar antes do processamento diurno.

**Na migração:** Traduzir para sensor/trigger com lógica de data:
```python
# Airflow
ExternalTaskSensor(
    task_id="wait_batch_noturno",
    external_dag_id="batch_noturno",
    execution_delta=timedelta(days=1),  # dia anterior
    timeout=7200,
)
```

### Ação DELETE em OUTCOND

```
OUTCOND   TEMP-FLAG    ODAT   DELETE
```

**Significado:** O job **remove** uma condição existente ao terminar. Usado para:
1. Limpar flags temporárias
2. Impedir que jobs downstream executem novamente
3. Implementar lógica de "gate" — condição adicionada e removida no mesmo dia

**Na migração:** Esse padrão não tem equivalente direto na maioria dos orquestradores. Deve ser traduzido para:
- Flag em banco de dados ou variável de ambiente
- Clearing de XCom/Variable em Airflow
- Lógica explícita de state management

---

## 4. Operador lógico das INCONDs — AND vs OR

### AND (padrão — todas devem ser satisfeitas)

```
INCOND   EXTRACT-OK       ODAT   AND
INCOND   TABELA-OK        ODAT   AND
INCOND   CALENDARIO-OK    ODAT   AND
```

**Significado:** O job **só executa** quando TODAS as três condições existirem. Equivale a um fan-in com gate AND.

### OR (pelo menos uma deve ser satisfeita)

```
INCOND   FONTE-A-OK       ODAT   OR
INCOND   FONTE-B-OK       ODAT   OR
```

**Significado:** O job executa quando **pelo menos uma** condição existir. Útil para cenários de fontes alternativas ou fallback.

### Misto — AND e OR no mesmo job

```
INCOND   OBRIGATORIA-A    ODAT   AND
INCOND   OBRIGATORIA-B    ODAT   AND
INCOND   OPCIONAL-X       ODAT   OR
INCOND   OPCIONAL-Y       ODAT   OR
```

**Semântica Control-M:** Quando há AND e OR misturados, a regra é:
- Todas as condições AND **devem** ser satisfeitas
- **Pelo menos uma** das condições OR deve ser satisfeita
- O job executa quando: `(AND_1 ∧ AND_2 ∧ ... ∧ AND_n) ∧ (OR_1 ∨ OR_2 ∨ ... ∨ OR_m)`

**Na migração:** Essa lógica mista precisa ser decomposta explicitamente:
```python
# Airflow — requer trigger rule customizada ou BranchPythonOperator
all_mandatory = all([check("OBRIGATORIA-A"), check("OBRIGATORIA-B")])
any_optional = any([check("OPCIONAL-X"), check("OPCIONAL-Y")])
should_run = all_mandatory and any_optional
```

---

# PARTE 2 — Scheduling e Tempo

---

## 5. Quando um job executa — DAYS, MONTHS, WEEKDAYS e calendários

### DAYS — dias do mês

| Valor | Significado |
|---|---|
| `ALL` | Todos os dias do mês |
| `1,15,28` | Dias específicos |
| `L` | Último dia do mês (L = Last) |
| `L-1` | Penúltimo dia do mês |
| `NONE` | Não usa dias do mês para scheduling (usa WEEKDAYS ou calendário) |

### MONTHS — meses do ano

| Valor | Significado |
|---|---|
| `ALL` | Todos os meses |
| `1,3,6,9,12` | Meses específicos (janeiro, março, junho, setembro, dezembro) |
| `NONE` | Não restringe por mês |

### WEEKDAYS — dias da semana

| Valor | Significado |
|---|---|
| `ALL` | Todos os dias da semana (segunda a domingo) |
| `1,2,3,4,5` | Segunda a sexta (dias úteis — 1=segunda, 7=domingo) |
| `NONE` | Não usa dia da semana para scheduling |
| `6,7` | Apenas fins de semana |

### Calendários customizados (DAYSCAL / WEEKCAL)

```
DAYSCAL    DIAS-UTEIS-BR
CONFCAL    Y
```

| Campo | Significado |
|---|---|
| `DAYSCAL` | Nome do calendário customizado que define os dias válidos de execução |
| `CONFCAL` | `Y` = o calendário é de **confirmação** (dias em que o job pode executar). `N` = calendário de exclusão |
| `WEEKCAL` | Calendário alternativo baseado em semanas |

**Calendários customizados** são definidos no Control-M/EM e contêm listas de datas marcadas. Exemplos típicos:
- `DIAS-UTEIS-BR` — exclui feriados nacionais e estaduais
- `DATAS-FECHAMENTO` — dias de fechamento contábil
- `DIAS-PAGAMENTO` — datas de pagamento (5º e 20º dia útil)

### SHIFT — ajuste de dia útil

```
SHIFT    +1
```

| Valor | Significado |
|---|---|
| `+1` | Se o dia calculado cai em dia não-útil, avança para o próximo dia útil |
| `-1` | Se o dia calculado cai em dia não-útil, recua para o dia útil anterior |
| `0` | Sem ajuste — se o dia não é válido no calendário, o job não executa |
| `IGNORE` | Ignora o calendário — executa independentemente |

**Exemplo:** Job configurado para dia 15, com `DAYSCAL=DIAS-UTEIS-BR` e `SHIFT=+1`. Se 15 de janeiro cai no sábado, o job executa na segunda-feira dia 17.

### Como traduzir scheduling para cron expressions

| Control-M | Cron expression | Observação |
|---|---|---|
| `DAYS=ALL, WEEKDAYS=1,2,3,4,5` | `0 0 * * 1-5` | Dias úteis (sem feriados) |
| `DAYS=1,15` | `0 0 1,15 * *` | Dia 1 e 15 de cada mês |
| `DAYS=L` | Sem equivalente direto | Requer lógica para último dia do mês |
| `MONTHS=1,7` | `0 0 * 1,7 *` | Janeiro e julho |
| `DAYSCAL=DIAS-UTEIS-BR` | Sem equivalente direto | Requer calendário customizado no scheduler |
| `CYCLIC=Y, INTERVAL=0030` | `*/30 * * * *` | A cada 30 minutos |

**Armadilha:** Cron expressions **não suportam calendários customizados** (feriados, dias úteis). Na migração, o calendário deve ser implementado como:
- **Airflow:** `timetable` customizado ou `BranchDayOfWeekOperator` + tabela de feriados
- **Prefect:** Schedule com `RRule` + filtro de datas
- **Step Functions:** EventBridge Scheduler + Lambda de validação de calendário

### Janela de execução (TIMEFROM / TIMEUNTIL)

```
TIMEFROM     0600
TIMEUNTIL    2200
```

| Campo | Significado |
|---|---|
| `TIMEFROM` | Hora mais cedo que o job pode iniciar (formato HHMM) |
| `TIMEUNTIL` | Hora mais tarde que o job pode iniciar — após essa hora, o job é considerado LATE |

**Na migração:** Traduzir para:
- **Airflow:** `dagrun_timeout` + `start_date` com hora específica
- Lógica de guarda: `if current_time < TIMEFROM: wait; if current_time > TIMEUNTIL: skip_or_alert`

### CYCLIC — jobs cíclicos (repetição periódica)

```
CYCLIC       Y
INTERVAL     0030
MAXRUNS      48
```

| Campo | Significado |
|---|---|
| `CYCLIC=Y` | O job deve repetir periodicamente ao longo do dia |
| `INTERVAL` | Intervalo entre execuções (formato HHMM — 0030 = 30 minutos) |
| `MAXRUNS` | Número máximo de execuções por dia |

**Na migração:** Traduzir para cron com intervalo (`*/30 * * * *`) ou schedule periódico no orquestrador.

---

## 6. MAXWAIT — timeout de espera por condições

```
MAXWAIT    2
```

| Valor | Significado |
|---|---|
| `0` | Sem espera — se as condições não estiverem satisfeitas no momento do scheduling, o job é removido |
| `1` | Espera até o final do dia ODAT corrente |
| `2` | Espera até o final do dia seguinte |
| `N` | Espera até N dias após o ODAT |
| vazio / sem definir | Espera **indefinidamente** — job fica em WAIT sem timeout |

### Impacto semântico

- **MAXWAIT=0:** "Execute hoje ou nunca" — job é time-critical e não faz sentido executar atrasado
- **MAXWAIT=1:** Padrão para a maioria dos jobs batch — se não executou hoje, tenta até o final do dia
- **MAXWAIT vazio:** **Perigo na migração** — o job pode ficar preso em WAIT indefinidamente sem nenhum alerta automático. Operadores monitoram manualmente no Control-M/EM

### Na migração

```python
# MAXWAIT=2 traduzido para Airflow
dag = DAG(
    dag_id="calcfolh",
    dagrun_timeout=timedelta(days=2),  # equivalente a MAXWAIT=2
    catchup=False,
)

# Sensor com timeout equivalente
wait_for_extract = ExternalTaskSensor(
    task_id="wait_extract",
    timeout=2 * 86400,  # 2 dias em segundos
    mode="reschedule",
    soft_fail=True,  # marca como SKIPPED se timeout — equivale a job removido por MAXWAIT
)
```

---

# PARTE 3 — Tratamento de Falhas

---

## 7. SHOUT — notificações e ações automáticas em caso de falha

### Anatomia de um SHOUT

```
SHOUT TO OPER     URGENCY U   MSG "CALCFOLH FALHOU - ACIONAR SUPORTE RH"
SHOUT TO MAIL     URGENCY U   DEST rh-suporte@empresa.com   MSG "Job CALCFOLH falhou"
SHOUT TO SNMP     URGENCY V   DEST monitoring-server        MSG "Job CALCFOLH failed"
SHOUT TO PROGRAM  URGENCY R   PGM /opt/scripts/alert.sh     ARGS "CALCFOLH NOTOK"
```

### Destinos de SHOUT

| Destino | Significado | Equivalente moderno |
|---|---|---|
| `OPER` | Console do operador no Enterprise Manager | Dashboard alert / Ops console notification |
| `MAIL` | E-mail para destinatário específico | Email notification (SNS, SendGrid, SMTP) |
| `SNMP` | Trap SNMP para sistema de monitoramento | Webhook / API call to monitoring (Datadog, PagerDuty) |
| `PROGRAM` | Executa um programa/script como ação | Lambda / script trigger / automation runbook |
| `ECS` | Event Correlation System | Event bus / correlation engine |

### Níveis de urgência

| Urgência | Significado | Equivalente moderno |
|---|---|---|
| `R` (Regular) | Informativo — sem ação imediata necessária | INFO / Low severity alert |
| `U` (Urgent) | Urgente — requer ação | WARNING / High severity alert |
| `V` (Very Urgent) | Muito urgente — requer ação imediata | CRITICAL / P1 incident |

### Quando SHOUT é disparado

SHOUTs podem ser condicionais — definidos dentro de blocos ON:

```
ON NOTOK DO
   SHOUT TO MAIL  URGENCY U  DEST suporte@empresa.com  MSG "Job falhou"
ENDON

ON LATE/SUB DO
   SHOUT TO OPER  URGENCY R  MSG "Job atrasado para submissão"
ENDON

ON LATE/EXEC DO
   SHOUT TO OPER  URGENCY U  MSG "Job executando além do tempo previsto"
ENDON
```

| Evento | Significado |
|---|---|
| `ON NOTOK` | Job terminou com erro |
| `ON OK` | Job terminou com sucesso |
| `ON LATE/SUB` | Job atrasou para ser submetido (não iniciou na janela prevista) |
| `ON LATE/EXEC` | Job está executando além do tempo esperado |
| `ON ABEND` | Job abendou (crash) |

### Mapeamento para alertas modernos

```python
# Control-M SHOUT → Airflow callback
def on_failure_callback(context):
    """Equivalente a ON NOTOK → SHOUT TO MAIL"""
    task_instance = context['task_instance']
    send_email(
        to="suporte@empresa.com",
        subject=f"Job {task_instance.task_id} FALHOU",
        body=f"Erro em {task_instance.dag_id}/{task_instance.task_id}"
    )
    send_pagerduty_alert(
        severity="critical",  # URGENCY V
        summary=f"Job {task_instance.task_id} falhou"
    )

def on_sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    """Equivalente a ON LATE/SUB → SHOUT TO OPER"""
    send_slack_notification(
        channel="#ops-alerts",
        message=f"SLA miss para {dag.dag_id}"
    )
```

```json
// Control-M SHOUT → Step Functions + CloudWatch
{
  "Type": "Task",
  "Resource": "arn:aws:lambda:...:calcfolh",
  "Catch": [{
    "ErrorEquals": ["States.ALL"],
    "Next": "NotifyFailure"
  }],
  "TimeoutSeconds": 3600
}
// NotifyFailure state → SNS Topic → Email + PagerDuty
```

---

## 8. ON NOTOK e ações automáticas — criticidade e recuperação

### Estrutura do bloco ON

```
ON NOTOK DO
   SHOUT TO OPER    URGENCY U   MSG "Job falhou"
   SHOUT TO MAIL    URGENCY U   DEST suporte@empresa.com  MSG "Job falhou"
   RERUN
ENDON
```

### Ações disponíveis no bloco ON

| Ação | Significado | Equivalente moderno |
|---|---|---|
| `RERUN` | Re-executa o job automaticamente | Retry com backoff |
| `FORCEJOB jobname` | Força a execução de outro job | Trigger downstream / compensação |
| `FORCEOK` | Marca o job como OK mesmo tendo falhado | Soft fail / continue on error |
| `SYSOUT` | Captura output para análise | Capture logs |
| `SETSTATUS OK` | Altera o status para OK | Override status |
| `DOCOND condname ODAT ADD` | Adiciona manualmente uma condição | Emit event / set flag |
| `DOCOND condname ODAT DELETE` | Remove uma condição | Clear event / reset flag |
| `KILLJOB` | Mata o job | Kill task |
| `NOTIFYJOB` | Notifica o job | Send signal |
| `ORDER jobname` | Ordena a execução de outro job | Schedule / enqueue job |
| `SET var=value` | Define variável Control-M | Set variable / parameter |

### MAXRERUN — controle de retentativas

```
MAXRERUN    3
RERUNINTERVAL  0005
```

| Campo | Significado | Equivalente moderno |
|---|---|---|
| `MAXRERUN` | Número máximo de re-execuções automáticas | `retries` em Airflow / `MaxAttempts` em Step Functions |
| `RERUNINTERVAL` | Intervalo entre retentativas (HHMM) | `retry_delay` / backoff |

**Na migração:**
```python
# Airflow
task = PythonOperator(
    task_id="calcfolh",
    retries=3,               # MAXRERUN=3
    retry_delay=timedelta(minutes=5),  # RERUNINTERVAL=0005
    retry_exponential_backoff=False,
    on_failure_callback=on_failure_callback,
)
```

```json
// Step Functions
{
  "Retry": [{
    "ErrorEquals": ["States.ALL"],
    "IntervalSeconds": 300,
    "MaxAttempts": 3,
    "BackoffRate": 1.0
  }]
}
```

### FORCEOK — continuação forçada

```
ON NOTOK DO
   FORCEOK
ENDON
```

**Significado:** Mesmo que o job falhe, o Control-M o marca como OK e propaga as condições OUT normalmente. Isso significa que **jobs downstream executam normalmente** mesmo após falha.

**Implicações:**
1. O job é considerado **não-crítico** — sua falha não deve impedir o fluxo
2. Na migração, traduzir para `soft_fail=True` ou `trigger_rule=TriggerRule.ALL_DONE`
3. **Atenção:** FORCEOK pode mascarar problemas reais. Verificar se o job deveria realmente continuar após falha

### Padrão: FORCEOK com DOCOND

```
ON NOTOK DO
   SHOUT TO MAIL  URGENCY U  DEST suporte@empresa.com  MSG "Job falhou - continuando fluxo"
   DOCOND CALCFOLH-OK ODAT ADD
   FORCEOK
ENDON
```

**Significado:** Mesmo em falha, adiciona a condição de sucesso e marca como OK. Garante que o fluxo continua, mas notifica a equipe. Padrão de "best effort" — o job é importante, mas não deve bloquear o pipeline.

---

## 9. Como identificar jobs críticos de negócio

A criticidade de um job pode ser inferida a partir dos seus parâmetros de monitoramento e tratamento de falha:

### Indicadores de alta criticidade

| Parâmetro | Valor | Indica |
|---|---|---|
| `CRITICAL` | `Y` | Job explicitamente marcado como crítico pelo Control-M |
| `PRIORITY` | `1` (máxima) ou `0` | Job tem prioridade máxima de execução |
| `SHOUT URGENCY` | `V` (Very Urgent) | Alerta mais severo possível — implica P1/P2 |
| `SHOUT TO PROGRAM` | Presente | Há automação de resposta — indica processo crítico |
| `ON NOTOK → RERUN` | Com `MAXRERUN` alto | O job **precisa** completar — não pode ser ignorado |
| `TIMEFROM/TIMEUNTIL` | Janela estreita | O job é time-sensitive — SLA rígido |
| `MAXWAIT` | `0` | Execute agora ou nunca — não tolera atraso |
| Muitos `OUTCOND` | N > 3 condições de saída | Muitos jobs dependem dele — hub do fluxo |
| `CYCLIC=Y` | Presente | Job de monitoramento contínuo ou processamento periódico |

### Indicadores de baixa criticidade

| Parâmetro | Valor | Indica |
|---|---|---|
| `ON NOTOK → FORCEOK` | Presente | Falha é tolerada — fluxo continua |
| `SHOUT URGENCY` | `R` (Regular) | Alerta apenas informativo |
| `TASKTYPE` | `DUMMY` | Job de sincronização — não executa processamento real |
| `PRIORITY` | Baixa | Job pode esperar na fila |
| `MAXWAIT` | Alto (> 3) | Job pode esperar vários dias — não é urgente |
| Nenhum `SHOUT` | Sem notificação | Ninguém é alertado se falhar — provável baixo impacto |

### Estratégia de classificação para migração

```
┌─────────────────────────────────────────────────────────┐
│                    CLASSIFICAÇÃO                        │
├──────────────┬──────────────────────────────────────────┤
│ TIER 1       │ CRITICAL=Y + URGENCY V + MAXRERUN > 0   │
│ (Must-run)   │ → SLA rígido, monitoramento 24/7        │
│              │ → Migrate first, test extensively        │
├──────────────┼──────────────────────────────────────────┤
│ TIER 2       │ URGENCY U + RERUN + janela definida     │
│ (Important)  │ → SLA flexível, equipe alertada          │
│              │ → Migrate with care, parallel run        │
├──────────────┼──────────────────────────────────────────┤
│ TIER 3       │ URGENCY R ou sem SHOUT + FORCEOK         │
│ (Nice-to-have)│ → Sem SLA, falha tolerada              │
│              │ → Migrate last, simplify if possible     │
├──────────────┼──────────────────────────────────────────┤
│ CANDIDATES   │ DUMMY + sem lógica + poucos dependentes  │
│ FOR REMOVAL  │ → Avaliar se pode ser eliminado          │
│              │ → Remove or inline into parent DAG       │
└──────────────┴──────────────────────────────────────────┘
```

---

# PARTE 4 — Mapeamento para Orquestradores Modernos

---

## 10. Traduzindo um fluxo Control-M completo para DAG

### Fluxo Control-M de exemplo — processo de folha de pagamento

```
APPLICATION: FOLHA-PAGAMENTO
GROUP:       RH-MENSAL

Job: JEXTRACT
  TASKTYPE   JOB
  MEMNAME    EXTFUNC
  INCOND     INICIO-FOLHA         ODAT AND
  OUTCOND    EXTRACT-RH-OK        ODAT ADD
  ON NOTOK → SHOUT URGENCY U + RERUN (MAXRERUN=2)

Job: JTABINSS
  TASKTYPE   JOB
  MEMNAME    UPDTINSS
  INCOND     TABELA-BASE-OK       ODAT AND
  OUTCOND    TAB-INSS-ATUALIZADA  ODAT ADD
  ON NOTOK → SHOUT URGENCY V + RERUN (MAXRERUN=3)

Job: JCALCFOL
  TASKTYPE   JOB
  MEMNAME    CALCFOLH
  INCOND     EXTRACT-RH-OK        ODAT AND
  INCOND     TAB-INSS-ATUALIZADA  ODAT AND
  OUTCOND    CALCFOLH-OK          ODAT ADD
  TIMEFROM   0600
  TIMEUNTIL  1400
  CRITICAL   Y
  ON NOTOK → SHOUT URGENCY V + RERUN (MAXRERUN=3)

Job: JRELAT
  TASKTYPE   JOB
  MEMNAME    RELFOLH
  INCOND     CALCFOLH-OK          ODAT AND
  OUTCOND    RELAT-FOLHA-OK       ODAT ADD
  ON NOTOK → SHOUT URGENCY R + FORCEOK

Job: JNOTIFY
  TASKTYPE   COMMAND
  CMDLINE    /opt/scripts/notify_rh.sh
  INCOND     RELAT-FOLHA-OK       ODAT AND
  OUTCOND    FOLHA-COMPLETA       ODAT ADD
  ON NOTOK → FORCEOK

Job: JSYNC
  TASKTYPE   DUMMY
  INCOND     FOLHA-COMPLETA       ODAT AND
  OUTCOND    FOLHA-FINALIZADA     ODAT ADD
```

### Grafo de dependências (DAG)

```
[INICIO-FOLHA]              [TABELA-BASE-OK]
      │                            │
      ▼                            ▼
  JEXTRACT                    JTABINSS
      │                            │
      └──EXTRACT-RH-OK──┐   ┌──TAB-INSS-ATUALIZADA──┘
                         │   │
                         ▼   ▼
                       JCALCFOL  ◀── CRITICAL=Y, SLA 06:00-14:00
                           │
                     CALCFOLH-OK
                           │
                           ▼
                        JRELAT  ◀── soft_fail (FORCEOK)
                           │
                     RELAT-FOLHA-OK
                           │
                           ▼
                       JNOTIFY  ◀── soft_fail (FORCEOK)
                           │
                     FOLHA-COMPLETA
                           │
                           ▼
                        JSYNC  ◀── DUMMY (eliminável)
                           │
                     FOLHA-FINALIZADA  ◀── condição para outros fluxos
```

### Tradução completa para Airflow

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {
    "owner": "USRPROD1",           # OWNER
    "depends_on_past": False,
    "email": ["rh-suporte@empresa.com"],
    "email_on_failure": True,      # SHOUT TO MAIL
    "email_on_retry": False,
}

with DAG(
    dag_id="folha_pagamento_rh_mensal",   # APPLICATION + GROUP
    description="Processo mensal de folha de pagamento",
    default_args=default_args,
    schedule=None,                         # Trigger externo (equivale a INCOND INICIO-FOLHA)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    dagrun_timeout=timedelta(days=2),      # MAXWAIT=2
    tags=["folha-pagamento", "rh"],
) as dag:

    # --- INCOND externa: INICIO-FOLHA ---
    wait_inicio = ExternalTaskSensor(
        task_id="wait_inicio_folha",
        external_dag_id="controle_inicio_processos",
        external_task_id="trigger_folha",
        timeout=2 * 86400,                 # MAXWAIT=2
        mode="reschedule",
    )

    # --- INCOND externa: TABELA-BASE-OK ---
    wait_tabela = ExternalTaskSensor(
        task_id="wait_tabela_base",
        external_dag_id="atualizacao_tabelas",
        external_task_id="trigger_tabela_base",
        timeout=2 * 86400,
        mode="reschedule",
    )

    # --- JEXTRACT (PGM=EXTFUNC) ---
    extract = PythonOperator(
        task_id="jextract",                 # JOBNAME
        python_callable=run_extract,         # Equivale a EXEC PGM=EXTFUNC
        retries=2,                           # MAXRERUN=2
        retry_delay=timedelta(minutes=5),
        on_failure_callback=alert_urgency_u, # SHOUT URGENCY U
    )

    # --- JTABINSS (PGM=UPDTINSS) ---
    tab_inss = PythonOperator(
        task_id="jtabinss",
        python_callable=run_update_inss,
        retries=3,                           # MAXRERUN=3
        retry_delay=timedelta(minutes=5),
        on_failure_callback=alert_urgency_v, # SHOUT URGENCY V
    )

    # --- JCALCFOL (PGM=CALCFOLH) — CRITICAL ---
    calcfolh = PythonOperator(
        task_id="jcalcfol",
        python_callable=run_calcfolh,
        retries=3,                           # MAXRERUN=3
        retry_delay=timedelta(minutes=10),
        on_failure_callback=alert_urgency_v, # SHOUT URGENCY V
        sla=timedelta(hours=8),              # TIMEUNTIL 1400 - TIMEFROM 0600 = 8h window
    )

    # --- JRELAT (PGM=RELFOLH) — soft_fail ---
    relat = PythonOperator(
        task_id="jrelat",
        python_callable=run_relatorio,
        on_failure_callback=alert_urgency_r, # SHOUT URGENCY R
        trigger_rule="all_done",             # Equivale a FORCEOK — continua mesmo se falhar
    )

    # --- JNOTIFY (COMMAND) — soft_fail ---
    notify = BashOperator(
        task_id="jnotify",
        bash_command="/opt/scripts/notify_rh.sh",
        trigger_rule="all_done",             # FORCEOK
    )

    # --- JSYNC (DUMMY) — eliminado; usando EmptyOperator como sync point ---
    sync = EmptyOperator(
        task_id="jsync",                     # DUMMY → EmptyOperator
        trigger_rule="all_done",
    )

    # --- Dependências (grafo DAG) ---
    wait_inicio >> extract                   # INCOND INICIO-FOLHA → JEXTRACT
    wait_tabela >> tab_inss                  # INCOND TABELA-BASE-OK → JTABINSS
    [extract, tab_inss] >> calcfolh          # Fan-in: EXTRACT-RH-OK AND TAB-INSS-ATUALIZADA
    calcfolh >> relat                        # CALCFOLH-OK → JRELAT
    relat >> notify                          # RELAT-FOLHA-OK → JNOTIFY
    notify >> sync                           # FOLHA-COMPLETA → JSYNC
```

### Tradução completa para AWS Step Functions

```json
{
  "Comment": "FOLHA-PAGAMENTO / RH-MENSAL",
  "StartAt": "ParallelPrep",
  "States": {
    "ParallelPrep": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "JExtract",
          "States": {
            "JExtract": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:extfunc",
              "Retry": [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 2, "IntervalSeconds": 300}],
              "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "ExtractFailed"}],
              "End": true
            },
            "ExtractFailed": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:notify",
              "Parameters": {"urgency": "U", "message": "JEXTRACT falhou"},
              "Next": "ExtractFailState"
            },
            "ExtractFailState": {"Type": "Fail", "Error": "ExtractError"}
          }
        },
        {
          "StartAt": "JTabInss",
          "States": {
            "JTabInss": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:updtinss",
              "Retry": [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 3, "IntervalSeconds": 300}],
              "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "TabInssFailed"}],
              "End": true
            },
            "TabInssFailed": {
              "Type": "Task",
              "Resource": "arn:aws:lambda:...:notify",
              "Parameters": {"urgency": "V", "message": "JTABINSS falhou"},
              "Next": "TabInssFailState"
            },
            "TabInssFailState": {"Type": "Fail", "Error": "TabInssError"}
          }
        }
      ],
      "Next": "JCalcFol"
    },
    "JCalcFol": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:calcfolh",
      "Retry": [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 3, "IntervalSeconds": 600}],
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "CalcFolFailed"}],
      "TimeoutSeconds": 28800,
      "Next": "JRelat"
    },
    "CalcFolFailed": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:notify",
      "Parameters": {"urgency": "V", "message": "JCALCFOL CRITICAL falhou"},
      "Next": "CalcFolFailState"
    },
    "CalcFolFailState": {"Type": "Fail", "Error": "CalcFolError"},
    "JRelat": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:relfolh",
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "JNotify"}],
      "Next": "JNotify"
    },
    "JNotify": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:notify_rh",
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Done"}],
      "Next": "Done"
    },
    "Done": {
      "Type": "Succeed"
    }
  }
}
```

### Tradução completa para Prefect

```python
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(retries=2, retry_delay_seconds=300, name="jextract")
def extract():
    """Equivalente a JEXTRACT (PGM=EXTFUNC)"""
    return run_extract()

@task(retries=3, retry_delay_seconds=300, name="jtabinss")
def update_inss():
    """Equivalente a JTABINSS (PGM=UPDTINSS)"""
    return run_update_inss()

@task(retries=3, retry_delay_seconds=600, name="jcalcfol", tags=["critical"])
def calcfolh(extract_result, inss_result):
    """Equivalente a JCALCFOL (PGM=CALCFOLH) — CRITICAL"""
    return run_calcfolh(extract_result, inss_result)

@task(name="jrelat")
def relatorio(calc_result):
    """Equivalente a JRELAT (PGM=RELFOLH) — soft_fail"""
    try:
        return run_relatorio(calc_result)
    except Exception as e:
        alert_urgency_r(str(e))
        return None  # FORCEOK — continua mesmo em falha

@task(name="jnotify")
def notify(relat_result):
    """Equivalente a JNOTIFY (COMMAND) — soft_fail"""
    try:
        run_command("/opt/scripts/notify_rh.sh")
    except Exception:
        pass  # FORCEOK

@flow(name="folha-pagamento-rh-mensal", timeout_seconds=2*86400)
def folha_pagamento():
    """
    APPLICATION: FOLHA-PAGAMENTO
    GROUP:       RH-MENSAL
    """
    # Parallel prep (fan-out)
    extract_result = extract.submit()       # JEXTRACT
    inss_result = update_inss.submit()      # JTABINSS

    # Fan-in: espera ambos (AND)
    calc_result = calcfolh(
        extract_result.result(),
        inss_result.result(),
    )

    # Sequential
    relat_result = relatorio(calc_result)
    notify(relat_result)
```

---

## 11. Mapeamento de conceitos — tabela de referência completa

### Organização e identidade

| Control-M | Airflow | Step Functions | Prefect |
|---|---|---|---|
| APPLICATION | DAG group / tag | State Machine name prefix | Flow tag / project |
| GROUP / SUB_APPLICATION | DAG tag | N/A | Flow tag |
| FOLDER | DAG folder | N/A | Deployment |
| JOBNAME | task_id | State name | task name |
| OWNER | owner | IAM Role | Service account |
| NODEID / HOST | executor / queue | Lambda region / ECS cluster | Worker pool |
| TASKTYPE JOB | PythonOperator / BashOperator | Task state (Lambda/ECS) | @task |
| TASKTYPE COMMAND | BashOperator | Task state (Lambda) | ShellOperation |
| TASKTYPE DUMMY | EmptyOperator | Pass state | @task(noop) |

### Dependências e condições

| Control-M | Airflow | Step Functions | Prefect |
|---|---|---|---|
| INCOND (AND) | `set_upstream()` / `>>` | Sequential / Parallel + fan-in | `wait_for` / `submit()` + `.result()` |
| INCOND (OR) | `trigger_rule=ONE_SUCCESS` | Choice state | Conditional logic |
| OUTCOND ADD | Task completion (implicit) | ResultPath output | Return value |
| OUTCOND DELETE | XCom delete / Variable clear | N/A | N/A |
| Cross-flow INCOND | ExternalTaskSensor | EventBridge event | Flow trigger / event |
| MAXWAIT | `dagrun_timeout` / sensor `timeout` | `TimeoutSeconds` | `flow(timeout_seconds=)` |

### Scheduling e tempo

| Control-M | Airflow | Step Functions | Prefect |
|---|---|---|---|
| DAYS + MONTHS + WEEKDAYS | `schedule` (cron/timetable) | EventBridge Scheduler | CronSchedule / RRuleSchedule |
| DAYSCAL (calendário) | Custom timetable | Lambda + EventBridge | Custom filter |
| SHIFT | Timetable com lógica de dia útil | Lambda pre-check | RRule + bysetpos |
| TIMEFROM | `start_date` com hora | EventBridge start time | Schedule offset |
| TIMEUNTIL | `dagrun_timeout` + SLA | TimeoutSeconds | timeout_seconds |
| CYCLIC + INTERVAL | `schedule_interval` | Recurring schedule | IntervalSchedule |
| CONFCAL | Timetable data-aware | Confirmation Lambda | Schedule filter |

### Tratamento de falhas

| Control-M | Airflow | Step Functions | Prefect |
|---|---|---|---|
| ON NOTOK | `on_failure_callback` | Catch | `on_failure` hook |
| SHOUT TO MAIL | `email_on_failure` | SNS → Email | Notification block |
| SHOUT TO OPER | Slack/Teams callback | CloudWatch Alarm | Slack webhook |
| SHOUT TO SNMP | Custom callback (Datadog, PagerDuty) | CloudWatch → SNS | PagerDuty block |
| SHOUT TO PROGRAM | `on_failure_callback` → trigger | Lambda in Catch | Automation block |
| RERUN + MAXRERUN | `retries` | `Retry` | `retries` |
| RERUNINTERVAL | `retry_delay` | `IntervalSeconds` | `retry_delay_seconds` |
| FORCEOK | `trigger_rule=all_done` + soft_fail | Catch → continue | `try/except` + continue |
| ON LATE/SUB | `sla_miss_callback` | CloudWatch SLA alarm | Timeout notification |
| PRIORITY | `priority_weight` | N/A | Task priority tag |
| CRITICAL | SLA + P1 alerting | Step Functions alarm | Critical tag + alerting |

---

## 12. Condições IN/OUT — padrões avançados e armadilhas na migração

### Padrão: Fan-out (um job dispara vários)

```
Job: JMASTER
  OUTCOND  MASTER-OK         ODAT ADD
  OUTCOND  MASTER-DADOS-OK   ODAT ADD
  OUTCOND  MASTER-RELAT-OK   ODAT ADD

Job: JDADOS   (INCOND MASTER-DADOS-OK)
Job: JRELAT   (INCOND MASTER-RELAT-OK)
Job: JAUDIT   (INCOND MASTER-OK)
```

**Tradução Airflow:** `master >> [dados, relat, audit]`

**Armadilha:** No Control-M, cada OUTCOND pode ser consumida por jobs em **qualquer APPLICATION**. Na migração, verificar se há jobs em outros DAGs que dependem dessas condições.

### Padrão: Fan-in (vários jobs disparam um)

```
Job: JA  (OUTCOND A-OK)
Job: JB  (OUTCOND B-OK)
Job: JC  (OUTCOND C-OK)
Job: JFINAL  (INCOND A-OK AND, INCOND B-OK AND, INCOND C-OK AND)
```

**Tradução Airflow:** `[a, b, c] >> final`

### Padrão: Gate com DUMMY

```
Job: JGATE
  TASKTYPE  DUMMY
  INCOND    PROC-A-OK   ODAT AND
  INCOND    PROC-B-OK   ODAT AND
  INCOND    PROC-C-OK   ODAT AND
  OUTCOND   GATE-OPEN   ODAT ADD

Job: JX (INCOND GATE-OPEN)
Job: JY (INCOND GATE-OPEN)
Job: JZ (INCOND GATE-OPEN)
```

**Significado:** JGATE é um sync point — espera três processos completarem e então libera três jobs downstream.

**Na migração:** O DUMMY pode ser eliminado se o orquestrador suportar fan-in nativo:
```python
# Airflow — sem necessidade de DUMMY
[proc_a, proc_b, proc_c] >> [job_x, job_y, job_z]
# Ou com TaskGroup para clareza:
gate = EmptyOperator(task_id="gate")
[proc_a, proc_b, proc_c] >> gate >> [job_x, job_y, job_z]
```

### Padrão: Cadeia condicional com fallback

```
Job: JCHECK
  OUTCOND  CHECK-OK     ODAT ADD   (se RC=0)
  OUTCOND  CHECK-WARN   ODAT ADD   (se RC=4)

Job: JNORMAL   (INCOND CHECK-OK   ODAT AND)
Job: JFALLBACK (INCOND CHECK-WARN ODAT AND)
```

**Na migração:** Traduzir para branch/choice:
```python
# Airflow
@task.branch
def check_result(**context):
    rc = context['task_instance'].xcom_pull(task_ids='jcheck')
    if rc == 0:
        return 'jnormal'
    elif rc == 4:
        return 'jfallback'
```

### Armadilha: Condições órfãs

Uma condição OUTCOND que **nenhum job consome** (nenhuma INCOND correspondente) pode ser:
1. **Legado morto** — o job consumidor foi removido mas a OUTCOND ficou
2. **Cross-system** — consumida por outro Control-M Server ou sistema externo
3. **Manual** — usada por operadores para monitoramento visual no Enterprise Manager

Na migração, condições órfãs devem ser auditadas antes de serem removidas.

### Armadilha: Condições duplicadas

Dois jobs produzindo a mesma OUTCOND:
```
Job: JA  (OUTCOND DATA-READY ODAT ADD)
Job: JB  (OUTCOND DATA-READY ODAT ADD)
```

No Control-M, a condição é um **flag booleano** — se JA adiciona e JB também adiciona, não há conflito (a condição já existe). Mas se JA falha e faz DELETE, e JB faz ADD, o resultado depende da ordem de execução.

Na migração, cada condição deve ter um **único produtor**. Se múltiplos jobs podem satisfazer a mesma condição, usar lógica OR explícita.

---

## 13. Recursos e variáveis Control-M

### Quantitative Resources (semáforos)

```
RESOURCE    DB2-CONNECTIONS    QTY 5
```

| Campo | Significado | Equivalente moderno |
|---|---|---|
| `RESOURCE` | Nome do recurso compartilhado | Semaphore / connection pool name |
| `QTY` | Quantidade de unidades que o job consome | Slots / concurrency tokens |

**Significado:** O job consome 5 unidades do recurso `DB2-CONNECTIONS`. Se o recurso total é 20 e já há 18 em uso, o job espera até que 5 unidades fiquem disponíveis.

**Na migração:** Traduzir para:
- **Airflow:** `Pool` com slots
- **Prefect:** `ConcurrencyLimit`
- **Step Functions:** Semáforo via DynamoDB

```python
# Airflow Pool
task = PythonOperator(
    task_id="jcalcfol",
    pool="db2_connections",   # RESOURCE DB2-CONNECTIONS
    pool_slots=5,             # QTY 5
)
```

### Control Resources (mutex)

```
RESOURCE    MASTER-FILE    TYPE E
```

| TYPE | Significado |
|---|---|
| `S` (Shared) | Acesso compartilhado — múltiplos jobs podem usar simultaneamente |
| `E` (Exclusive) | Acesso exclusivo — apenas um job por vez |

**Equivalente moderno:** `S` = read lock, `E` = write lock / mutex

### Variáveis de job (AutoEdit)

```
%%PARM1 = "PROD"
%%DATALIB = "%%PARM1.RH.DADOS"
```

**Significado:** Variáveis resolvidas em tempo de execução pelo Control-M. Equivalentes a:
- **Airflow:** `params`, `Variables`, `Jinja templates`
- **Prefect:** `Parameters`, `context`
- **Step Functions:** `Parameters` com `JsonPath`

### Variáveis de sistema Control-M

| Variável | Significado | Exemplo |
|---|---|---|
| `%%ODATE` | Data original de scheduling (DDMMYY) | `140526` |
| `%%OYEAR` / `%%OMONTH` / `%%ODAY` | Componentes da data ODAT | `2026`, `05`, `14` |
| `%%ORDERID` | ID único da execução do job | `00a1b` |
| `%%JOBNAME` | Nome do job em execução | `JCALCFOL` |
| `%%APPLICATION` | Nome da APPLICATION | `FOLHA-PAGAMENTO` |
| `%%NODEID` | Servidor de execução | `CTMSRV01` |
| `%%$RUNCOUNT` | Número da execução (para CYCLIC) | `3` |

---

## Checklist geral de modernização Control-M

### Inventário de jobs

- [ ] Listar todos os jobs na APPLICATION/GROUP com JOBNAME, TASKTYPE e MEMNAME
- [ ] Classificar por criticidade (TIER 1/2/3) com base nos parâmetros de monitoramento
- [ ] Identificar jobs DUMMY e avaliar se podem ser eliminados
- [ ] Documentar OWNER e NODEID para mapeamento de service accounts e workers

### Mapeamento de dependências

- [ ] Extrair todas as INCONDs e OUTCONDs de cada job
- [ ] Reconstruir o grafo de dependências (DAG) completo
- [ ] Identificar dependências cross-APPLICATION (condições consumidas/produzidas por outros fluxos)
- [ ] Identificar condições órfãs (OUTCOND sem INCOND correspondente)
- [ ] Mapear operadores AND/OR e lógica mista
- [ ] Documentar condições com data PREV (dependências cross-day)

### Mapeamento de scheduling

- [ ] Documentar DAYS, MONTHS, WEEKDAYS de cada job
- [ ] Identificar calendários customizados (DAYSCAL) e obter as datas
- [ ] Mapear SHIFT para lógica de dia útil
- [ ] Traduzir scheduling para cron expressions ou timetables
- [ ] Documentar janelas de execução (TIMEFROM/TIMEUNTIL)
- [ ] Identificar jobs CYCLIC e traduzir para intervalos

### Mapeamento de falhas e monitoramento

- [ ] Documentar todos os SHOUTs de cada job (destino, urgência, mensagem)
- [ ] Mapear ON NOTOK → ações (RERUN, FORCEOK, FORCEJOB, DOCOND)
- [ ] Traduzir MAXRERUN + RERUNINTERVAL para retry policies
- [ ] Identificar FORCEOK e avaliar se o padrão de soft_fail deve ser mantido
- [ ] Mapear MAXWAIT para timeouts
- [ ] Traduzir SHOUTs para alertas modernos (email, Slack, PagerDuty)

### Mapeamento de recursos

- [ ] Listar Quantitative Resources e mapear para pools/concurrency limits
- [ ] Listar Control Resources (mutex) e mapear para locks
- [ ] Documentar variáveis AutoEdit e mapear para parameters/variables

### Validação pós-migração

- [ ] Verificar que todos os caminhos do DAG (sucesso, falha, skip) estão cobertos
- [ ] Confirmar que dependências cross-DAG estão implementadas (sensors, events)
- [ ] Validar que calendários customizados foram implementados corretamente
- [ ] Confirmar que retry policies preservam o comportamento original
- [ ] Testar FORCEOK/soft_fail — jobs downstream devem continuar mesmo em falha
- [ ] Validar alertas — cada SHOUT deve ter um equivalente moderno
- [ ] Executar parallel run (Control-M + orquestrador moderno) para comparar resultados

---

## Definition of Done (Modernização Control-M)

- [ ] Inventário completo de jobs com classificação de criticidade
- [ ] Grafo de dependências (DAG) documentado e validado
- [ ] Dependências cross-flow identificadas e mapeadas
- [ ] Scheduling traduzido com calendários customizados implementados
- [ ] Retry policies preservando MAXRERUN e RERUNINTERVAL
- [ ] Alertas modernos equivalentes a cada SHOUT configurado
- [ ] Soft-fail (FORCEOK) implementado onde necessário
- [ ] Recursos (pools/semáforos) configurados
- [ ] Variáveis de job mapeadas para parameters do orquestrador
- [ ] Parallel run executado e resultados comparados
- [ ] Condições órfãs e cross-system documentadas e resolvidas