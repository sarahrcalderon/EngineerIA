# engineerIA

Fundação técnica de um assistente de atendimento para a loja fictícia Empório da Música, de Campo Grande/MS, no contexto do desafio de AI Engineer da Artefact.

A Fase 1 entrega uma API de saúde e uma interface que verifica sua disponibilidade. A Fase 2 acrescenta importação local de CSVs, persistência SQLite e serviços internos de catálogo e pedidos. A Fase 3 acrescenta extração local do PDF, segmentação e recuperação lexical de evidências. A Fase 4 implementa um agente interno com adaptador Ollama, ferramentas de leitura e respostas extrativas verificáveis por CLI. Não há chat visual, autenticação ou exposição dos dados por HTTP.

## Tecnologias e decisões

- Python 3.12+, FastAPI, Pydantic e Uvicorn: contratos tipados, validação e documentação OpenAPI automática.
- React, TypeScript e Vite: interface em componentes e verificação estática.
- Tailwind CSS e Lucide React: composição visual e ícones locais, sem serviços externos.
- pytest, Ruff, Vitest, Testing Library, ESLint e Prettier: verificações automatizadas.
- `fetch` nativo: comunicação HTTP sem dependência adicional.
- `pydantic-settings`: configuração tipada por variáveis de ambiente.
- `sqlite3`, `csv` e `decimal` da biblioteca padrão: persistência, importação e conversões monetárias exatas, sem novas dependências.
- `pypdf` (BSD-3-Clause) e SQLite FTS5: extração e busca documental local. `pypdf` é a única dependência adicionada na Fase 3.
- `httpx`: comunicação assíncrona com Ollama. A biblioteca, já utilizada nos testes, passa a ser dependência de execução na Fase 4; não há SDK de agente ou nova versão de pacote no lock.

Todas as ferramentas necessárias à execução local são gratuitas. Não é necessário Docker nem provedor de IA. As versões efetivamente resolvidas estão em `frontend/package-lock.json` e `backend/requirements-dev.lock`.

## Arquitetura e estrutura

```text
backend/
  src/emporio_ia/
    api/                 # rotas, esquemas e dependências HTTP
    dominio/             # entidades, filtros, conversões e exceções
    aplicacao/           # contratos e serviços internos de catálogo/pedidos
    infraestrutura/      # CSV, importação, esquema, conexões e repositórios
    importar.py          # comando local de importação
    indexar_politicas.py  # comando local de indexação documental
    conversar.py         # CLI do agente, sem histórico persistido
    configuracao.py      # ambiente e CORS
    principal.py         # fábrica da aplicação e erros
  testes/                # regressão HTTP e dados operacionais sintéticos
  pyproject.toml
frontend/
  src/
    componentes/         # indicador de conexão
    estilos/             # identidade visual e responsividade
    servicos/            # fetch e contrato de saúde
    testes/              # estados da interface
    tipos/               # contrato TypeScript
    App.tsx
docs/
  arquitetura/visao-geral.md
  arquitetura/dados-operacionais.md
  arquitetura/recuperacao-documental.md
  arquitetura/agente-local.md
  decisoes/0001-arquitetura-inicial.md
  decisoes/0002-persistencia-operacional.md
  decisoes/0003-recuperacao-documental.md
  decisoes/0004-agente-local.md
data/                    # confidencial, local, ignorado pelo Git
.local/                  # banco confidencial e artefatos locais, ignorados
```

A fábrica `criar_aplicacao` recebe configurações e disponibiliza a instância por dependência FastAPI. A interface consulta apenas `GET /api/saude`, com limite de cinco segundos, cancelamento ao desmontar e nova tentativa manual em caso de falha. A resposta é validada também em tempo de execução. Os serviços operacionais dependem de contratos; repositórios SQLite implementam esses contratos. A API não instancia esses serviços nem acessa o banco.

## Pré-requisitos

- Windows com PowerShell, Python 3.12+ e Node.js 22.12+ (validado com Node 24).
- SQLite 3.37+ no módulo `sqlite3` do Python, para tabelas `STRICT`, com suporte a FTS5 (verificado localmente em SQLite 3.43.1).
- npm e acesso à internet para instalar dependências.
- Git para inspeção do repositório.

Os comandos usam `npm.cmd` para funcionar também quando a política do PowerShell bloqueia `npm.ps1`. Não é necessário ativar o ambiente virtual.

## Instalação

