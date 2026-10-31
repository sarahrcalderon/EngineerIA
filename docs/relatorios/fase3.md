# Relatório técnico — Fase 3

Data: 31/10/2026. Escopo: extração, indexação e recuperação local das políticas.

## A. Diagnóstico

Branch `main`, working tree inicialmente limpa, no commit `6480448` da Fase 2. Antes das mudanças, os 117 testes anteriores e Ruff lint/format passaram. `data/` e `.local/` estavam ignoradas, sem fontes ou bancos rastreados. Os arquivos originais e o banco operacional foram registrados por SHA-256 em inventários temporários fora do repositório para comparação final.

O SQLite local é 3.43.1. O suporte a FTS5 foi confirmado criando uma tabela virtual em memória. Não houve necessidade de alternativa de busca ou instalação de serviço externo. A única biblioteca adicionada foi pypdf 6.21.4, com licença BSD-3-Clause confirmada nos metadados instalados.

## B. Documento

O PDF existe, pode ser lido e não é criptografado. Possui oito páginas, todas com texto extraível, sem páginas vazias na inspeção. A extração padrão fragmentava muitas palavras em linhas isoladas; a extração em modo `layout` organizou melhor linhas e separadores de parágrafos, com candidatos a títulos numerados.

Foi comparada por página a frequência dos caracteres não brancos nos modos padrão e layout: todas as oito páginas preservaram o mesmo conjunto de caracteres e respectivas contagens. Essa verificação não comprova ordem semântica perfeita nem substitui revisão visual de tabelas ou regras. Não houve OCR, renderização online, cópia ou publicação de texto. Nenhuma política real é reproduzida neste relatório.

## C. Arquitetura

Domínio: entidades documentais, normalização, segmentação, termos e validações, sem dependências de PDF ou banco. Aplicação: `IndexadorPoliticas` e `ServicoRecuperacao`, dependentes de contratos de extração e índice. Infraestrutura: `ExtratorPdf`, `RepositorioTrechos` e persistência FTS5. Composição: CLI local `emporio_ia.indexar_politicas`.

O índice documental é independente das consultas de produtos e pedidos. Nenhuma rota documental foi criada. O [documento arquitetural](../arquitetura/recuperacao-documental.md) e a [ADR 0003](../decisoes/0003-recuperacao-documental.md) detalham as responsabilidades.

## D. Extração

Leitura binária local e processamento em memória dos mesmos bytes usados para SHA-256. Extração por página com pypdf em modo `layout` e leitura estrita; preservação da numeração física a partir de 1. Normalização NFC e espaços controlados, preservando pontuação, acentos e valores.

Páginas isoladas vazias são preservadas como metadados e não geram trechos. Um PDF inteiro sem texto produz erro e não instala OCR automaticamente. Arquivos ausentes, ilegíveis, corrompidos ou criptografados geram mensagens sanitizadas. Logs do parser são suprimidos para não expor objetos documentais. Limites locais: 20 MiB e 500 páginas.

## E. Segmentação

Parágrafos e títulos heurísticos são priorizados, sem cruzar páginas. Limite padrão de 1200 caracteres, configurável entre 200 e 10000. Parágrafos longos são divididos entre frases; uma unidade maior que o limite causa erro, em vez de corte ou truncamento. Não há sobreposição.

Os metadados incluem documento, página, seção quando identificada, texto, ordem global, início/fim na página normalizada, hash do conteúdo e identificador determinístico. A seção é inferida por estrutura textual, sem garantia de classificação semântica. Sua continuidade entre páginas é preservada quando aplicável.

O PDF local resultou em 75 trechos. Todos foram conferidos por igualdade com o intervalo correspondente da página normalizada. Identificadores permanecem estáveis na reindexação da mesma origem e configuração. Testes sintéticos verificam cobertura textual, numeração e preservação de valores.

## F. Indexação

Índice em `.local/politicas.sqlite3`, separado de `.local/emporio.sqlite3`. Contém documentos, trechos e tabela virtual FTS5 com `unicode61 remove_diacritics 2`. Texto e seção são confidenciais; termos derivados também permanecem apenas no banco privado.

`application_id` valida a identidade do arquivo e `user_version` controla a versão do esquema. Banco operacional ou arquivo não vazio de identidade desconhecida é recusado antes da escrita. A configuração também impede caminhos iguais.

Uma transação abrange DDL, limpeza e inserção de metadados, trechos e índice. Falhas fazem rollback. O teste provoca erro após inserções parciais e confirma que a busca anterior permanece disponível. Outro teste verifica que falha na extração não apaga o índice.

Hash do PDF e assinatura do processamento detectam mudanças na origem ou parâmetros. A reindexação real, também executada a partir de `backend/`, manteve oito páginas e 75 trechos e informou `alterado=false`. A identidade é por conteúdo, não por bytes do arquivo SQLite. Integridade do índice e referências passaram nas verificações SQLite. Não há monitoramento automático da origem.

## G. Recuperação

O serviço recebe pergunta e limite, normaliza caixa e acentos, remove termos comuns e trata algumas terminações de plural. Exige todos os termos significativos no mesmo trecho ou na seção, evitando promover correspondências parciais fracas. Perguntas apenas genéricas, numéricas ou sem correspondência retornam lista vazia.

