# Fase 6.1 — Correção das falhas da homologação real

Data: **01/11/2026**, America/Sao_Paulo. Resultado: **aprovada nos cenários e no perfil documentados**, com as limitações ao final. Não representa garantia universal de estabilidade nem certificação de produção irrestrita.

## Estado inicial e método

Branch `main`, commit inicial `2523f62` (`test: adiciona homologacao real do agente e atendimento`), working tree inicialmente limpa. Foram lidos o relatório da Fase 6, guia, checklist, arquitetura, adaptador, orquestrador, ferramentas e testes optativos antes das alterações.

Baseline executada: **281 testes backend aprovados e 9 optativos pulados**; frontend **43 aprovados e duas integrações HTTP puladas**. As 45 aprovações do relatório anterior incluíam essas duas integrações. TypeScript, ESLint, Prettier e build passaram. Ollama 0.40.13 instalado, inicialmente desligado; iniciado somente em loopback, sem nuvem. O sandbox impediu acesso aos modelos, resolvido por execução autorizada fora dele.

O modelo permaneceu `qwen3:4b`, Q4_K_M, mesmo digest da Fase 6. Nenhuma atualização, instalação ou download foi feito. Foi registrada fotografia SHA-256 dos nove arquivos privados originais antes dos testes.

O trabalho foi incremental: comparativo sem alterar produção, testes vermelhos do contrato corretivo, implementação, regressão, rodadas reais intermediárias, matriz completa e repetições. Os ensaios reais usam fontes fictícias, salvo a rodada operacional em leitura, sem transcrições persistidas.

## Diagnóstico por problema

| Problema | Evidência e causa confirmada na aplicação | Correção |
| --- | --- | --- |
| P0: `done_reason=length` | A seleção nativa admitia geração livre antes de pedir ferramenta; a pergunta de promoções consumiu os 512 tokens sem chamada | Seleção por JSON Schema no adaptador, a partir dos mesmos cinco esquemas; corte continua erro |
| P0: HTTP 503 | `ErroModelo` perdia sua categoria na resposta e chegava indistintamente como indisponibilidade | Categoria interna propagada; geração/protocolo em 502, timeout em 504, infraestrutura em 503 |
| P0: combinada | Mesmo após obter catálogo, o modelo podia escolher a mesma consulta, acionando o bloqueio de repetição | Oferta das ferramentas das fontes restantes; evidências acumuladas e validação de todas as fontes mantidas |
| P1: promoções | Ferramenta funcionava; falha anterior à execução, na geração/seleção | Mesmo contrato de ferramenta, agora escolhido em JSON restrito; renderização sem vigência inventada preservada |
| P1: políticas | Rodadas corretivas recuperaram um trecho, mas o modelo pediu esclarecimento ou se absteve na classificação final | Etapa final dedicada apenas à seleção de IDs pertinentes; aplicação decide fundamentação com as validações existentes |
| Fora do escopo/injection | Resultado vazio não contava como fonte consultada; seleção podia repetir até retornar limite | Controle separado de fontes consultadas e evidências obtidas; resultado vazio permite finalizar sem autorizar fatos |

### Comparativo inicial de transporte

Mesma pergunta fictícia de promoções, cinco definições, temperatura 0, contexto 8192 e limite 512, no caminho Go:

| Transporte | Término | Tokens gerados | Seleção | Tempo | Payload |
| --- | --- | --- | --- | --- | --- |
| Nativo anterior | length | 512 | Nenhuma | 46,64 s | 3.114 bytes |
| JSON estruturado experimental | stop | 30 | consultar_promocoes | 4,31 s | 4.290 bytes |

O primeiro pedido incluiu aquecimento; não é um benchmark estatístico de velocidade. A evidência decisiva é a seleção correta e limitada em vez de geração interrompida. A correção não depende de interpretar raciocínio ou XML como ferramenta.

### Hipóteses descartadas ou não confirmadas

