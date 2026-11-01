# Agente local — Fase 4

## Componentes e fronteiras

O núcleo é acessível por `ServicoAgente.processar_pergunta` e pela CLI `emporio_ia.conversar`, sem nova rota HTTP. O frontend permanece inalterado. A API de saúde não carrega modelo, fontes ou agente.

| Camada         | Responsabilidade                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------------ |
| Domínio        | Mensagens, solicitações, dados de ferramentas, evidências, resposta e erros independentes de Ollama/FastAPI/SQLite |
| Aplicação      | Contratos de modelo e ferramentas; orquestração, limites, proteção de entrada e fundamentação                      |
| Infraestrutura | Adaptador HTTP Ollama; validação dos cinco esquemas e adaptação dos serviços existentes                            |
| Composição     | CLI monta repositórios e serviços, recebe pergunta e apresenta resposta/referências localmente                     |

```mermaid
sequenceDiagram
    participant CLI
    participant Agente
    participant Modelo as Ollama local
    participant Ferramentas
    CLI->>Agente: Pergunta
    Agente->>Agente: Validar e aplicar limites
    Agente->>Modelo: Instruções + pergunta + esquemas permitidos
    Modelo-->>Agente: Solicitação de ferramenta
    Agente->>Ferramentas: Argumentos validados
    Ferramentas-->>Agente: Dados de leitura e referências
    Agente->>Modelo: Resultados no papel tool com IDs locais
    Modelo-->>Agente: JSON de tipo e evidências selecionadas
    Agente->>Agente: Conferir IDs, fontes e formato; renderizar
    Agente-->>CLI: Resposta restrita ou abstenção
```

Não há container de agentes, SDK de Ollama, cache de conversas ou execução de código solicitado pelo modelo. `httpx`, já instalado nos testes, passa a dependência de execução; nenhuma nova versão de biblioteca foi adicionada ao lock.

## Protocolo local

O adaptador usa `/api/version`, `/api/show` e `/api/chat` documentados pelo Ollama. Antes de cada turno, valida a presença de versão, capacidades de ferramentas e ausência de indicação de modelo remoto. O chat usa ferramentas nativas, `stream=false`, opções configuradas e `think=false` quando o modelo declara suporte a thinking. Retorna apenas conteúdo e solicitações tipadas; formatos malformados ou geração interrompida por limite não são tratados como sucesso.

São aceitas somente URLs HTTP de loopback, com `localhost` convertido para IP local. Não há credenciais, caminhos arbitrários, proxies de ambiente ou redirecionamentos. Nomes com `cloud` e metadados remotos são recusados. A instalação local do servidor continua sendo uma fronteira de confiança; o adaptador não consegue provar o comportamento de um servidor comprometido. A operação documentada usa `OLLAMA_NO_CLOUD=1` no processo Ollama.

Timeout, limite de corpo HTTP, resposta não JSON, modelo ausente, servidor indisponível e falta de ferramentas produzem erros sanitizados. Cancelamento é propagado e os clientes HTTP são fechados. Nenhum corpo de erro, prompt ou resposta privada entra em logs.

## Ferramentas e projeções

| Ferramenta             | Entrada permitida              | Saída autorizada                                                      |
| ---------------------- | ------------------------------ | --------------------------------------------------------------------- |
| `buscar_produtos`      | Termo e limite                 | Nome cadastrado, categoria, preço e disponibilidade                   |
| `consultar_produto`    | Identificador inteiro positivo | Mesma projeção comercial                                              |
| `consultar_categorias` | Limite                         | Nome e identificador de categorias                                    |
| `consultar_promocoes`  | Produto opcional e limite      | Percentual registrado, indicador cadastrado e vigência não confirmada |
| `buscar_politicas`     | Pergunta lexical e limite      | Citação, documento, página, hash, trecho e BM25                       |

Esquemas Pydantic estritos recusam campos extras, coerções de identificadores, SQL e caminhos. O registro é explícito e o executor usa despacho fechado, sem reflexão ou execução de nomes arbitrários. Resultados são limitados pela configuração, mesmo quando o modelo solicita mais. Categorias e promoções reutilizam consultas existentes e só projetam o subconjunto permitido. Descrições livres e especificações dos produtos são omitidas. Nomes são apresentados como valores entre aspas, para não confundir conteúdo com campos ou instruções.

Não existe ferramenta de clientes, pedidos, histórico, estoque mutável, escrita, SQL livre, filesystem ou comandos. A proteção não depende apenas da detecção textual de pedidos pessoais; essas capacidades não estão registradas. A verificação lexical de perguntas pessoais é uma barreira adicional conservadora, não autenticação.

## Fundamentação verificável

O modelo finaliza com JSON contendo apenas tipo e IDs de evidência. Não controla texto comercial, referências, preços ou páginas exibidos. O servidor associa IDs gerados localmente aos resultados efetivamente obtidos naquela pergunta. Texto livre, campos extras, IDs inexistentes ou ausência de evidência causam abstenção.

