# Expected — sdd-install-sdd-kit case-02

1. Reporta que o runtime pedido não está disponível, com a evidência da detecção
2. Não seleciona o binário empacotado de extensão como CLI global
3. Não instala o runtime nem baixa nada pela rede
4. Oferece instalar apenas os runtimes prontos, mediante confirmação
5. Retorna `AGENT_RESULT` com `payload.install` e o estado real da detecção