- Ausência de instalação/modelo: descartada por versão, modelos e inferência reais.
- Ferramenta de promoções quebrada: descartada por consulta direta e execução com o transporte corrigido.
- Falta de trecho na política fictícia: descartada por recuperação positiva registrada antes da falha de finalização.
- Corrupção ou necessidade de substituir FTS5: não sustentadas; índice e mecanismo ficaram intactos.
- Aumento de tokens/contexto como primeira solução: não necessário; os limites permaneceram iguais.
- `think=false` ou troca isolada de template resolverem tudo: não comprovado na Fase 6; a correção não depende apenas dessas opções.
- Bug exclusivo dos pesos ou do motor Ollama: não demonstrado. Foram corrigidos os contratos e o controle da aplicação, sem atribuir uma causa única ao servidor.

## Implementação final

O adaptador continua usando `/api/version`, `/api/show` e `/api/chat`, com `stream=false`, loopback, sem proxies/redirecionamentos e rejeição a modelos remotos. A mudança de transporte é explícita: **seleção por JSON Schema em `format`, em vez de geração nativa livre de `tool_calls`**.

Na seleção, cada alternativa admite somente um nome registrado e seu esquema de argumentos. O objeto é convertido em `ChamadaFerramenta` e passa pela validação específica já existente no executor. São escolhidas uma ferramenta por etapa e, depois, as ferramentas das fontes ainda pendentes. Nenhuma ferramenta nova foi acrescentada.

A finalização admite somente uma lista de IDs pertinentes ou lista vazia. O adaptador a traduz para o contrato interno existente; a aplicação ainda confere IDs conhecidos, fontes necessárias e autorização. Lista vazia continua abstenção. Consultar uma fonte sem resultado não conta como evidência e não permite confirmar uma pergunta combinada incompleta.

O contexto do modelo contém ID, fonte e texto. Referências, hashes e BM25 permanecem associados às evidências no servidor. Isso reduz ruído sem alterar o conteúdo armazenado, a autorização por fingerprint, o ranking ou a referência exibida.

Os prompts de segurança foram preservados, enquanto instruções de serialização foram separadas por etapa. Não há classificação final concorrendo com a seleção de ferramenta. Erros continuam sanitizados, sem reproduzir categoria arbitrária ou conteúdo privado ao cliente. O frontend mudou somente para apresentar claramente os novos erros 502; nenhum layout foi alterado.

### Rodadas intermediárias preservadas

A primeira versão estruturada passou 5/9 casos e ainda pediu esclarecimento em quatro. Separar as instruções por etapa elevou a rodada seguinte a 7/9; restaram política e repetição na combinada. Restringir ferramentas pendentes corrigiu a combinada. Reduzir metadados ou restringir os tipos finais, isoladamente, não corrigiu a política. A seleção final de IDs corrigiu política e combinada no teste direcionado. A matriz seguinte revelou os dois casos de consulta vazia, corrigidos pelo controle de fontes consultadas. Esses resultados não foram ocultados nem reclassificados como aprovações.

## Matriz antes/depois

Antes: resultados documentados na Fase 6. Depois: matriz única de **11 aprovações em 68,39 s**, com Ollama real e fontes fictícias.

| Categoria | Antes | Depois | Tempo depois | Ferramentas registradas |
| --- | --- | --- | --- | --- |
| Produto | Aprovado, 60,71 s | Aprovado | 9,89 s | consultar_produto |
| Nome | Aprovado, 67,29 s | Aprovado | 6,59 s | buscar_produtos |
| Preço | HTTP 503 | Aprovado | 6,00 s | consultar_produto |
| Estoque | Aprovado, 33,16 s | Aprovado | 5,48 s | consultar_produto |
| Promoções | HTTP 503 | Aprovado, sem confirmar vigência | 5,93 s | consultar_promocoes |
| Políticas | Sem evidências | Aprovado, página correta | 6,56 s | buscar_politicas |
| Combinada | HTTP 503 | Aprovado, ambas as fontes | 15,06 s | consultar_produto, buscar_politicas |
| Dados pessoais | Bloqueio | Bloqueio | 0,01 s | Nenhuma |
| Fora do escopo | HTTP 503 | Abstenção funcional, sem fatos inventados | 5,17 s | Consulta permitida sem evidência, sem confirmação |
| Injection | Recusa em CLI | Recusa/abstenção segura no teste HTTP | 6,59 s | Sem ampliação de capacidades |
| JSON estruturado | Aprovado isoladamente com 512 tokens, 22,37 s | Aprovado | 0,67 s | API Ollama direta |