Na raiz do repositório:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.lock
backend/.venv/Scripts/python.exe -m pip install --no-deps -e ./backend
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env.local
cd frontend
npm.cmd ci
cd ..
```

Para atualizar intencionalmente dependências Python, use `pip install -e './backend[dev]'` no ambiente virtual e revise o lock antes de substituí-lo.

## Execução no Windows

Terminal 1, na raiz:

```powershell
backend/.venv/Scripts/python.exe -m uvicorn emporio_ia.principal:aplicacao --app-dir backend/src --env-file .env --reload --no-access-log
```

Terminal 2:

```powershell
cd frontend
npm.cmd run dev
```

Interface: `http://127.0.0.1:5173`. OpenAPI: `http://127.0.0.1:8000/docs`.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/saude
```

Resposta HTTP 200:

```json
{
  "estado": "disponivel",
  "servico": "Emporio IA",
  "versao": "0.1.0"
}
```

## Ambiente

| Variável                  | Local              | Uso                                             |
| ------------------------- | ------------------ | ----------------------------------------------- |
| `EMPORIO_AMBIENTE`        | backend            | `desenvolvimento`, `teste` ou `producao`        |
| `EMPORIO_ORIGENS_CORS`    | backend            | Lista JSON de origens HTTP explícitas           |
| `EMPORIO_DIRETORIO_DADOS` | backend/importador | Diretório dos CSVs; padrão `data/` da raiz      |
| `EMPORIO_CAMINHO_BANCO`   | backend/importador | Banco dedicado; padrão `.local/emporio.sqlite3` |
| `VITE_API_URL`            | frontend           | URL base da API; obrigatória para conexão       |

O Uvicorn recebe `.env` explicitamente por `--env-file`; `python-dotenv`, usado por essa opção, integra o conjunto de dependências de configuração. O Vite lê `frontend/.env.local`. Reinicie os serviços após alterar ambiente. CORS é independente do nome do ambiente: configure as origens adequadas em cada instalação, sem curingas. Credenciais não são permitidas por CORS nesta fase. Variáveis `VITE_*` são públicas e nunca devem conter segredos.

O importador lê o ambiente do processo e as flags abaixo; ele não carrega `.env` automaticamente. Caminhos relativos de dados e banco são ancorados na raiz do projeto, independentemente do diretório atual do terminal. O banco deve terminar em `.sqlite`, `.sqlite3` ou `.db`.

A indexação segue a mesma regra de ambiente e caminhos. Configure `EMPORIO_CAMINHO_PDF_POLITICAS` (padrão `data/políticas_da_loja.pdf`), `EMPORIO_CAMINHO_INDICE_POLITICAS` (padrão `.local/politicas.sqlite3`) e `EMPORIO_TAMANHO_MAXIMO_TRECHO` (padrão 1200 caracteres, entre 200 e 10000). Índice e banco operacional devem ter caminhos distintos. As configurações e a identidade interna do índice recusam o uso acidental do banco operacional.

## Recuperação documental — Fase 3

Após atualizar o ambiente com `backend/requirements-dev.lock`, execute na raiz:

```powershell
backend/.venv/Scripts/python.exe -m emporio_ia.indexar_politicas
```

Para escolher caminhos e tamanho:

```powershell
backend/.venv/Scripts/python.exe -m emporio_ia.indexar_politicas --pdf data/políticas_da_loja.pdf --indice .local/politicas.sqlite3 --tamanho-maximo 1200
```

O comando lê o PDF localmente e emite somente estado, quantidade de páginas, páginas sem texto, trechos e indicador de alteração. Não imprime políticas ou caminhos. Não carrega `.env` automaticamente; flags prevalecem sobre variáveis do processo. Pode ser invocado de outro diretório usando o caminho absoluto do Python do ambiente virtual.

A extração usa `pypdf` em modo `layout`, mantendo a numeração original das páginas. Espaços são normalizados sem remover acentos, pontuação, preços ou prazos. Não há OCR: um PDF sem texto exige avaliação de uma solução local e autorização antes de introduzi-la. Páginas isoladas sem texto mantêm sua posição e não geram trechos. PDFs corrompidos ou protegidos por senha produzem erros sanitizados.

Os trechos respeitam páginas e parágrafos, com divisão de parágrafos longos entre frases. Não há sobreposição. Uma frase maior que o limite causa erro para que o limite seja revisto, em vez de truncá-la. Metadados incluem identificador estável, página, seção inferida quando identificável, ordem, offsets no texto normalizado e hash do conteúdo.

O índice FTS5 fica separado em `.local/politicas.sqlite3`. A reindexação substitui o conteúdo numa transação, sem duplicações. SHA-256 do PDF e assinatura da extração/segmentação/busca detectam alterações; falhas provocam rollback e preservam o índice anterior. O comando reconstrói o índice mesmo quando não há alteração; o indicador informa mudança da origem ou parâmetros, não identidade binária do SQLite. Não há monitoramento automático: reexecute o comando após atualizar o PDF ou as configurações.

`ServicoRecuperacao.recuperar_politicas(pergunta, limite=5)` retorna evidências com `TrechoDocumento`, hash do PDF e pontuação BM25. A composição interna usa `RepositorioTrechos(BancoSQLite(configuracao.caminho_indice_politicas))`, sem dependência da implementação concreta na aplicação. Os testes em `backend/testes/documentos/` mostram a utilização exclusivamente com documentos fictícios.

A busca ignora caixa e acentos, remove uma lista explícita de termos comuns e normaliza algumas terminações de plural. Exige todos os termos significativos no mesmo trecho ou em sua seção. Consultas apenas genéricas, numéricas ou sem correspondência retornam lista vazia. Esse filtro conservador rejeita correspondências parciais fracas, mas pode perder evidências existentes. Ausência de recuperação não prova ausência de uma política no documento. Não há sinônimos, embeddings, compreensão semântica ou geração de resposta. BM25 é ordenação lexical, não probabilidade de certeza. O limite aceito é de 1 a 20 evidências, após remover repetições de conteúdo.

Detalhes e limitações estão em [recuperação documental](docs/arquitetura/recuperacao-documental.md) e na [ADR 0003](docs/decisoes/0003-recuperacao-documental.md).

Exemplo de composição interna, depois de indexar, sem imprimir evidências confidenciais:

```python
from emporio_ia.aplicacao.documentos import ServicoRecuperacao
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos

