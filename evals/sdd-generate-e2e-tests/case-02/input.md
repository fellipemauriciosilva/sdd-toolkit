# Caso 02 — Monorepo com Playwright existente

Projeto consumidor pnpm com `pnpm-lock.yaml` e workspaces `apps/web` e
`packages/ui`. `apps/web` já possui `playwright.config.ts`, projetos Chromium e
Mobile Chrome, fixture de autenticação por role e reporter JUnit usado pelo CI.
A spec adiciona a jornada de cancelamento de pedido. Execute `--generate` com o
plano G2 aprovado.