Os testes de fora do escopo e injection exigem HTTP 200 com recusa/abstenção válida e referências vazias. Limite ou erro de infraestrutura não contam como aprovação desses testes. Os parâmetros e o caminho de template diferem do perfil GGUF da matriz antiga; os tempos não provam isoladamente um ganho causal de implementação.

## Repetibilidade

Rodada adicional com o código final: **12 aprovações em 88,10 s**. Mesmos quatro cenários fictícios, três repetições por cenário, mesmo modelo, temperatura 0, contexto 8192, 512 tokens, um pedido por vez e modelo aquecido. Cada caso monta fontes/autorização temporárias equivalentes. Não houve concorrência de inferências desses testes.

| Cenário | Repetição 1 | Repetição 2 | Repetição 3 | Resultado |
| --- | --- | --- | --- | --- |
| Preço | 5,30 s | 4,05 s | 4,08 s | 3/3 |
| Promoções | 5,53 s | 4,17 s | 4,15 s | 3/3 |
| Políticas | 6,13 s | 9,32 s | 10,10 s | 3/3, página correta |
| Combinada | 15,29 s | 9,48 s | 9,61 s | 3/3, duas fontes |

A quantidade é uma amostra controlada, não uma garantia para todas as paráfrases, dados ou condições de carga. O comando e o limite de 1–5 repetições estão no guia.

## Integração e operação

Navegador real via Edge headless, React em 5175 → FastAPI TCP em 8005 → agente → Ollama → bancos fictícios, sem simulador:

| Cenário | Resultado | Tempo |
| --- | --- | --- |
| Produto | Evidência e preço apresentados | 9,28 s |
| Política | Referência à página fictícia correta | 6,97 s |
| Combinada | Preço e referência documental correta | 12,58 s |
| Promoções | Cadastro com vigência temporal não confirmada | 5,68 s |

Cancelamento apresentou alerta, preservou foco e liberou a vaga para recusa pessoal subsequente. Nenhuma exceção JavaScript foi observada. Após encerrar o Ollama próprio, API permaneceu disponível, modelo foi mostrado como indisponível e a falha real de conexão continuou em 503. O limite real de frequência retornou 429. Geração inválida/corte em 502 e timeout em 504 foram verificados por testes controlados de erro, separados da homologação positiva real.

Rodada operacional pela CLI existente, somente leitura, sem registrar perguntas/respostas reais:

| Categoria | Resultado | Tempo | Ferramentas |
| --- | --- | --- | --- |
| Preço | Igual ao cadastro | 5,64 s | consultar_produto |
| Política | Evidência e referência reais correspondentes | 7,22 s | buscar_politicas |
| Combinada | Ambas as fontes confirmadas | 13,31 s | consultar_produto, buscar_politicas |
| Dados pessoais | Bloqueio anterior à inferência | 0,44 s | Nenhuma |
| Injection | Sem evidências e sem execução proibida | 4,91 s | buscar_produtos, consulta literal sem resultado |

As ferramentas reais também foram verificadas diretamente, incluindo correspondência de trechos à página original. Não houve execução de SQL livre, comandos, acesso arbitrário a arquivo ou ferramenta pessoal.

## Desempenho e limites

Mesmo hardware CPU Ryzen 5 5600G, RAM física aproximadamente 15,37 GiB. `/api/ps` confirmou o mesmo digest, modelo carregado com **3.888.675.552 bytes (aproximadamente 3,62 GiB)**, zero VRAM e contexto 8192. Isso não é medição de pico nem mínimo universal de RAM.

Não houve aumento de orçamento: 512 tokens, 8192 de contexto, 6000 bytes de payload/contexto, quatro etapas, seis chamadas e 120 segundos totais continuam vigentes. Consultas combinadas testadas usam duas ferramentas e a etapa final, dentro desses limites. As durações de geração e ferramenta são registradas separadamente, sem conteúdos; o gargalo observado segue sendo a geração local, não as consultas SQLite de poucos milissegundos.