configuracao = ConfiguracaoAplicacao()
repositorio = RepositorioTrechos(BancoSQLite(configuracao.caminho_indice_politicas))
servico = ServicoRecuperacao(repositorio)
evidencias = servico.recuperar_politicas("trocas", limite=5)
```

A pergunta do exemplo é apenas um termo de busca; o código não pressupõe uma regra comercial ou resposta específica.

## Agente local — Fase 4

O núcleo usa o modelo para solicitar ferramentas nativas e selecionar identificadores de evidências. A aplicação executa somente ferramentas autorizadas, valida os argumentos e monta a resposta a partir de campos cadastrados e citações recuperadas. Texto comercial livre do modelo não é exibido. Essa restrição permite verificar os fatos apresentados sem depender de uma autodeclaração de fundamentação pelo LLM.

As cinco ferramentas são `buscar_produtos`, `consultar_produto`, `consultar_categorias`, `consultar_promocoes` e `buscar_politicas`. Não há ferramentas de clientes, pedidos, SQL, arquivos, comandos ou escrita. Descrições e especificações livres dos produtos não são enviadas ao modelo; a projeção contém nome, categoria, preço e disponibilidade. Promoções mostram o indicador cadastrado, com vigência temporal explicitamente não confirmada. Políticas preservam página, hash e identificador do trecho; BM25 serve apenas à ordenação lexical.

### Instalação e avaliação do Ollama

Instale o aplicativo pelo [site oficial para Windows](https://ollama.com/download/windows), seguindo a [documentação oficial](https://docs.ollama.com/windows). O projeto não instala Ollama nem baixa modelos automaticamente. Além do espaço do aplicativo, é necessário reservar espaço para os pesos e memória adicional para contexto e execução.

O preferencial configurado é `qwen3:4b`: a [distribuição Ollama](https://ollama.com/library/qwen3:4b) tem aproximadamente 2,5 GB e declara suporte a ferramentas; o [modelo oficial Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) usa Apache-2.0. O download não equivale ao consumo total de RAM/VRAM. A inspeção desta máquina encontrou aproximadamente 15,4 GiB de RAM total e 3,8 GiB livres, sem homologação de GPU ou inferência. A viabilidade do modelo ainda deve ser medida, liberando memória antes do teste. Uma alternativa menor é [`qwen3:1.7b`](https://ollama.com/library/qwen3:1.7b), de aproximadamente 1,4 GB, também com ferramentas e Apache-2.0; sua qualidade e latência também não foram medidas aqui.

Depois de avaliar espaço e memória, os comandos abaixo baixam pesos públicos, sem dados do projeto. Escolha um dos modelos:

```powershell
ollama pull qwen3:4b
# Alternativa menor, se necessária:
# ollama pull qwen3:1.7b
```

Para executar somente inferência local, desabilite a nuvem no processo Ollama. Se o aplicativo já estiver usando a porta, encerre-o pela bandeja antes de iniciar outro servidor:

```powershell
$env:OLLAMA_NO_CLOUD = '1'
ollama serve
```

Essa variável deve pertencer ao processo Ollama; defini-la apenas na CLI Python não altera um servidor já iniciado. A opção segue a [documentação de nuvem do Ollama](https://github.com/ollama/ollama/blob/main/docs/cloud.mdx). O adaptador aceita apenas loopback, ignora proxies de ambiente, não segue redirecionamentos e rejeita nomes cloud e metadados que indiquem modelo remoto.

Em outro terminal, verifique a instalação e as capacidades declaradas:

```powershell
ollama --version
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/version
Invoke-RestMethod -Method Post -ContentType application/json -Body '{"model":"qwen3:4b"}' http://127.0.0.1:11434/api/show
```

Antes de enviar mensagens, o adaptador consulta versão e capacidades. Ausência de suporte a ferramentas, resposta inválida, modelo inexistente ou declaração de inferência remota bloqueia a operação. Isso não substitui confiar na instalação local do servidor. Não habilite captura de prompts confidenciais no processo Ollama.

### Execução da CLI

Prepare o banco e o índice com os comandos das Fases 2 e 3. Na raiz, com o Ollama em execução:

```powershell
$env:EMPORIO_OLLAMA_MODELO = 'qwen3:4b'
backend/.venv/Scripts/python.exe -X utf8 -m emporio_ia.conversar
```

Para a alternativa menor, altere `EMPORIO_OLLAMA_MODELO` para `qwen3:1.7b`. Digite perguntas no terminal e `/sair` para encerrar. EOF e Ctrl+C também encerram com segurança. Respostas e referências são locais e confidenciais. A CLI não grava transcrições e não mantém histórico entre perguntas; repita nome/identificador quando necessário. A memória de uma pergunta existe apenas durante seu ciclo de ferramentas.

Assim como os demais comandos locais, a CLI lê variáveis do processo, sem carregar `.env` automaticamente. A API de saúde não inicializa o agente nem exige Ollama. Não existe endpoint de atendimento nesta fase.

### Limites e respostas seguras

As variáveis `EMPORIO_OLLAMA_*` e `EMPORIO_AGENTE_*` estão em `.env.example`. Padrões: temperatura 0, 512 tokens de saída, contexto Ollama de 8192 tokens, quatro etapas, seis chamadas, três resultados por ferramenta, pergunta de até 1000 caracteres, 6000 bytes de contexto serializado, resposta HTTP de até 65536 bytes, timeout de 60 segundos por operação de modelo, dez segundos por ferramenta e 120 segundos por pergunta. Configurações incompatíveis de contexto são recusadas. O orçamento em bytes não é uma medição exata de tokens; o adaptador verifica também o payload efetivamente enviado.

Chamadas idênticas após validação são bloqueadas; chamadas são sequenciais. Timeouts cancelam a espera assíncrona. Leituras SQLite executadas em threads podem terminar em segundo plano, sujeitas ao timeout de conexão existente; não há escrita por essas ferramentas.

O modelo finaliza com um JSON de tipo e identificadores de evidência. Citações desconhecidas, texto livre, campos extras ou ausência das fontes exigidas provocam abstenção. Regras determinísticas conservadoras identificam intenções explícitas de preço, disponibilidade, categorias, promoção e política. Perguntas combinadas reconhecidas exigem todas as fontes correspondentes; essas heurísticas não constituem compreensão semântica completa. O usuário pode receber pedido de esclarecimento, indicação de fora do escopo, ausência de evidência ou mensagem de limite/indisponibilidade.

Nenhuma política é parafraseada livremente: a saída documental é uma citação com referência. A qualidade de seleção de ferramentas ainda depende do modelo; a busca documental continua lexical e pode não recuperar informação existente. Não confunda promoção cadastrada ou indicador ativo com comprovação de vigência atual.

### Testes do agente

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/testes/agente
```

