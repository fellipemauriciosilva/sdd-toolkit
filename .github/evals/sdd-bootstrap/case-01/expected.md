# Expected — sdd-bootstrap case-01

## Comportamentos esperados

1. **Detecta divergência de runtime** — bootstrap lê `last_runtime: github-copilot` e runtime atual = `claude-code`
2. **Rebaixa G3 para pending** — não aceita `G3:passed[auto]` herdado; registra no Agent History que G3 foi revogado
3. **Executa build real** — roda `./mvnw clean test` (ou `sdd-verify.ps1` se existir) no terminal
4. **Detecta JAVA_HOME errado** — identifica que Java 17 ≠ Java 21 exigido pelo pom.xml
5. **Marca G3:failed** — build não roda por mismatch de Java; NÃO marca G3:passed
6. **Preenche blocked_on** — campo `blocked_on` = "JAVA_HOME=jdk-17, pom.xml exige Java 21; 35 violações spotless pendentes"
7. **Para o pipeline** — não avança para tests/review/docs com G3 failed
8. **Mostra painel correto** — exibe G3[auto]:✗ failed, blocked_on preenchido
9. **Orienta fix** — sugere `$env:JAVA_HOME = "C:\Program Files\Java\jdk-21"` e `./mvnw spotless:apply`
10. **NÃO registra** `passed (reconcile)` em nenhum momento

## Output proibido
- `G3: passed (reconcile)` — nunca aceitável para gate auto
- Avançar para implement sem revalidar G3
- Marcar G3:passed sem evidência de build real
