# Execução local e reprodução da homologação

Perfil verificado em 01/11/2026: Windows, Python 3.12.2, Node 24.21.0, Ollama 0.40.13 e `qwen3:4b` Q4_K_M. A homologação comercial está incompleta; não apresentar a demonstração como atendimento pronto para uso real.

## Preparar o ambiente

Siga a instalação com os locks no README. Nesta fase não houve instalação, atualização de dependências ou download de modelo. Em uma instalação nova, os comandos abaixo exigem rede e devem ser executados conscientemente pelo operador:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.lock
backend/.venv/Scripts/python.exe -m pip install --no-deps -e backend
cd frontend
npm.cmd ci
```

O modelo ocupa aproximadamente 2,5 GB em disco. Há custos adicionais de RAM para contexto e execução; a medição local do modelo carregado foi aproximadamente 3,62 GiB, em CPU. Isso não constitui um requisito universal mínimo. A licença declarada do Qwen3-4B é Apache-2.0; preserve as condições do modelo e das dependências. O projeto e os dados privados não receberam uma licença de distribuição nova.

## Ollama

No Windows, o executável observado é `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`. A ausência no PATH de um shell não comprova ausência da instalação. Confira `ollama --version`, `ollama list` e a API `http://127.0.0.1:11434/api/version`.

Se o modelo não estiver instalado, `ollama pull qwen3:4b` é uma ação manual de download; não foi executada nesta fase. Não substitua o modelo sem revisar a homologação.

Não inicie uma segunda instância se já houver servidor ativo. Para reproduzir o perfil comparativo nativo usado nesta fase, em terminal próprio:

```powershell
$env:OLLAMA_HOST='127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD='1'
$env:OLLAMA_GO_TEMPLATE='false'
& "$env:LOCALAPPDATA/Programs/Ollama/ollama.exe" serve
```

`OLLAMA_GO_TEMPLATE=false` seleciona o template nativo do GGUF nesta versão. Foram observadas falhas tanto nesse caminho como no padrão Go; esta variável **não é uma correção comprovada**. Ela deve pertencer ao processo Ollama, e não apenas ao Python. Não habilite logs de corpo de requisição nem nuvem. Não altere os arquivos do modelo como parte desses comandos.

## Aplicação operacional

Importe os CSVs e indexe o PDF somente quando necessário, com os comandos existentes no README. A homologação desta fase fez consultas em modo de leitura e não reimportou nem reindexou os arquivos privados.

Na raiz:

```powershell
backend/.venv/Scripts/python.exe -m uvicorn emporio_ia.principal:aplicacao --reload --host 127.0.0.1 --port 8000 --no-access-log
```

No frontend, execute `npm.cmd run dev` e abra `http://127.0.0.1:5173`. A configuração padrão usa esse par de portas. A instância FastAPI se chama `aplicacao`, nunca `app`.

Variáveis backend: [.env.example](../../.env.example), carregadas somente com `--env-file .env` quando desejado. CLIs leem o ambiente do processo. Vite lê `frontend/.env.local`, com exemplo em `frontend/.env.example`. Variáveis `VITE_*` são públicas.

O atendimento visitante só publica evidências explicitamente aprovadas em `.local/publicacao.json`. A revisão descrita na [arquitetura](../arquitetura/atendimento-web.md) é obrigatória; não autorize dados reais automaticamente para preparar uma demonstração. Clientes e pedidos não fazem parte das ferramentas do atendimento.

## Demonstração sem dados privados

O servidor abaixo cria bancos e aprovações exclusivamente fictícios em diretório temporário, usa o agente/Ollama reais e não lê os bancos operacionais. Requer o ambiente de desenvolvimento instalado. A validação de isolamento tem teste de regressão.

```powershell
backend/.venv/Scripts/python.exe backend/testes/servidor_homologacao.py
```

Ele escuta somente `127.0.0.1:8005`, com CORS explícito para o frontend em 5175. Em outro terminal:

```powershell
cd frontend
$env:VITE_API_URL='http://127.0.0.1:8005'
npm.cmd run dev -- --port 5175
```

Abra `http://127.0.0.1:5175`. Os identificadores e fatos desse servidor pertencem às fixtures, não à loja. Apresente primeiro os limites: perguntas independentes, histórico somente visual e homologação pendente. Verifique uma consulta fictícia de produto, uma política, as referências, uma recusa pessoal, erro e cancelamento. Se uma consulta falhar, mantenha a falha visível; não substitua o servidor por um simulador para aparentar sucesso.

Encerre os processos próprios ao terminar. O servidor de homologação remove seu diretório temporário no encerramento normal. Não execute exclusão ou reset dos arquivos operacionais.

## Testes

Na raiz, a suíte independente de Ollama:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/testes -q
backend/.venv/Scripts/ruff.exe check backend
backend/.venv/Scripts/ruff.exe format --check backend
```

Homologação optativa, com modelo real e fontes fictícias:

```powershell
$env:EMPORIO_TESTAR_OLLAMA_REAL='1'
backend/.venv/Scripts/python.exe -m pytest backend/testes/atendimento/test_ollama_real.py -q -o junit_family=legacy --junitxml=.local/ollama-real.xml
Remove-Item Env:EMPORIO_TESTAR_OLLAMA_REAL
```

Essa suíte pode falhar na instalação avaliada e deve retornar falha quando os critérios não forem atendidos. Os nove testes são pulados na execução comum, sem disfarçar uma aprovação real. O XML contém somente casos fictícios e metadados; mantenha-o em armazenamento ignorado.

No frontend: `npm.cmd test`, `npm.cmd run typecheck`, `npm.cmd run lint`, `npm.cmd run format:check` e `npm.cmd run build`. Para incluir as duas integrações HTTP, mantenha o backend de homologação ativo e defina `EMPORIO_TESTAR_INTEGRACAO=1` e `VITE_API_URL=http://127.0.0.1:8005` antes de `npm.cmd test`.

## Antes de compartilhar

Leia a [checklist](checklist.md) e o [relatório da Fase 6](../relatorios/fase6.md). Examine `git status`, staging e arquivos ignorados. Não compartilhe `data/`, `.local/`, bancos, PDF, CSVs, transcrições ou autorizações reais. Não publique o backend nem Ollama na internet.
