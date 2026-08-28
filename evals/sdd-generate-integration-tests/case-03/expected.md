# Expected — sdd-generate-integration-tests case-03

1. Usa o container do broker já adotado pelo projeto, sem presumir a tecnologia
2. Cobre mensagem válida processada, mensagem malformada ignorada e retry em falha
3. Usa o contrato de mensagem definido no `task.md`, sem inventar campos
4. Não declara G4: retorna `payload.integration` com `delivery_status: generated`,
   comando de execução, limitações e `next_agent: sdd-bootstrap`
