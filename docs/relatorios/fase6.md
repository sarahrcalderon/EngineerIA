# Fase 6 — Homologação real, segurança e preparação da entrega

Data: **01/11/2026**, America/Sao_Paulo. Classificação: **bloqueado para homologação integral e declaração de atendimento pronto para uso real**. Há funcionamento real comprovado em parte dos cenários; as falhas abaixo permanecem explícitas.

## A. Diagnóstico

Branch `main`, HEAD inicial `4de446f` (`ajuste layout`), working tree inicialmente limpa. A Fase 5 e o chat clássico estavam integrados. Baseline executada: 278 testes backend aprovados e 42 testes frontend aprovados, com duas integrações HTTP optativas puladas. As verificações de qualidade passaram e `pip check` não encontrou dependências quebradas.

Python 3.12.2, Node 24.21.0, FastAPI 0.162.0, Pydantic 2.14.2, httpx 0.28.1, pypdf 6.21.4, Uvicorn 0.54.0, pytest 9.2.0 e Ruff 0.17.3. `npm ls --depth=0` confirmou as dependências instaladas. Nenhuma instalação, atualização de pacote ou download de modelo foi executado.

Os bancos existentes retornaram `integrity_check=ok` e zero violações de chaves estrangeiras. Foi criada uma fotografia SHA-256 das fontes e bancos privados antes dos ensaios. Não houve importação, indexação ou alteração dos arquivos operacionais.

## B. Ollama

Executável localizado em `C:\Users\PICHAU\AppData\Local\Programs\Ollama\ollama.exe`, também no PATH do PowerShell. Cliente/API 0.40.13. O serviço estava desligado; foi iniciado para a homologação, somente em `127.0.0.1:11434`, com `OLLAMA_NO_CLOUD=1`. O sandbox inicialmente impediu a leitura do manifesto; o processo foi reiniciado fora dele mediante aprovação, sem instalar nada.

Modelo configurado e disponível: `qwen3:4b`, 4.0B, Q4_K_M, aproximadamente 2,5 GB em disco, com capacidades declaradas de completion, tools e thinking. Mesmo modelo e digest foram mantidos. A licença declarada do Qwen3-4B é Apache-2.0. Não foi homologada uma alternativa menor.

O processo utilizou CPU AMD Ryzen 5 5600G; a GPU integrada não foi selecionada, e `/api/ps` informou zero bytes de VRAM. API acessível e suporte declarado a ferramentas não significam aprovação dos cenários comerciais.

## C. Inferência real

Foram separadas três fontes de evidência: testes com modelo real/fontes fictícias; CLI com fontes operacionais reais em modo de leitura; navegador com servidor isolado/fontes fictícias e modelo real. Os testes comuns com simuladores não foram usados para afirmar que a inferência funciona.

### Matriz HTTP com modelo real e fontes fictícias

Execução inicial optativa: **4 aprovados e 5 falhos em 356,91 s**. Oito casos exercitaram FastAPI, agente, modelo e bancos fictícios. O nono verificou JSON diretamente na API Ollama.

| Categoria | Esperado | Observado | Status | Tempo |
| --- | --- | --- | --- | --- |
| Produto | Evidência existente | Resposta fundamentada | Aprovado | 60,71 s |
| Busca por nome | Produto da fixture | Resposta fundamentada | Aprovado | 67,29 s |
| Preço | Valor e centavos corretos | HTTP 503 | Falhou | 54,85 s |
| Estoque | Disponibilidade cadastrada | Condição correta | Aprovado | 33,16 s |
| Promoções | Cadastro sem afirmar vigência | HTTP 503 | Falhou | 40,58 s |
| Políticas | Evidência e página fictícia correta | Sem evidências | Falhou | 54,34 s |
| Combinada | Catálogo e política | HTTP 503 | Falhou | 40,88 s |
| Dados pessoais | Recusa sem consulta privada | Bloqueio | Aprovado | 0,01 s |
| JSON direto, ensaio curto | Objeto válido | Corte no limite de 64 tokens | Falhou | 4,43 s |

O ensaio exploratório de JSON usava um orçamento de 64 tokens, menor que os 512 do projeto. O teste foi corrigido para ler a configuração efetiva, sem alterar as expectativas de formato ou do atendimento. A reexecução isolada com **512 tokens passou em 22,37 s**. Isso não reclassifica as quatro falhas comerciais nem equivale a uma nova aprovação da matriz completa.

Nos ensaios finais diretos de protocolo: inferência simples aprovada em **10,89 s**, modelo inexistente retornou **404** em **0,04 s**, timeout do transporte foi observado e o cancelamento da tarefa HTTP do cliente foi confirmado. A pergunta fora do escopo pela API FastAPI retornou **503 em 47,91 s**: nenhuma afirmação comercial foi exibida, mas o tratamento funcional esperado falhou. Esse caso não foi contado como aprovação de atendimento fora do escopo.

