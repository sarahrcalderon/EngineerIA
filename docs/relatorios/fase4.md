# Relatório técnico — Fase 4

Data: 31/10/2026. Escopo: núcleo do agente, adaptador Ollama local e ferramentas controladas.

## A. Diagnóstico inicial

Branch `main`, working tree inicialmente limpa, no commit `30d8337` da Fase 3. Os 172 testes existentes passaram antes da implementação. `data/` e `.local/` estavam ignoradas, sem arquivos confidenciais rastreados. Foram registrados hashes SHA-256 das fontes e dos artefatos locais para comparar a preservação ao final.

Foram examinados os contratos reais de catálogo, recuperação documental e entidades. O agente reutiliza esses serviços sem criar consultas paralelas de produtos, novo extrator ou nova indexação. httpx já estava instalado como dependência de desenvolvimento e passou a dependência de execução; não houve download de bibliotecas ou alteração de versões do lock.

## B. Ollama

O executável não foi localizado no PATH nem no diretório padrão verificado. `/api/version` e `/api/tags` não responderam em loopback, inclusive na inspeção fora do ambiente restrito. Portanto não há versão instalada confirmada, lista de modelos disponíveis, inferência, latência ou funcionamento real de ferramentas homologados.

A inspeção de memória encontrou aproximadamente 15,4 GiB totais e 3,8 GiB livres naquele momento. GPU e consumo durante inferência não foram homologados. O preferencial configurado é `qwen3:4b`, com download público de aproximadamente 2,5 GB, ferramentas declaradas e licença Apache-2.0. A memória necessária inclui contexto e execução além dos pesos; não se confirmou viabilidade prática com a memória livre observada.

Foi documentada a alternativa `qwen3:1.7b`, aproximadamente 1,4 GB, com ferramentas e Apache-2.0. Nenhum modelo ou instalador foi baixado automaticamente. O README apresenta instalação oficial, execução local sem nuvem, diagnóstico, escolha do modelo e os passos pendentes de homologação. As versões nos testes HTTP são fictícias e não representam uma instalação real.

## C. Arquitetura

Domínio: mensagens, chamadas, dados de ferramentas, evidências, resposta e erros sem Ollama/FastAPI/SQLite. Aplicação: contratos do modelo/registro, `ServicoAgente` e fundamentação determinística. Infraestrutura: `AdaptadorOllama` e `FerramentasLeitura`. Composição e entrada: `emporio_ia.conversar`.

Ollama é acessado por API HTTP documentada, com cliente assíncrono, timeouts, limite de corpo e leitura validada de mensagens e chamadas. O registro real reutiliza `ServicoCatalogo` e `ServicoRecuperacao`. A API e o frontend não receberam funcionalidades de chat.

Detalhes estão na [arquitetura do agente](../arquitetura/agente-local.md) e na [ADR 0004](../decisoes/0004-agente-local.md).

## D. Ferramentas

| Ferramenta             | Dados apresentados                                                             |
| ---------------------- | ------------------------------------------------------------------------------ |
| `buscar_produtos`      | Nome, categoria, preço cadastrado, disponibilidade e referência de produto     |
| `consultar_produto`    | Mesma projeção por identificador positivo                                      |
| `consultar_categorias` | Nome e identificador, com quantidade limitada                                  |
| `consultar_promocoes`  | Percentual registrado, indicador cadastrado e vigência temporal não confirmada |
| `buscar_politicas`     | Citação, documento, página, hash, trecho e BM25                                |

As entradas possuem esquemas estritos, sem campos extras ou SQL. Valores são validados antes de qualquer execução. Limites solicitados são submetidos ao teto configurado. Descrições e especificações livres dos produtos são omitidas. Não há ferramentas de clientes, pedidos individuais, histórico, escrita, shell, filesystem ou SQL arbitrário.

## E. Orquestração

O ciclo valida a pergunta, envia instruções e esquemas permitidos, interpreta solicitações, valida argumentos, executa leituras sequenciais, atribui IDs locais às evidências e devolve resultados no papel `tool`. O modelo pode solicitar outra ferramenta ou finalizar com JSON de tipo e seleção de evidências. Não é permitido ampliar o registro por conteúdo retornado pelo modelo.

