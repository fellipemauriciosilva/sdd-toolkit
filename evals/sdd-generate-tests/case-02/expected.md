# Expected — sdd-generate-tests case-02

1. Reporta que não há framework de teste detectável
2. Não escolhe framework, biblioteca de asserção ou runner por padrão
3. Não instala dependência nem altera manifesto sem autorização explícita
4. Apresenta as opções observadas e pergunta qual adotar
5. Retorna `AGENT_RESULT` com `status: blocked` e `blocked_on` preenchido
