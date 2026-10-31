# ADR 0005 — Atendimento web local com autorização de evidências

Estado: implementada na Fase 5; homologação do modelo permanece pendente.

## Contexto

O agente interno da Fase 4 consulta fontes confidenciais. Um chat sem autenticação não pode receber automaticamente os dados que a CLI interna consegue consultar. CORS não autoriza publicação.

## Decisão

Adicionar uma aplicação de atendimento ao visitante e um filtro de evidências com aprovação explícita por fingerprint em arquivo privado. Aplicar autorização antes do modelo e novamente na saída. Reutilizar o agente, ferramentas e repositórios existentes. Expor apenas mensagem isolada e referências seguras por HTTP local, sob limites de corpo, frequência, concorrência e tempo. Manter histórico no estado React e persistir somente tema.

Concluir a seleção do modelo com esquema JSON restrito aos identificadores de evidências existentes depois que as fontes necessárias forem consultadas. Preservar as validações de origem e conteúdo da Fase 4; não aceitar análise ou prosa livre como resposta comercial.

## Consequências

Sem aprovação explícita, o chat se abstém e nenhum conteúdo operacional é publicado. Alterar texto invalida a aprovação. A curadoria exige revisão humana e permanece fora do Git. Não existe autorização por cliente nem acesso a pedidos. Os limites são por processo, portanto múltiplos workers e publicação na internet exigiriam outra arquitetura e autenticação. A homologação real é requisito separado, ainda não cumprido em todos os cenários.
