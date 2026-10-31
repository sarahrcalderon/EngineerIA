# engineerIA

Fundação técnica de um assistente de atendimento para a loja fictícia Empório da Música, de Campo Grande/MS, no contexto do desafio de AI Engineer da Artefact.

A Fase 1 entrega uma API de saúde e uma interface que verifica sua disponibilidade. O objetivo é estabelecer configuração, organização, testes e documentação para as próximas etapas. Não há chat, agente, consultas comerciais ou processamento de dados nesta versão.

## Tecnologias e decisões

- Python 3.12+, FastAPI, Pydantic e Uvicorn: contratos tipados, validação e documentação OpenAPI automática.
- React, TypeScript e Vite: interface em componentes e verificação estática.
- Tailwind CSS e Lucide React: composição visual e ícones locais, sem serviços externos.
- pytest, Ruff, Vitest, Testing Library, ESLint e Prettier: verificações automatizadas.
- `fetch` nativo: comunicação HTTP sem dependência adicional.
- `pydantic-settings`: configuração tipada por variáveis de ambiente.

Todas as ferramentas necessárias à execução local são gratuitas. Não é necessário Docker nem provedor de IA. As versões efetivamente resolvidas estão em `frontend/package-lock.json` e `backend/requirements-dev.lock`.

## Arquitetura e estrutura

```text
backend/
  src/emporio_ia/
    api/                 # rotas, esquemas e dependências HTTP
    configuracao.py      # ambiente e CORS
    principal.py         # fábrica da aplicação e erros
  testes/                # contrato HTTP, configuração e inicialização
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
  decisoes/0001-arquitetura-inicial.md
data/                    # confidencial, local, ignorado pelo Git
```

A fábrica `criar_aplicacao` recebe configurações e disponibiliza a instância por dependência FastAPI. A interface consulta apenas `GET /api/saude`, com limite de cinco segundos, cancelamento ao desmontar e nova tentativa manual em caso de falha. A resposta é validada também em tempo de execução. Camadas de domínio e infraestrutura serão criadas quando houver regras e integrações concretas.

## Pré-requisitos

- Windows com PowerShell, Python 3.12+ e Node.js 22.12+ (validado com Node 24).
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

| Variável | Local | Uso |
| --- | --- | --- |
| `EMPORIO_AMBIENTE` | backend | `desenvolvimento`, `teste` ou `producao` |
| `EMPORIO_ORIGENS_CORS` | backend | Lista JSON de origens HTTP explícitas |
| `VITE_API_URL` | frontend | URL base da API; obrigatória para conexão |

O Uvicorn recebe `.env` explicitamente por `--env-file`; `python-dotenv`, usado por essa opção, integra o conjunto de dependências de configuração. O Vite lê `frontend/.env.local`. Reinicie os serviços após alterar ambiente. CORS é independente do nome do ambiente: configure as origens adequadas em cada instalação, sem curingas. Credenciais não são permitidas por CORS nesta fase. Variáveis `VITE_*` são públicas e nunca devem conter segredos.

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

Os arquivos operacionais são fornecidos separadamente e devem permanecer exclusivamente em `data/`, sem versionamento. A aplicação desta fase não lê essa pasta. Não copie dados para testes, documentação, logs ou backups versionados. `.env` e bancos locais também são ignorados. Os testes usam somente respostas sintéticas de saúde.

Antes de qualquer commit, examine `git status --short`, `git ls-files -- data` e `git diff --cached --name-only`, além de `git check-ignore data/`. O `.gitignore` não protege conteúdo já versionado. Se houver dados no histórico, suspenda publicação e faça diagnóstico; não reescreva histórico sem autorização.

## Limitações e próximas etapas

O indicador informa a disponibilidade da API, não a de um agente. Não há autenticação, persistência, importação de CSV, extração de PDF, atendimento, promoções ou consulta de pedidos. As funcionalidades apresentadas na página estão explicitamente marcadas como futuras.

As próximas fases poderão definir importação local, SQLite, consultas estruturadas, recuperação de políticas e integração local com Ollama, conforme os requisitos de privacidade e a capacidade do computador. Nenhuma dessas dependências está instalada nesta fase. A escolha do modelo e da biblioteca de PDF ainda precisa de validação.

## Transparência e licença

A implementação da Fase 1 contou com assistência de código do OpenAI Codex. A revisão e a validação dos requisitos do desafio permanecem sob responsabilidade da pessoa candidata.

Nenhuma licença de distribuição foi atribuída sem decisão da titular do projeto. Os dados privados fornecidos para o desafio não são licenciados por este repositório.

## Referências e validação

A configuração segue a documentação oficial de [CORS do FastAPI](https://fastapi.tiangolo.com/tutorial/cors/), [Tailwind com Vite](https://tailwindcss.com/docs/installation/using-vite) e [Vite](https://vite.dev/guide/).

Nesta entrega foram executados oito testes Python e seis testes frontend, incluindo integração com a API real, além de Ruff, TypeScript, ESLint, Prettier e build. Não foi realizada inspeção visual em navegador nesta sessão. A auditoria npm após atualizar as ferramentas eliminou os dois alertas críticos iniciais, mas ainda aponta 12 alertas moderados na cadeia de desenvolvimento do ESLint, ligados a `minimatch`, sem correção automática disponível. Não foram aplicadas substituições forçadas incompatíveis. O pytest também emite um aviso de depreciação do transporte `httpx` no TestClient do Starlette; os testes passam.