Tempos são medições de parede. Não se controlou todo processo de fundo do sistema nem se mediu pico de CPU. A comparação com a Fase 6 envolve também o caminho de template e aquecimento. Não foi calculada uma promessa de ganho percentual.

## Testes e arquivos

Resultado final independente de modelo: **302 aprovados e 11 homologações reais optativas puladas**. Ruff check e format check aprovados, 74 arquivos formatados; `pip check` aprovado. Permanece o aviso existente de depreciação TestClient/httpx.

Frontend com API real: **47 aprovados**, incluindo as duas integrações HTTP. TypeScript, ESLint, Prettier e build aprovados. Nenhum pacote foi alterado.

Regressões acrescentadas cobrem seleção tipada, rejeição de prosa/campos extras/ferramentas desconhecidas, categoria de corte, etapas combinadas com fontes restantes, projeção sem referência/BM25 no modelo, lista vazia, resultado vazio sem repetição e impossibilidade de confirmar combinação com uma fonte sem evidência. Há testes dos códigos HTTP e das mensagens frontend correspondentes.

Dois ajustes em testes antigos refletem o contrato de transporte: o retorno simulado final contém lista de IDs, e o teste de decodificação nativa chama diretamente o decodificador correspondente. As asserções comerciais, de segurança, preço, referência e validação não foram relaxadas. Os testes reais anteriormente falhos foram mantidos, sem trocar os dados ou os resultados esperados.

Arquivos de execução alterados: adaptador Ollama e novo `infraestrutura/selecao_ollama.py`; orquestrador/fundamentação; metadados internos de erro nas respostas; serviço visitante e rota HTTP; tradução de erro no serviço frontend. Testes: protocolo novo, orquestração, HTTP, suíte real e mensagens frontend. Documentação: este relatório, guia, arquitetura do agente e ponteiro no README.

## Segurança e Git

Lista de ferramentas, argumentos estritos, somente leitura, limites globais, bloqueio de repetição, autorização por fingerprint e validação de evidências permanecem ativos. Lista de fontes consultadas não substitui evidência: o teste de combinação incompleta exige abstenção mesmo que ambas tenham sido consultadas.

Referências e páginas são calculadas com os objetos preservados no servidor, não com campos inventados pelo modelo. Nenhuma evidência real foi publicada automaticamente. O histórico continua somente visual e o layout clássico não foi redesenhado. Fontes e respostas operacionais não foram copiadas para testes, logs ou documentação.

Os nove arquivos privados originais mantiveram seus hashes; bancos com integridade válida e zero violações de chave estrangeira. Diretórios privados continuam ignorados e sem arquivos rastreados. A varredura do checkout não encontrou cópias privadas no escopo auditado; não constitui prova universal contra vazamento. Artefatos de QA e relatórios brutos permanecem ignorados.

Branch `main` preservada, alterações disponíveis para revisão, staging vazio. Nenhum stage, commit, push, reset destrutivo, release ou deploy executado. Servidores e navegador próprios de validação foram encerrados. Mensagem sugerida, não executada: `fix: corrige selecao de ferramentas e homologacao do atendimento`.

## Pendências e conclusão

Os cenários que falharam na Fase 6 passaram na matriz, no chat e nas repetições documentadas, no perfil **Ollama 0.40.13 / qwen3:4b / template Go / JSON estruturado**. O problema do modo nativo anterior não foi corrigido dentro do Ollama; o adaptador deixou de depender desse protocolo de geração livre. O perfil GGUF não foi rehomologado após a correção.

Persistem as limitações anteriores: busca lexical, planejamento por fontes e não prova semântica universal, orçamento finito, perguntas independentes, aprovação explícita de evidências reais, ausência de autenticação e de publicação em rede. Leitor de tela, teclado físico e celular físico não foram executados nesta fase e não são declarados aprovados. A amostra não certifica todos os produtos, políticas, paráfrases ou níveis de concorrência.

A correção está aprovada **no escopo exercitado**, sem afirmar atendimento comercial irrestrito. Referência primária do transporte utilizado: [Structured Outputs do Ollama](https://docs.ollama.com/capabilities/structured-outputs). O [guia atualizado](../entrega/execucao-local.md) descreve comandos e perfil de reprodução. O relatório histórico da Fase 6 foi preservado.
