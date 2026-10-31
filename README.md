# engineerIA

Fundação técnica de um assistente de atendimento para a loja fictícia Empório da Música, de Campo Grande/MS, no contexto do desafio de AI Engineer da Artefact.

A Fase 1 entrega uma API de saúde e uma interface que verifica sua disponibilidade. A Fase 2 acrescenta importação local de CSVs, persistência SQLite e serviços internos de catálogo e pedidos. Não há chat, agente, processamento do PDF ou exposição dos dados operacionais por HTTP.

## Tecnologias e decisões

- Python 3.12+, FastAPI, Pydantic e Uvicorn: contratos tipados, validação e documentação OpenAPI automática.
- React, TypeScript e Vite: interface em componentes e verificação estática.
- Tailwind CSS e Lucide React: composição visual e ícones locais, sem serviços externos.
- pytest, Ruff, Vitest, Testing Library, ESLint e Prettier: verificações automatizadas.
- `fetch` nativo: comunicação HTTP sem dependência adicional.
- `pydantic-settings`: configuração tipada por variáveis de ambiente.
- `sqlite3`, `csv` e `decimal` da biblioteca padrão: persistência, importação e conversões monetárias exatas, sem novas dependências.

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
  decisoes/0001-arquitetura-inicial.md
  decisoes/0002-persistencia-operacional.md
data/                    # confidencial, local, ignorado pelo Git
.local/                  # banco confidencial e artefatos locais, ignorados
```

A fábrica `criar_aplicacao` recebe configurações e disponibiliza a instância por dependência FastAPI. A interface consulta apenas `GET /api/saude`, com limite de cinco segundos, cancelamento ao desmontar e nova tentativa manual em caso de falha. A resposta é validada também em tempo de execução. Os serviços operacionais dependem de contratos; repositórios SQLite implementam esses contratos. A API não instancia esses serviços nem acessa o banco.

## Pré-requisitos

- Windows com PowerShell, Python 3.12+ e Node.js 22.12+ (validado com Node 24).
- SQLite 3.37+ no módulo `sqlite3` do Python, para tabelas `STRICT`.
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

Os arquivos operacionais são fornecidos separadamente e devem permanecer exclusivamente em `data/`, sem versionamento. Apenas o importador local lê os CSVs; a API e os testes não leem os dados reais. Não copie dados para testes, documentação, logs ou backups versionados. `.env`, `.local/`, bancos, journals, arquivos WAL/SHM e backups com extensões previstas também são ignorados. Mantenha quaisquer backups dentro de `.local/` ou em armazenamento privado fora do repositório.

O SQLite contém dados pessoais e comerciais: não o compartilhe. Ele não é criptografado; a proteção em repouso depende das permissões da conta e do volume local. O `.gitignore` previne inclusão acidental no Git, mas não substitui controle de acesso nem impede adição forçada. Leituras usam `mode=ro` e `query_only`; todas as conexões ativam chaves estrangeiras. Não há logs de registros, SQL com valores de usuários ou respostas HTTP operacionais.

Antes de qualquer commit, examine `git status --short`, `git ls-files -- data` e `git diff --cached --name-only`, além de `git check-ignore data/`. O `.gitignore` não protege conteúdo já versionado. Se houver dados no histórico, suspenda publicação e faça diagnóstico; não reescreva histórico sem autorização.

## Limitações e próximas etapas

O indicador informa a disponibilidade da API, não a de um agente ou do banco. Persistência e consultas são locais e internas; as funcionalidades de atendimento da página continuam marcadas como futuras. Não há autenticação, extração de PDF, LLM, Ollama, RAG, Function Calling, chat ou deploy.

A próxima fase poderá definir recuperação de políticas, avaliando biblioteca de PDF, licença e referências verificáveis. Integração local com Ollama permanece futura e depende da capacidade do computador. O SQLite não oferece autorização por cliente: controles de identidade e de acesso devem anteceder qualquer exposição dos serviços. Não existem preços históricos por item na origem; o total do pedido é preservado sem recalculá-lo com preços atuais.

## Transparência e licença

A implementação das Fases 1 e 2 contou com assistência de código do OpenAI Codex. A revisão e a validação dos requisitos do desafio permanecem sob responsabilidade da pessoa candidata.

Nenhuma licença de distribuição foi atribuída sem decisão da titular do projeto. Os dados privados fornecidos para o desafio não são licenciados por este repositório.

## Referências e validação

A configuração segue a documentação oficial de [CORS do FastAPI](https://fastapi.tiangolo.com/tutorial/cors/), [Tailwind com Vite](https://tailwindcss.com/docs/installation/using-vite) e [Vite](https://vite.dev/guide/).

A Fase 2 inclui testes sintéticos para importação, cabeçalhos, tipos, moeda, datas, duplicatas, relacionamentos, rollback após escrita e interrupção, idempotência, consultas, SQL parametrizado, isolamento de pedidos, CLI e ausência de exposição HTTP. Os resultados executados constam no [relatório da Fase 2](docs/relatorios/fase2.md).

Não foi realizada inspeção visual em navegador nesta sessão. A auditoria npm da Fase 1 apontava 12 alertas moderados na cadeia de desenvolvimento do ESLint, ligados a `minimatch`; as dependências frontend não foram alteradas nem novamente auditadas na Fase 2. O pytest continua emitindo um aviso de depreciação do transporte `httpx` no TestClient do Starlette; os testes passam.