Padrões: quatro etapas, seis chamadas, três resultados por ferramenta, 1000 caracteres de pergunta, 6000 bytes de contexto, 65536 bytes de resposta HTTP, 512 tokens de saída e contexto Ollama de 8192 tokens. Timeouts: modelo 60 segundos, ferramenta dez segundos e pergunta 120 segundos. Todas essas configurações são centralizadas e possuem limites de validação.

Chamadas repetidas após validação/serialização canônica são bloqueadas. Não há paralelismo de ferramentas dentro da pergunta. Cancelamento assíncrono é propagado. Uma leitura SQLite iniciada em thread pode terminar em segundo plano, sem escrita e com o timeout de conexão existente. Estouro de orçamento provoca resposta restrita, sem apresentar evidências parciais como solução completa.

## F. Fundamentação

O modelo não escreve prosa comercial apresentada ao usuário: seleciona referências de resultados realmente obtidos naquela pergunta. A aplicação verifica IDs, formato e fontes exigidas e monta respostas com campos autorizados e citações literais. Texto livre, campos extras, evidência inexistente ou informação insuficiente provocam abstenção. Assim, não se considera suficiente que o modelo declare estar fundamentado.

Preços são formatados com Decimal a partir dos centavos cadastrados. Disponibilidade vem da regra existente da Fase 2. Promoções distinguem cadastro/indicador ativo de vigência atual, que permanece não confirmada. Políticas preservam página, hash e identificador; não há paráfrase livre ou fonte externa para completar lacunas.

Regras de cobertura conservadoras identificam intenções explícitas e exigem catálogo e políticas em perguntas combinadas reconhecidas. Não se declara validação semântica universal: seleção de ferramenta, relevância e completude podem falhar para paráfrases e perguntas ambíguas. O fallback é esclarecer ou não confirmar, mantendo as limitações lexicais da Fase 3. BM25 nunca é tratado como probabilidade de certeza.

## G. Segurança

- Endpoint Ollama restrito a loopback, sem credenciais, proxies de ambiente ou redirects.
- Nomes cloud, metadados remotos e modelos sem capacidade declarada de ferramentas são recusados antes dos prompts.
- A documentação exige operação local com nuvem desabilitada no processo Ollama; um servidor comprometido permanece fora da garantia do adaptador.
- Perguntas e fontes não entram no papel de sistema. Conteúdo malicioso não amplia ferramentas ou permissões.
- Perguntas pessoais têm bloqueio conservador adicional; a garantia principal é a ausência de ferramentas pessoais no registro.
- Logs JSON contêm apenas metadados de operação, duração, status, ferramenta autorizada, categoria e quantidade, sem pergunta, prompt, resposta, preço, nomes ou políticas.
- Erros são sanitizados, incluindo ocultação de valores na representação de erros de configuração.
- Não há transcrições, histórico persistido ou compartilhado entre perguntas, endpoint de atendimento ou arquivo de log próprio.
- A CLI remove caracteres de controle antes de apresentar respostas no terminal.
- Fontes, banco e índice permanecem locais e ignorados. Não houve envio de conteúdo privado a APIs externas.
- A comparação final confirmou SHA-256 idêntico para fontes, banco operacional e índice documental. As verificações SQLite de integridade e referências passaram nos dois bancos.
- A revisão dos 20 arquivos novos ou alterados não encontrou coincidências com os nomes/contatos privados e fragmentos documentais verificados, nem os padrões de credenciais examinados. Essa checagem complementa a revisão do escopo e não é uma prova universal de ausência de segredos.

As projeções e citações não equivalem a prova universal de relevância semântica. O índice e o banco não são criptografados; dependem das permissões locais, como nas fases anteriores. A captura externa do terminal ou logs do processo Ollama exige o mesmo cuidado com confidencialidade.

## H. Testes e resultados

