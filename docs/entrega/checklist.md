# Checklist de aderência — Fase 6

Esta checklist deriva da instrução de Fase 6 fornecida pelo usuário. Não foi encontrado no checkout um enunciado original separado do desafio que permita certificar todos os requisitos da avaliação externa. Os relatórios das fases são registros de implementação, não substitutos desse enunciado.

| Requisito documentado | Evidência | Estado |
| --- | --- | --- |
| Preservar projeto e chat clássico | Branch main, alterações pontuais e inspeção Edge | Atendido |
| Confirmar instalação/modelo local | Ollama 0.40.13, qwen3:4b Q4_K_M, sem nuvem | Atendido |
| Não baixar/trocar modelo silenciosamente | Mesmo tag e digest; nenhum download | Atendido |
| Produto e busca por nome | Ferramentas reais e casos com modelo real aprovados | Parcial: latência alta |
| Preços e estoque | CLI real e parte da matriz aprovadas | Parcial: preço falhou em outra rodada |
| Promoção sem vigência inventada | Renderização determinística e ferramentas verificadas | Parcial: inferência comercial falhou |
| Políticas e referências corretas | Fontes reais/CLI verificadas; testes de referência | Parcial: consulta de política falhou no chat |
| Pergunta combinada | Casos reais executados | Não atendido: falhas de geração |
| Dados pessoais protegidos | Recusas reais, ferramentas fechadas e testes HTTP | Atendido nos cenários executados |
| Resistência a ampliação por injection | CLI real recusou; testes de whitelist/argumentos | Atendido nos cenários, sem prova universal |
| Navegador → agente/modelo → ferramentas → resposta | Produto fictício exibido no chat com Ollama real | Parcial: RAG comum falhou |
| Erros, limites e cancelamento | API TCP, navegador e regressão | Atendido nos cenários executados |
| Layout e teclado automatizado | Edge desktop/mobile, Tab, Enter, Shift+Enter, foco | Atendido por automação |
| Teclado físico, leitor de tela e celular físico | Não executados | Pendente |
| Fontes privadas intactas e ignoradas | SHA-256, integridade SQLite e varredura do checkout | Atendido no escopo auditado |
| Testes independentes de modelo | pytest/Vitest e ferramentas de qualidade | Atendido |
| Homologação integral do modelo | Matriz real contém falhas explícitas | Não atendido |
| Documentação de execução e limitações | README, guia e relatório | Atendido |
| Não executar stage/commit/push/deploy | Staging vazio, alterações para revisão | Atendido |

Classificação: **bloqueado para declarar homologação integral ou atendimento pronto para uso real**. O código e os testes ficam disponíveis para revisão, com evidências parciais de funcionamento. Isso não equivale a afirmar que o produto inteiro é inutilizável nem a certificar a entrega externa sem seu enunciado original.