Consultas usam parâmetros SQL e termos literais, sem aceitar sintaxe SQL ou MATCH do chamador. Resultados seguem BM25 crescente, página e ordem, com remoção de conteúdo repetido antes do limite final. Cada evidência inclui texto, página, seção, identificadores, posições, hash do conteúdo, hash do PDF e pontuação lexical.

Foram exercitadas buscas locais com correspondência e sem evidência, sem imprimir conteúdo. As páginas e os offsets foram conferidos contra a extração da mesma versão. Testes sintéticos verificam perguntas relacionadas e não relacionadas, acentos, caixa, plurais, ranking e limites.

Limitações: sem sinônimos, embeddings ou semântica. A exigência conjuntiva pode rejeitar perguntas respondíveis por paráfrases ou informações distribuídas entre blocos. Ausência de evidência recuperada não prova ausência da política. BM25 não representa probabilidade de certeza. O mecanismo fornece evidências e não respostas geradas.

## H. Segurança

- PDF e seis CSVs permaneceram com os hashes SHA-256 originais.
- O banco operacional permaneceu binariamente idêntico por SHA-256.
- Fontes, índice, journals, WAL e SHM estão ignorados; staging vazio.
- Não houve texto real em fixtures, exemplos de políticas ou logs.
- A extração não cria arquivos temporários de conteúdo em disco.
- Erros e a CLI não reproduzem texto, valores internos ou caminhos.
- Entidades documentais não incluem conteúdo em sua representação textual padrão.
- A API continua sem rotas de políticas, documentos, trechos ou índice.
- Nenhum arquivo foi enviado para serviço externo; nenhuma operação de publicação ocorreu.

O índice não é criptografado e depende das permissões locais, assim como o banco operacional. Ignore do Git não substitui controle de acesso nem impede adição forçada. O futuro agente deverá tratar texto recuperado como dados não confiáveis, sem autoridade de instrução.

## I. Testes e validações

| Verificação executada                                   | Resultado                                                                                      |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `python -m pytest backend/testes` pelo ambiente virtual | 172 testes passaram: 117 anteriores e 55 documentais                                           |
| `ruff check backend`                                    | Aprovado                                                                                       |
| `ruff format --check backend`                           | Aprovado                                                                                       |
| CLI real de indexação e reindexação em outro diretório  | Oito páginas, zero vazias, 75 trechos; sem duplicação                                          |
| Origem dos 75 trechos                                   | Offsets e texto conferidos                                                                     |
| SQLite FTS5 e integridade do índice                     | Aprovados                                                                                      |
| SHA-256 das fontes e banco operacional                  | Preservados                                                                                    |
| Importador de CSV e consultas da Fase 2                 | Suíte sintética anterior preservada e aprovada                                                 |
| Inicialização da aplicação atual e saúde HTTP           | HTTP 200, resposta original preservada                                                         |
| OpenAPI                                                 | Apenas `/api/saude` declarado                                                                  |
| CORS local                                              | Origem explícita preservada                                                                    |
| `npm.cmd run typecheck`                                 | Aprovado                                                                                       |
| `npm.cmd run lint`                                      | Aprovado                                                                                       |
| `npm.cmd run format:check`                              | Aprovado                                                                                       |
| `npm.cmd run build`                                     | Aprovado                                                                                       |
| Vitest com integração real                              | Seis testes passaram; integração também verificada contra instância isolada da aplicação atual |
| Git ignore de PDF, índice e journals                    | Verificado                                                                                     |

O pytest mantém um aviso de depreciação do transporte httpx no TestClient do Starlette. Não houve inspeção visual em navegador nesta sessão. Não foi repetida auditoria npm; os alertas moderados registrados na Fase 1 permanecem fora deste escopo, sem alteração de dependências frontend. Não foram inventadas métricas de qualidade semântica da recuperação.

## J. Arquivos

Criados:

- `dominio/documentos.py`, `dominio/segmentacao.py` e `dominio/busca_documental.py`.
- `aplicacao/documentos.py`.
- `infraestrutura/documentos/`: extrator e repositório FTS5.
- `indexar_politicas.py`.
- `backend/testes/documentos/`: gerador de PDFs fictícios, testes de extração, segmentação, índice, recuperação, segurança e CLI.
- Visão documental, ADR 0003 e este relatório.

Atualizados: `backend/pyproject.toml`, lock de dependências Python, configuração central, `.env.example`, README e visão geral da arquitetura. O `.gitignore` existente já protegia todos os novos derivados. Frontend, importador operacional, repositórios anteriores e testes anteriores não foram modificados.

## K. Git

Branch: `main`. Mudanças da Fase 3 permanecem no working tree, sem staging. Nenhum `git add`, commit, push, rebase, mudança de branch ou reescrita de histórico foi executado.

Mensagem sugerida: `feat: implementa recuperacao documental das politicas`.

## L. Próxima fase

Avaliar compatibilidade e desempenho do Ollama local, definir modelo, contratos de ferramentas, orquestração controlada e regras para respostas fundamentadas e ausência de evidência. A camada futura deverá validar permissões para dados pessoais e tratar documentos como fonte de dados não confiáveis. Nada disso foi implementado nesta fase.

As Fases 1, 2 e 3 contaram com assistência de código do OpenAI Codex. A revisão final e a responsabilidade pelo desafio permanecem com a pessoa candidata.
