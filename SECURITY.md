# Política de Segurança

Não publique vulnerabilidades, credenciais, prompts sensíveis ou evidências de
exploração em issues ou Discussions.

Use o recurso **Private vulnerability reporting** do GitHub como canal
preferencial. Se ele não estiver habilitado, contate o mantenedor inicial em
[fellipemauriciosilva@gmail.com](mailto:fellipemauriciosilva@gmail.com). Informe
versão afetada, impacto, passos de reprodução e uma possível mitigação, sem
incluir secrets. O LinkedIn não é canal para relatos de segurança.

São relevantes, entre outros: prompt injection, execução inesperada, acesso a
secrets, path traversal, alteração fora do escopo e falhas de instalação,
update ou rollback.

O modelo de ameaças, limites do runtime e práticas de operação estão em
[docs/THREAT-MODEL.md](docs/THREAT-MODEL.md). Após a correção, os mantenedores
publicam um resumo seguro no [CHANGELOG.md](CHANGELOG.md).

## Configuração recomendada no GitHub

Antes de abrir o repositório para contribuições, o mantenedor deve habilitar nas
configurações do GitHub: **Private vulnerability reporting**, **Secret
scanning** e **Push protection** (quando disponíveis), **Dependabot alerts** e
**Dependabot security updates**. Proteja `main` exigindo pull request e revisão
do responsável definido em `.github/CODEOWNERS`.

O repositório não depende de workflows do GitHub Actions. As validações locais
antes de uma release estão documentadas em [docs/RELEASE.md](docs/RELEASE.md).
