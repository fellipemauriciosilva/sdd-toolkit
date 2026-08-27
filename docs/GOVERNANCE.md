# Governança

O SDD Toolkit é mantido de forma aberta, com revisão técnica dos mantenedores e participação da comunidade.

A manutenção inicial, autoria e escopo de responsabilidade estão registrados em
[MAINTAINERS.md](MAINTAINERS.md). A entrada de novos mantenedores exige revisão
e decisão documentada, sem transferir automaticamente autoria histórica.

## Decisões

- Mudanças de comportamento, segurança, formato de estado ou instalação precisam de issue ou contexto documentado.
- Breaking changes exigem atualização de changelog, documentação e migration guide.
- Pelo menos um mantenedor deve revisar mudanças normais; mudanças de segurança ou release exigem dois revisores quando possível.
- O roadmap é a referência para prioridades públicas, mas não garante prazo.

## Releases

Releases são criadas a partir de tags versionadas após CI verde, revisão do changelog e validação dos artefatos. O processo operacional está em [RELEASE.md](RELEASE.md).

## Código gerado

`agents/` e `templates/` são fontes. `dist/` é derivado e deve ser regenerado pelo processo automatizado. Alterações manuais em artefatos gerados não são aceitas sem alteração correspondente na fonte.
