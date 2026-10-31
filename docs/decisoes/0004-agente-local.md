# ADR 0004 — Agente local com ferramentas fechadas e respostas extrativas

Estado: aceita para implementação; homologação de inferência real pendente.

## Contexto

Catálogo e políticas já possuem serviços internos de leitura. A nova fase precisa de seleção de ferramentas por um LLM local, sem liberar dados pessoais ou permitir invenção de fatos comerciais. Não há autenticação, atendimento HTTP ou interface de chat nesta etapa. Ollama não está disponível no ambiente inspecionado.

## Decisão

Implementar um contrato de modelo e um adaptador assíncrono pequeno com httpx, sem SDK ou framework pesado de agentes. Configurar preferencial `qwen3:4b`, sem instalá-lo automaticamente e sem afirmar compatibilidade operacional ainda não medida. Oferecer `qwen3:1.7b` como alternativa menor documentada. Confirmar capacidades locais e recusar metadados remotos antes de enviar prompts.

Permitir somente loopback, sem proxies e sem redirects. Documentar `OLLAMA_NO_CLOUD=1` no servidor. A configuração do servidor local é uma fronteira de confiança externa; não se pode provar comportamento de um servidor malicioso pela API.

Registrar explicitamente cinco ferramentas de leitura, com esquemas estritos, limites e projeções reduzidas. Reutilizar `ServicoCatalogo` e `ServicoRecuperacao`. Não registrar consultas de pedidos ou clientes, mesmo que existam na Fase 2. Não fornecer SQL, filesystem, shell ou ferramentas de escrita ao modelo.

Usar chamadas nativas de ferramentas no ciclo, seguido de uma finalização JSON de seleção de evidências. A aplicação monta as respostas comerciais a partir de dados realmente retornados e de citações documentais. Não aceitar prosa comercial livre do modelo, porque presença de uma referência ou autodeclaração de fundamentação não verifica uma afirmação. A abordagem limita fluidez e interpretação, mas torna os campos apresentados verificáveis.

Aplicar regras conservadoras de cobertura de fontes para intenções explícitas e perguntas combinadas. Não alegar validação semântica universal. Ausência, formato inválido, citação desconhecida ou fonte necessária não recuperada resultam em abstenção ou esclarecimento. Promoções permanecem sem confirmação temporal; BM25 não é certeza.

Manter histórico apenas durante uma pergunta, com limites de etapas, chamadas, resultados, contexto, resposta e tempo. Executar ferramentas sequencialmente e bloquear repetição canônica. A CLI não persiste conversas ou inicia atendimento pela rede.

## Consequências

O núcleo é testável sem Ollama por simuladores e HTTP mock, com adaptadores reais de dados sintéticos. A versão de httpx já presente passa a dependência de execução; nenhuma nova biblioteca é baixada. A API e o frontend não mudam.

Prompt injection não depende apenas de instruções do sistema: há redução de capacidades e validação determinística fora do modelo. A seleção de fontes pode continuar errada ou incompleta; citações não equivalem a interpretação comercial. A busca FTS5 mantém as limitações lexicais da Fase 3. Consultas SQLite canceladas podem continuar brevemente em threads, sempre sem escrita.

Ollama real, consumo de RAM/VRAM, latência, confiabilidade de tool calling e qualidade do modelo nesta máquina devem ser homologados antes de declarar funcionamento de ponta a ponta. A fase seguinte poderá preparar chat e integração controlada, sem liberar pedidos pessoais antes de autorização apropriada.
