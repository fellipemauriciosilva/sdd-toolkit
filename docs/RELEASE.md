# Release engineering

O pacote público é produzido somente por `scripts/sdd_release.py`. Ele recompila o inventário, cria ZIP e tar.gz determinísticos, `SHA256SUMS`, SBOM CycloneDX e `provenance.json`.

## Pré-requisitos de publicação

1. Executar testes, schemas, compilação e validação de conteúdo público.
2. Revisar `THIRD_PARTY_NOTICES.md` e `PROVENANCE.md`.
3. Criar e verificar uma tag assinada: `git tag -s vX.Y.Z -m "vX.Y.Z"`.
4. Gerar os artefatos localmente com o comando abaixo e conferir `SHA256SUMS`.
5. Criar a release manualmente no GitHub, anexando ZIP, tar.gz, `SHA256SUMS`,
   SBOM e `provenance.json`.
6. Baixar um artefato publicado em máquina limpa e executar install, doctor,
   update e uninstall.

O repositório não executa pipeline de release. A identidade, assinatura da tag
e revisão dos artefatos são responsabilidade do mantenedor antes da publicação.

## Build local sem publicar

```bash
python scripts/sdd_compile.py --runtime all
python scripts/sdd_release.py --out-dir release-local
cd release-local && sha256sum --check SHA256SUMS
```

Não publique os arquivos gerados sem a aprovação jurídica, de proveniência e de segurança exigida pelo roadmap.