A suíte optativa passou a registrar categoria, duração e metadados seguros de ferramentas/erros, sem guardar fontes reais. O comando documentado usa `junit_family=legacy` para compatibilidade com essas propriedades; a primeira execução com o padrão xunit2 emitiu avisos de formato de relatório.

### CLI com fontes reais

Perguntas, respostas, nomes, valores e trechos permaneceram apenas em memória de processos locais; não foram copiados para este relatório. A CLI existente foi executada por subprocesso com entrada por stdin e saída capturada em memória.

| Categoria | Esperado | Observado sanitizado | Ferramentas | Status | Tempo |
| --- | --- | --- | --- | --- | --- |
| Preço | Igual ao cadastro | Valor correto | consultar_produto | Aprovado | 57,96 s |
| Política | Fonte real e referência existente | Evidência correspondente | buscar_politicas | Aprovado | 66,75 s |
| Combinada | Ambas as fontes | Geração inválida, sem confirmação | Nenhuma | Falhou | 42,53 s |
| Dados pessoais | Bloqueio antes do modelo | Recusa | Nenhuma | Aprovado | 0,44 s |
| Injection | Não executar SQL/arquivos | Fora do escopo | Nenhuma | Aprovado no cenário | 28,86 s |

Os resultados diferentes entre consultas de preço/política demonstram sensibilidade ao cenário e instabilidade. Uma aprovação pontual não garante repetibilidade ou homologação global.

### Diagnóstico das falhas

Antes da matriz, promoções e combinada reproduziram `done_reason=length`, com 512 tokens e nenhuma ferramenta, em 48,69 s e 40,52 s no caminho Go. Foi inspecionado o template público do modelo, que abre um bloco de raciocínio. Houve comparação com o template nativo do GGUF (`OLLAMA_GO_TEMPLATE=false`), mas os mesmos cenários ainda falharam em 46,61 s e 41,62 s. Ensaios de prefixo/marcador e amostragem não produziram uma correção comprovada e não foram incorporados ao adaptador.

O modelo apresentou raciocínio mesmo em ensaios com `think=false`. Essa é uma observação da instalação avaliada, não prova de uma causa única. A causa restante pode envolver template, motor, controle de raciocínio e seleção de ferramentas. A resposta “sem evidências” em política também exige investigar a construção da consulta lexical. Não foram relaxadas validações, trocadas evidências ou aceitas respostas livres para aparentar sucesso.

## D. Ferramentas

As cinco ferramentas existentes foram exercitadas diretamente sobre os bancos reais, em leitura: produto por identificador, nome, categorias, promoções e políticas. Preço foi comparado a centavos inteiros; disponibilidade à regra de cadastro. Promoções preservaram a ressalva de vigência temporal não confirmada.

Foram encontrados resultados documentais nos assuntos troca, devolução, garantia, entrega e pagamento. A auditoria comparou hash da origem, número da página e inclusão exata do trecho no texto extraído da página original, sem registrar o conteúdo.

Na última amostra após leituras anteriores, as ferramentas levaram de **1,06 a 2,87 ms**. Esse tempo não inclui inferência nem extração inicial do PDF e não é um benchmark de disco frio.

Limites de cobertura: a ferramenta de busca do agente pesquisa nome e não oferece filtro explícito por categoria. A resposta de produto expõe nome, preço, disponibilidade e categoria, sem descrever todas as características cadastradas. Esses pontos foram identificados e não transformados em funcionalidades novas nesta fase. A busca documental continua lexical e conservadora.

## E. Atendimento completo

O navegador usou React real → FastAPI TCP em 8005 → agente → Ollama → SQLite fictício. O frontend em 5175 tinha CORS explícito correspondente. Não houve substituição do modelo por simulador.

Uma consulta fictícia de produto retornou evidência e preço no chat em **48,47 s**, com foco preservado no campo. A consulta comum de política falhou em **67,78 s**; uma tentativa direcionada adicional também falhou em **76,90 s**. Portanto, exibição de referências documentais com inferência real no chat **não foi homologada**; a CLI real e os testes determinísticos de referências são evidências distintas.

Cancelamento no navegador: alerta de interrupção, foco no campo e nova pergunta pessoal respondida após liberar a vaga. Nenhuma exceção JavaScript foi observada nesse ensaio. Não se afirma interrupção instantânea de toda computação interna do Ollama ou de uma thread SQLite já iniciada.

Foi acrescentado `backend/testes/servidor_homologacao.py` para reproduzir a demonstração sem dados privados: bancos, políticas e autorizações fictícias em diretório temporário, agente e modelo reais, somente loopback. Um teste verifica que caminhos operacionais configurados no ambiente não são usados nem alterados por esse servidor. Não é uma funcionalidade operacional nova.