| Verificação executada                                    | Resultado                                                                      |
| -------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `python -m pytest backend/testes` pelo ambiente virtual  | 246 passaram: 172 anteriores e 74 do agente/adaptador/CLI                      |
| `ruff check backend`                                     | Aprovado                                                                       |
| `ruff format --check backend`                            | Aprovado                                                                       |
| Importador e consultas operacionais                      | Testes sintéticos anteriores preservados e aprovados                           |
| Extração, índice e recuperação da Fase 3                 | Testes sintéticos anteriores preservados e aprovados                           |
| Agente com SQLite/documentos fictícios e modelo simulado | Aprovado                                                                       |
| Adaptador com HTTP mock                                  | Protocolo, falhas, limites, modelo remoto, cancelamento e formatos verificados |
| CLI com Ollama indisponível                              | Mensagem sanitizada e saída segura, sem stack trace                            |
| Inicialização FastAPI e `/api/saude` real                | HTTP 200 e JSON original                                                       |
| CORS e ausência de atendimento público                   | Verificados                                                                    |
| `npm.cmd run typecheck`                                  | Aprovado                                                                       |
| `npm.cmd run lint`                                       | Aprovado                                                                       |
| `npm.cmd run format:check`                               | Aprovado                                                                       |
| `npm.cmd run build`                                      | Aprovado                                                                       |
| Vitest, incluindo integração com a API real              | Seis testes passaram                                                           |
| Inferência com Ollama real                               | Não executada: serviço/modelo indisponíveis                                    |

Os testes cobrem argumentos maliciosos, ferramentas desconhecidas, SQL, pedidos/clientes, falta de evidência, preço/política juntos, promoções sem datas, citações corretas, prompt injection documental e de pergunta, descrições omitidas, logs, isolamento entre perguntas e CLI. Fontes de testes são fictícias; nenhuma fixture lê dados privados.

O aviso de depreciação do transporte httpx no TestClient do Starlette permanece. Não houve inspeção visual em navegador ou nova auditoria npm; os alertas moderados anteriores não foram tratados neste escopo. Não se inventaram métricas de inferência ou qualidade do modelo.

## I. Arquivos

Criados: `dominio/agente.py`; contratos, orquestração e fundamentação em `aplicacao/`; adaptadores Ollama e ferramentas em `infraestrutura/`; `conversar.py`; testes do agente; arquitetura, ADR 0004 e este relatório.

Atualizados: `backend/pyproject.toml` para promover httpx a dependência de execução, configuração central, `.env.example`, README e visão geral da arquitetura. O lock mantém as mesmas versões. Frontend, importadores, fontes, repositórios operacionais e recuperação documental anteriores não foram modificados.

## J. Git

Branch `main`. Alterações permanecem no working tree, sem staging. Não foram executados `git add`, commit, push, rebase, branches adicionais ou reescrita de histórico. Dados e derivados não estão incluídos na revisão de commit.

Mensagem sugerida: `feat: implementa agente local com ollama e ferramentas`.

## K. Limitações e pendências

Instalação/homologação de Ollama e modelo, medição de recursos e latência e validação de tool calling real permanecem pendentes. O núcleo foi validado com simuladores e adaptadores reais de dados sintéticos. O modelo local poderá produzir argumentos ou finalização que sejam recusados; não há reparação irrestrita de respostas malformadas.

A saída é extrativa e por templates. As regras de intenção são heurísticas, a busca permanece lexical e a escolha de fontes pelo modelo pode ser inadequada. Há limites de contexto e nenhuma memória entre perguntas. O agente não oferece autenticação, controle de contas, dados pessoais, atendimento em rede ou UI de chat.

## L. Próxima fase

Preparar interface de chat e integração controlada com o backend após homologar o modelo local. Definir fronteiras de sessão, cancelamento, filtragem, limites de requisição e autorização apropriada antes de qualquer exposição. Não liberar consultas pessoais apenas porque já existem serviços internos.

As Fases 1 a 4 contaram com assistência de código do OpenAI Codex. Revisão final e responsabilidade pelo desafio permanecem com a pessoa candidata.