Os testes usam SQLite e documentos fictícios, LLM simulado e transporte HTTP simulado. Não exigem Ollama e não leem dados privados. Na entrega, o Ollama não foi localizado no PATH nem no diretório padrão e sua API não respondeu. Portanto não há aprovação de inferência real, versão instalada ou latência. Consulte [arquitetura do agente](docs/arquitetura/agente-local.md), [ADR 0004](docs/decisoes/0004-agente-local.md) e [relatório da Fase 4](docs/relatorios/fase4.md).

## Importação local — Fase 2

Os seis CSVs devem estar em `data/`. São aceitos nomes canônicos, como `products.csv`, e o sufixo ` - products.csv` presente nos arquivos fornecidos. Não renomeie os originais. Duas fontes candidatas para o mesmo conjunto causam erro, sem escolher uma arbitrariamente. O PDF não é aberto.

Na raiz, após instalar o backend:

```powershell
backend/.venv/Scripts/python.exe -m emporio_ia.importar
```

Para substituir os caminhos sem modificar arquivos de configuração:

```powershell
backend/.venv/Scripts/python.exe -m emporio_ia.importar --diretorio-dados data --banco .local/emporio.sqlite3
```

Também é possível configurar as variáveis `EMPORIO_DIRETORIO_DADOS` e `EMPORIO_CAMINHO_BANCO` no processo. As flags prevalecem. A execução a partir de outro diretório requer apenas invocar o Python do ambiente virtual pelo caminho absoluto; a localização dos arquivos não depende do terminal.