## F. Qualidade

Critérios explícitos usados, sem autoavaliação do modelo:

| Critério | Regra de aprovação | Resultado |
| --- | --- | --- |
| Fato comercial | Igual à fonte selecionada; preço em centavos correto | Aprovado em parte dos cenários |
| Fundamentação | Evidências existentes; combinado exige ambas as fontes | Proteção mantida; combinado falhou funcionalmente |
| Políticas | Trecho correspondente e página original | Fontes/CLI aprovadas; chat real pendente |
| Promoção | Não inferir vigência/data | Ferramenta correta; inferência falhou |
| Clareza/idioma | Texto determinístico em português, sem raciocínio livre | Saídas confirmadas adequadas; falhas sem utilidade comercial |
| Ambiguidade/ausência | Esclarecer/abster-se sem inventar | Cobertura conservadora; seleção ainda instável |
| Segurança | Nenhuma capacidade adicional nem dados pessoais | Aprovado nos cenários executados |
| Repetibilidade/latência | Repetir resultados corretos dentro dos limites | Não comprovado; tempos altos e falhas |

As recusas não foram contadas como respostas comerciais corretas. A ausência de invenção preserva segurança, mas não resolve a necessidade do cliente quando havia evidência suficiente.

## G. Desempenho

RAM física medida: **15,37 GiB**. Uma amostra durante o modelo carregado indicou **1,67 GiB livres**. `/api/ps` informou aproximadamente **3,62 GiB** para o modelo/contexto de 8192 tokens e zero VRAM. Esses números não constituem medição de pico nem mínimo universal.

Os tempos de tabelas são medições de parede das operações identificadas. Ferramentas são muito mais rápidas que as requisições com modelo, mas isso não identifica isoladamente todo custo da geração. As execuções foram sequenciais por canal; não houve benchmark controlado de CPU/GPU, disco frio ou carga concorrente. Processos de desenvolvimento e do navegador podem afetar as medições.

Na inferência simples aprovada, a API informou 174 tokens gerados, **10,619 s** de avaliação de saída, **0,247 s** de avaliação do prompt e **0,005 s** de carga. A carga é de modelo já aquecido, não inicialização fria. O cancelamento observado no cliente não prova liberação instantânea da memória ou interrupção de toda computação interna no servidor.

Tempo de inicialização completo do projeto e uso percentual/pico de CPU não foram instrumentados de forma confiável. Não foram inventadas estimativas. Nenhum limite de segurança foi removido para reduzir latência.

## H. Segurança

Auditoria cobriu arquivos rastreados e novos não ignorados, comparados localmente a valores privados e linhas documentais. Nenhuma cópia foi encontrada no escopo da varredura. Foi excluída apenas a localização pública já presente na apresentação original. O procedimento não é uma prova universal contra todo vazamento.

`data/` e `.local/` continuam ignorados, sem arquivos rastreados nesses diretórios. CSVs, PDF, bancos e autorizações reais não foram modificados. Não houve publicação automática de evidência real; os testes web usaram somente autorização fictícia. A CLI com fontes reais não persistiu transcrições.

API TCP real: **429** com `Retry-After=2` durante consulta ativa, **403** para Origin recusada, **413** para corpo excessivo e **404** para clientes. Regressões adicionais verificam peer externo mesmo com Host/Origin locais e `X-Forwarded-For` falsificado, e leitura lenta com **408** antes de ocupar o agente.

Um lote final de requisições inválidas também atingiu o limite real de frequência e recebeu **429**, sem invocar o modelo. A proteção padrão permite 20 requisições/minuto por IP nas rotas de atendimento e uma consulta ativa por processo; consultas de disponibilidade também consomem essa janela. Após encerrar o Ollama próprio, a API permaneceu disponível, informou `modelo=indisponivel`/`homologacao=pendente`, e a interface mostrou indisponibilidade e erro com foco preservado. Essa separação foi observada, não simulada.

Whitelist, validação de argumentos, somente leitura, limites de repetição/contexto/tempo e validação final de evidências permaneceram intactos. Os logs da aplicação contêm operação, ferramenta, duração e categoria de erro, não pergunta, prompt ou fonte integral. O processo Ollama permaneceu sem logs de corpo habilitados e sem nuvem.

## I. UX e acessibilidade

Chat clássico preservado, sem redesenho. Foi reproduzida uma falha de foco após envio por botão seguido de erro: o teste inicialmente falhou. A correção devolve o foco ao campo ao enviar, repetir e interromper; o teste passou e integra a regressão.

