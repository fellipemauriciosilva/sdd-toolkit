# Threat model e tratamento de dados

## Fronteiras

O toolkit escreve somente nos destinos exibidos no plano de instalação: arquivos
do projeto, workspace pessoal autorizado e, quando o runtime Claude for
solicitado, o bootstrap global. Ancestrais com symlink ou junction são
rejeitados antes da primeira cópia.

## Conteúdo não confiável

Specs, documentação, código do projeto, manifests Kubernetes e mensagens de
ferramentas são dados não confiáveis. Eles não podem alterar a política de
permissões, ampliar o escopo ou autorizar ações externas.

## Secrets

Análises de infraestrutura declarativa podem registrar somente nomes, tipos,
chaves e referências de Secret. Valores não são lidos, decodificados,
mascarados, persistidos ou enviados ao modelo. Se uma investigação exigir o
valor, ela deve ocorrer fora do toolkit, com procedimento aprovado pela equipe
responsável.

## Capabilities por agente

Cada agente fonte declara `capabilities` no frontmatter. O compilador usa essa
declaração para gerar o conjunto mínimo de tools do Copilot: agentes somente de
leitura não recebem edição nem terminal; agentes de escrita recebem apenas as
tools de edição; terminal e perguntas são concedidos somente quando declarados.
Um agente sem a declaração falha no build.

## Efeitos externos

Commit, push, criação de branch, abertura de PR, chamadas de API, alterações de
cluster e publicação são opt-in. O fluxo padrão somente apresenta plano, diff,
testes e comandos sugeridos. Qualquer autorização deve ser nominal, específica
e registrada no contexto da sessão.

## Limitações conhecidas antes da release pública

- o runtime pode possuir ferramentas de terminal mais amplas que o domínio
  lógico do toolkit; a integração de capabilities por adapter ainda deve ser
  concluída;
- a política de autorização ainda é instrução de agente, não enforcement fora
  do modelo;
- não há telemetria obrigatória; logs locais podem conter caminhos e resultados
  de comandos conforme o runtime.

Essas limitações impedem declarar o pacote pronto para uma release pública até
que os gates de segurança e supply chain sejam aprovados.