A aplicação copia os campos autorizados de produtos e categorias, formata centavos com Decimal e cita o texto documental sem paráfrase livre. Promoções distinguem indicador ativo de confirmação de vigência; não há datas ou cálculos de aplicação de desconto inventados. Referências vêm dos adaptadores locais, nunca de URLs ou páginas sugeridas pelo modelo. BM25 é ordenação lexical, não probabilidade.

Regras conservadoras de intenção exigem catálogo para palavras explícitas de preço/disponibilidade/produto; políticas para termos de política/prazo/troca/entrega/garantia; promoções e categorias para seus termos correspondentes. Perguntas combinadas reconhecidas exigem todas as fontes na seleção final. A regra é heurística: não comprova compreensão de toda paráfrase, associação semântica entre entidades ou completude da resposta. A seleção de ferramentas ainda pode ser inadequada. A resposta apresenta fontes identificadas, sem inventar uma síntese comercial para preencher essas lacunas.

## Limites, memória e falhas

Defaults centralizados: quatro turnos de modelo, seis chamadas totais, três resultados por ferramenta, pergunta de 1000 caracteres, contexto serializado de 6000 bytes, corpo HTTP de 65536 bytes, 512 tokens de saída e contexto do modelo de 8192 tokens. Há margem de compatibilidade configurável entre esses orçamentos. O adaptador verifica o payload real; bytes não equivalem a uma contagem exata do tokenizador.

Operações de modelo têm timeout de 60 segundos, ferramentas dez segundos, e a pergunta inteira 120 segundos. O ciclo é sequencial; chamadas equivalentes após validação e serialização canônica não são repetidas. Ao exceder orçamento, a aplicação não apresenta uma resposta comercial parcial como completa.

Consultas SQLite síncronas usam threads para não bloquear o ciclo assíncrono. Cancelar a espera não mata uma thread já em execução; ela pode terminar em segundo plano, com as restrições e timeout de conexão existentes. As ferramentas são apenas de leitura. Não há paralelismo de ferramentas dentro de uma pergunta, controle global de carga pública ou rate limiting: a aplicação é interna.

O histórico existe apenas dentro do ciclo de uma pergunta. Não há estado de conversa compartilhado ou persistido entre perguntas, arquivos de transcrição ou histórico de clientes. A CLI usa `/sair`, EOF ou Ctrl+C para encerrar e remove caracteres de controle das respostas apresentadas no terminal.

## Prompt injection e observabilidade

O prompt inicial é fixo. Perguntas ficam no papel `user`, solicitações no papel `assistant`, evidências no papel `tool`. Texto recuperado não cria mensagens `system` nem adiciona ferramentas. Mesmo que uma instrução maliciosa influencie a seleção do modelo, a lista fechada, validação de argumentos, limites e renderização final continuam sendo aplicados pela aplicação.

Isso não é uma prova universal de resistência a toda manipulação semântica. Há defesa determinística contra ampliação de capacidades e fabricação de campos de saída. Políticas podem conter instruções textuais e são apresentadas como citações, não executadas como código ou privilegiadas como regras do sistema.

Logs JSON registram somente operação, ferramenta autorizada, duração, estado, categoria de erro e quantidade de resultados. Não contêm pergunta, prompt, nome de produto, valores monetários, texto do PDF, referência pessoal ou resposta. Erros desconhecidos de ferramentas não reproduzem o nome solicitado pelo modelo. A CLI usa stderr, sem arquivo de log próprio; o usuário pode configurar captura externa, que deverá preservar a confidencialidade. Logs do processo Ollama são uma configuração externa ao projeto.

## Homologação e testes

O diagnóstico de ausência do Ollama pertence à Fase 4. A Fase 6 encontrou Ollama 0.40.13 e qwen3:4b Q4_K_M, executou inferência e consultas reais, incluindo CLI e navegador. A matriz ainda contém falhas de geração, seleção e recuperação; o funcionamento comercial não está integralmente homologado. O caminho de template Go e o nativo do GGUF foram comparados sem uma correção conclusiva. Consulte os resultados sanitizados no [relatório da Fase 6](../relatorios/fase6.md). O modelo menor não foi instalado nem homologado.

A suíte comum usa modelo determinístico, transporte httpx simulado, SQLite e políticas fictícias. Cobre formatos, ferramentas, fundamentos, duas fontes, manipulação de evidências, limites, cancelamento, dados pessoais, logs, isolamento entre perguntas e CLI. Não lê arquivos privados. A suíte optativa de atendimento real exige `EMPORIO_TESTAR_OLLAMA_REAL=1`; falhas nela não são convertidas em aprovações da suíte comum. O [guia de execução](../entrega/execucao-local.md) separa os comandos. Há um servidor de homologação que reutiliza fixtures em diretório temporário e o agente real, sem substituir modelos por simuladores.

Referências oficiais: [API de chat](https://docs.ollama.com/api/chat), [ferramentas](https://github.com/ollama/ollama/blob/main/docs/capabilities/tool-calling.mdx) e [execução sem nuvem](https://github.com/ollama/ollama/blob/main/docs/cloud.mdx).