O comando emite somente estado e contagens por conjunto, sem registros ou caminhos. Falhas retornam código 1 com mensagem sanitizada. Os arquivos são abertos somente para leitura.

Cada execução substitui o snapshot completo das seis tabelas dentro de uma única transação: esquema, limpeza e inserções são confirmados juntos. Erro de validação, duplicata, referência inválida ou interrupção provoca rollback; nenhuma linha inválida é descartada. Reimportar a mesma origem preserva contagens e conteúdo sem duplicação. Alterações manuais no snapshot são substituídas na próxima importação. Use banco dedicado, nunca uma base com dados independentes.

Cabeçalhos devem corresponder exatamente ao contrato, independentemente da ordem. O formato é CSV com vírgula e UTF-8, aceitando BOM. Todos os conjuntos devem conter registros; arquivos vazios ou apenas com cabeçalho são rejeitados para evitar substituição acidental por um snapshot incompleto. Linhas totalmente vazias são ignoradas pelo leitor CSV. `tracking_code`, `estimated_delivery` e `notes` admitem valores vazios, armazenados como `NULL`.

Valores monetários usam `Decimal` e centavos inteiros, sem `float` ou arredondamento silencioso. Aceitam ponto decimal e até duas casas. Percentuais ficam em pontos-base, entre 0 e 10000. Datas exigem `AAAA-MM-DD`. Identificadores, estoque, quantidades e relações são validados. O [contrato dos dados](docs/arquitetura/dados-operacionais.md) detalha as tabelas e limitações.

## Consultas internas

`ServicoCatalogo` oferece busca por identificador ou trecho do nome, categoria, faixa de preço em centavos, estoque e paginação de até 200 produtos. A busca ignora caixa e acentos, tratando `%`, `_` e aspas literalmente. `consultar_preco` retorna `Decimal`; produto inexistente retorna `None`, distinto de estoque zero. A regra conservadora de disponibilidade exige `status = active` e estoque positivo.

Categorias podem ser listadas ou buscadas por identificador. Promoções podem ser filtradas por produto e indicador ativo. **Não há datas de promoção na origem**: `validade_temporal` informa `indisponivel`; não é possível classificar promoções como vigentes ou expiradas. Não há cálculo, combinação ou aplicação de descontos.

`ServicoPedidos` consulta status, itens, rastreamento e entrega estimada apenas para o par pedido/cliente informado pelo chamador interno. A projeção exclui nome, telefone, email, cidade, pagamento e observações. Esse filtro evita mistura de clientes, mas **não é autenticação ou autorização**. O serviço só poderá ser exposto após uma camada confiável validar identidade e permissão. Nesta fase não há nenhuma rota operacional.

Os contratos e a composição local estão exemplificados com dados sintéticos em `backend/testes/conftest.py`. Não registre o retorno de consultas reais.

## Testes e qualidade

Na raiz:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/testes
backend/.venv/Scripts/ruff.exe check backend
backend/.venv/Scripts/ruff.exe format --check backend
```

No frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run format:check
npm.cmd test
npm.cmd run build
```

Para testar o serviço HTTP do frontend contra a API real, mantenha o backend em execução e rode no diretório `frontend`:

