# Expected — sdd-create-spec case-01

1. Cria pasta `.github/docs/specs/JT-2345/`
2. Cria subpasta `test-case/`
3. Cria `tasks.md` com apenas Identification preenchido (Ticket=JT-2345, Type=feature, Status=analysis)
4. Cria `status-task.md` com Ticket e Next Suggested Agent = sdd-analyze-demand
5. Cria `session-state.md` com ticket e project preenchidos
6. Informa: "Execute `/sdd-bootstrap gcb-hr-api-gestao-meta JT-2345` para iniciar"
7. NÃO analisa código, NÃO preenche Demand Summary
