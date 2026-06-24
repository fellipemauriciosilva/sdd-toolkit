# Expected — sdd-analyze-demand case-01

1. Lê task.md e identifica Demand Summary + Expected Behavior preenchidos
2. Analisa o código existente (MetaRepository, OutboxEventPublisher)
3. Preenche "Entry Point" — Kafka consumer `AprovacaoMetaConsumer`
4. Preenche "Affected Files" com lista dos arquivos a criar/modificar
5. Preenche "Flow Analysis" com o fluxo Kafka → UseCase → Repository → Outbox
6. Preenche "Implementation Plan" com passos concretos
7. Avalia G1: `task.md` tem Demand Summary e Expected Behavior não-TODO → **G1 passed**
8. Registra G1:passed no Agent History