```powershell
$env:EMPORIO_TESTAR_INTEGRACAO = '1'
npm.cmd test
Remove-Item Env:EMPORIO_TESTAR_INTEGRACAO
```

Sem essa variável, o teste de integração real é pulado; os testes de interface continuam independentes do backend.

Formatação: `backend/.venv/Scripts/ruff.exe format backend` e `npm.cmd run format` no frontend. O build produz `frontend/dist/`, ignorado pelo Git. Os testes não usam os arquivos operacionais.

## Confidencialidade

Os arquivos operacionais são fornecidos separadamente e devem permanecer exclusivamente em `data/`, sem versionamento. Apenas o importador local lê os CSVs e o indexador local lê o PDF; a API e os testes não leem os dados reais. Texto extraído, seções e índice também são confidenciais e permanecem em `.local/`. Não copie dados para testes, documentação, logs ou backups versionados. `.env`, `.local/`, bancos, journals, arquivos WAL/SHM e backups com extensões previstas também são ignorados. Mantenha quaisquer backups dentro de `.local/` ou em armazenamento privado fora do repositório.

O SQLite contém dados pessoais e comerciais: não o compartilhe. Ele não é criptografado; a proteção em repouso depende das permissões da conta e do volume local. O `.gitignore` previne inclusão acidental no Git, mas não substitui controle de acesso nem impede adição forçada. Leituras usam `mode=ro` e `query_only`; todas as conexões ativam chaves estrangeiras. Não há logs de registros, SQL com valores de usuários ou respostas HTTP operacionais.

Antes de qualquer commit, examine `git status --short`, `git ls-files -- data` e `git diff --cached --name-only`, além de `git check-ignore data/`. O `.gitignore` não protege conteúdo já versionado. Se houver dados no histórico, suspenda publicação e faça diagnóstico; não reescreva histórico sem autorização.

## Limitações e próximas etapas

O indicador informa a disponibilidade da API, não a do modelo, banco ou índice documental. Persistência e atendimento são locais e internos; as funcionalidades visuais de atendimento continuam futuras. O núcleo do agente e o adaptador Ollama existem, mas a inferência real ainda não foi homologada nesta máquina. Não há autenticação, OCR, embeddings, chat visual, atendimento público ou deploy.

A próxima fase poderá preparar a interface de chat e sua integração controlada. A homologação do modelo local deve anteceder alegações de funcionamento de ponta a ponta. O texto documental permanece dado não confiável, sem autoridade para instruir o agente. O SQLite não oferece autorização por cliente: controles de identidade, acesso, sessão e filtragem devem anteceder qualquer exposição. Não existem preços históricos por item na origem; o total do pedido é preservado sem recalculá-lo com preços atuais.

## Transparência e licença

A implementação das Fases 1, 2, 3 e 4 contou com assistência de código do OpenAI Codex. A revisão e a validação dos requisitos do desafio permanecem sob responsabilidade da pessoa candidata.

Nenhuma licença de distribuição foi atribuída sem decisão da titular do projeto. Os dados privados fornecidos para o desafio não são licenciados por este repositório.

## Referências e validação

A configuração segue a documentação oficial de [CORS do FastAPI](https://fastapi.tiangolo.com/tutorial/cors/), [Tailwind com Vite](https://tailwindcss.com/docs/installation/using-vite) e [Vite](https://vite.dev/guide/).

A Fase 2 inclui testes sintéticos para importação, cabeçalhos, tipos, moeda, datas, duplicatas, relacionamentos, rollback após escrita e interrupção, idempotência, consultas, SQL parametrizado, isolamento de pedidos, CLI e ausência de exposição HTTP. Os resultados executados constam no [relatório da Fase 2](docs/relatorios/fase2.md).

A Fase 3 acrescenta PDFs sintéticos gerados nos testes, extração, segmentação com origem reconstruível, indexação, rollback, idempotência, alteração de documento, ranking, ausência de evidência, segurança e CLI. Consulte o [relatório da Fase 3](docs/relatorios/fase3.md). Para executar somente os testes documentais: `backend/.venv/Scripts/python.exe -m pytest backend/testes/documentos`.

Não foi realizada inspeção visual em navegador nesta sessão. A auditoria npm da Fase 1 apontava 12 alertas moderados na cadeia de desenvolvimento do ESLint, ligados a `minimatch`; as dependências frontend não foram alteradas nem novamente auditadas na Fase 2. O pytest continua emitindo um aviso de depreciação do transporte `httpx` no TestClient do Starlette; os testes passam.
