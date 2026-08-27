# Skills

Skills são contexto técnico reutilizável instalado a partir de
`templates/skills/` e compilado para `dist/shared/skills/`.

Os grupos disponíveis incluem backend .NET, Java/Spring e Python; frontend
Angular, Next.js e React; iOS, Android, integrações, mainframe, banco, Cypress,
Playwright, Pydantic, leitura de documentos e Zephyr.

Uma skill não concede permissões extras ao runtime. Ela deve limitar-se a
orientação técnica verificável, não carregar secrets, dados de clientes ou
instruções para acessar produção.

Para adicionar ou revisar uma skill:

1. confirme autoria, licença e redistribuição;
2. mantenha exemplos fictícios e sanitizados;
3. execute o compilador e os testes de inventário;
4. registre terceiros em [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) quando aplicável.