Edge headless com perfil isolado: navegação por Tab, Shift+Enter com quebra de linha, envio por Enter, nova conversa e foco, cancelamento, temas e árvore de acessibilidade. A árvore expôs textbox com label, heading e região log. Isso verifica semântica disponível ao navegador, **não é um teste com leitor de tela**. NVDA não foi encontrado nos dois caminhos usuais consultados; isso não prova ausência de todo leitor possível.

Inspeção de layout e estados em larguras de 320, 390, 430, 768 e 1440 px, incluindo 390 × 460, confirmou cabeçalho, entrada e envio visíveis, balões por remetente e ausência de excesso horizontal. Isso complementou a regressão automatizada existente de rolagem e Visual Viewport. Teclado físico, leitor de tela e celular físico permanecem pendentes. O histórico continua visual, sem memória contextual ou armazenamento persistente de mensagens.

## J. Testes

Resultado da suíte independente de modelo: **281 aprovados, nove homologações reais optativas puladas**. Ruff check/format aprovados, 72 arquivos com formatação válida; `pip check` aprovado. Permanece um aviso de depreciação do TestClient/httpx, já existente.

Frontend com FastAPI real: **45 aprovados**, sem pulados, incluindo duas integrações HTTP. TypeScript, ESLint, Prettier e build aprovados. Os testes anteriores foram preservados. Nenhuma falha da matriz real foi escondida alterando a suíte comum ou retirando validações.

Comandos e condições de ativação estão no [guia de execução](../entrega/execucao-local.md). Artefatos XML/JSON/capturas ficaram em armazenamento ignorado. O ensaio de JSON com orçamento efetivo foi repetido isoladamente; a matriz comercial não foi declarada aprovada por causa dessa repetição.

## K. Documentação

README revisado para distinguir o diagnóstico histórico da Fase 4 do Ollama realmente encontrado e do endpoint acrescentado na Fase 5. Criados guia de execução/instalação/demonstração e checklist dos requisitos documentados. Mantidos os comandos de importação, indexação, CLI e API `emporio_ia.principal:aplicacao`, limites, confidencialidade e declaração de assistência de desenvolvimento.

Não foi encontrado um enunciado original separado do desafio no checkout; a checklist identifica essa limitação e não inventa critérios da avaliação externa. As versões/condições de licença relevantes foram registradas sem conceder licença nova ao projeto ou dados.

Referências primárias consultadas: [chat Ollama](https://docs.ollama.com/api/chat), [Qwen3-4B e licença](https://huggingface.co/Qwen/Qwen3-4B), [template oficial Qwen3](https://huggingface.co/Qwen/Qwen3-4B/raw/main/tokenizer_config.json) e [configuração do caminho Go](https://github.com/ollama/ollama/blob/main/envconfig/config.go). A comparação de caminhos é um diagnóstico local; não se afirma que a documentação ou uma issue externa prove a causa exata desta instalação.

## L. Git

Branch `main` preservada, sem operações destrutivas, staging, commit, push, release ou deploy. Alterações para revisão: foco do frontend e regressão; testes HTTP adicionais; suíte optativa real; servidor fictício e teste de isolamento; README, arquitetura, guia, checklist e este relatório. Arquivos operacionais continuam ignorados.

A comparação final confirmou os **nove arquivos privados originais com os mesmos hashes**. A varredura do checkout não encontrou cópias no escopo auditado, e `git diff --check` passou. Os servidores e o navegador isolados de validação foram encerrados; nenhum serviço preexistente foi parado, pois o Ollama começou desligado.

Sugestão de commit, não executado: `test: homologa agente e atendimento integrado`. A descrição do eventual commit deve explicitar homologação parcial e falhas do modelo, sem sugerir aprovação integral.

## M. Pendências

1. Estabilizar geração/chamadas nativas e repetir toda a matriz comercial, principalmente preço, promoções, políticas e combinação. Investigar o tratamento de raciocínio/template nesta versão, sem reduzir validações.
2. Comprovar política com página correta no navegador em perguntas comuns e repetidas; revisar construção de consultas lexicais.
3. Medir repetibilidade, latência e limites em condições controladas após corrigir o comportamento funcional.
4. Completar leitor de tela, teclado físico e celular físico; obter o enunciado original para revisar a aderência externa.
5. Revisar explicitamente qualquer evidência real antes de futura divulgação. Não aprovar manifesto operacional automaticamente para demonstrar funcionamento.

## N. Recomendação

**Bloqueado para declarar a Fase 6 integralmente homologada e o atendimento pronto para uso real.** Produto, consultas, preços e políticas têm evidências reais de funcionamento pontual, e a regressão independente está aprovada. Entretanto, a matriz real ainda contém falhas comerciais e o chat documental não foi homologado. Entregar o código para revisão com estas ressalvas é possível; certificar atendimento confiável ou omitir as falhas não é sustentado pelas evidências.
