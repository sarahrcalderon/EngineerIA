# ADR 0001 — Arquitetura inicial

Estado: aceita para a Fase 1.

## Contexto

O desafio exige uma base gratuita e local para um futuro agente de atendimento, mantendo os arquivos privados fora do Git. A primeira fase não deve antecipar o agente nem o processamento dos arquivos.

## Decisão

- Python 3.12+: tipagem moderna e ecossistema apropriado para dados e IA.
- FastAPI e Pydantic: contratos explícitos, validação e OpenAPI, com fábrica de aplicação para isolar configuração em testes.
- React: componentes pequenos para estados e apresentação.
- TypeScript: verificação estática; contratos externos ainda são validados em tempo de execução.
- Vite e Tailwind: desenvolvimento local, build estático e estilos sem serviço remoto.
- Monorepo: documentação e contrato HTTP evoluem junto dos dois projetos; dependências e ferramentas permanecem separadas.
- Organização incremental: apenas módulos com responsabilidades atuais. Domínio, aplicação e infraestrutura serão introduzidos quando houver implementação concreta.

## Decisões futuras condicionadas

SQLite é candidato para consultas estruturadas locais, sem serviço dedicado. Sua adequação a concorrência, migrações e volume será validada antes da implementação. Valores monetários devem preservar precisão com `Decimal` e representação persistida adequada.

Ollama é candidato para inferência local sem cobrança por API. A escolha de Qwen3 4B depende de memória, compatibilidade, latência e qualidade verificadas no computador. Não há instalação ou acoplamento ao modelo nesta fase.

## Consequências

A instalação exige Python e Node, mas não Docker. O contrato HTTP desacopla frontend e backend e pode ser testado sem dados operacionais. Não se introduzem frameworks de agentes, banco, bibliotecas de PDF ou abstrações vazias. O lock do frontend e o snapshot das dependências Python tornam a instalação reproduzível; atualizações exigem nova validação.
