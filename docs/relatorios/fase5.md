# Fase 5 — Interface de chat e integração segura

Data da validação: 31/10/2026. Implementação técnica concluída; homologação real parcial. Não declarar o atendimento pronto para uso real.

## A. Diagnóstico inicial

Branch `main`, HEAD inicial `be1904c`, working tree inicialmente limpa. Fundação React/TypeScript/Vite, FastAPI e agente local da Fase 4 preservados. Baseline: 246 testes backend aprovados; frontend com cinco aprovados e uma integração optativa não executada. Nenhum arquivo privado foi incorporado ao código.

Ambiente Windows, Python do ambiente virtual existente e Node local. Ollama 0.40.13 já instalado, com `qwen3:4b` local de aproximadamente 2,5 GB e capacidades de ferramentas/pensamento. Não houve instalação ou download do modelo. A medição inicial indicou aproximadamente 15,4 GiB de RAM total e 5,3 GiB livres. Edge disponível para inspeção headless com perfil isolado.

## B. Frontend

Layout de chat com identidade SVG existente, barra lateral desktop, cabeçalho, boas-vindas, sugestões, área de mensagens e composição. Componentes próprios: `CabecalhoAtendimento`, `BoasVindas`, `AreaMensagens` e `CampoMensagem`; o indicador de saúde existente foi preservado.

Temas claro/escuro com preferência inicial do sistema e armazenamento somente da preferência visual. CSS responsivo, tipografia legível, foco visível, região de mensagens acessível, rótulos e alvos de toque. Inspeção Edge em 1440 × 960 e 390 × 844: sem rolagem horizontal, campo visível e texto do campo com 16 px. Capturas ficaram em `.local/`, ignoradas pelo Git. Nenhum pacote frontend adicionado.

## C. UX

Sugestões preenchem o campo sem envio automático. Enter envia, Shift+Enter quebra linha e eventos de composição são respeitados. Há contador/limite, espera sem streaming fictício, prevenção de envio duplicado, cancelamento, nova tentativa e nova conversa com foco no campo. Erros distinguem rede, resposta inválida, limite, indisponibilidade e timeout.

Histórico somente no estado React, limitado a 50 mensagens recentes, descartado ao recarregar ou iniciar nova conversa. Cada pergunta é independente para o agente; isso está informado na interface. Não há transcrições em armazenamento persistente. Respostas tardias não repovoam conversas encerradas. HTML é apresentado como texto, sem execução.

## D. Backend

`GET /api/saude` permanece compatível. `GET /api/atendimento/disponibilidade` verifica metadados do servidor/modelo sem gerar resposta e informa homologação pendente. `POST /api/atendimento/mensagens` recebe exclusivamente uma mensagem e devolve estado, texto verificado, referências seguras e UUID de requisição.

O serviço visitante reutiliza o agente e ferramentas existentes por composição. A finalização pode selecionar somente evidências existentes sob esquema JSON; as verificações de fundamentação continuam obrigatórias. A resposta comercial é reconstruída pelas evidências autorizadas, sem publicar prosa livre do modelo. Os erros são sanitizados. Nenhum endpoint operacional de clientes ou pedidos foi criado.

## E. Segurança

Foi acrescentada autorização explícita por referência e SHA-256 de fonte/texto/referência, em manifesto privado `.local/publicacao.json`. Ausente ou vazio nega publicação; inválido falha de forma fechada. Filtro antes de enviar resultados ao modelo e nova checagem na resposta permitem revogação. A CLI de revisão emite somente fingerprints e não grava nem autoriza. O exemplo versionado está vazio. Nenhuma evidência operacional real foi autorizada automaticamente.

Atendimento restrito a peer e Host de loopback e origens CORS explícitas, sem credenciais. Não foi publicado na internet. Limites padrão: 1.000 caracteres, 8 KiB de corpo, leitura em 10 s, 20 requisições/minuto por IP, uma consulta ativa por processo, 120 s totais no backend e 130 s no navegador. Resposta limitada a 16.000 caracteres e 20 referências. A vaga é liberada após timeout ou cancelamento.

Referências têm título/tipo e página documental real, sem caminhos, hashes internos ou pontuações de ranking. Ferramentas continuam de leitura, com consultas parametrizadas; o modelo não recebe SQL, shell ou acesso arbitrário a arquivos.

Os nove arquivos privados existentes em `data/` e `.local/` mantiveram seus SHA-256. Os dois bancos retornaram `integrity_check=ok` e zero violações de chave estrangeira. A varredura dos arquivos alterados/novos contra valores privados e linhas documentais não encontrou cópias; foi desconsiderada apenas a localização pública já presente no README original. Essa verificação reduz risco de cópia acidental, não constitui prova universal de ausência de informação sensível.

## F. Ollama e homologação

O servidor local respondeu aos metadados com o modelo disponível. Isso é apresentado como “Modelo acessível”, separado de “em validação”. O backend usa `think=false` e `/no_think` para Qwen3, ferramentas nativas e finalização estruturada. Não foi feita chamada a provedor externo.

Os ensaios usaram exclusivamente catálogo e políticas fictícios em diretórios temporários, com autorização fictícia separada. A suíte real inicial cobriu dez cenários:

| Cenário | Resultado observado |
| --- | --- |
| Produto | Resposta fundamentada; 23,58 s |
| Preço | Valor sintético correto; 24,51 s |
| Disponibilidade | Condição sintética correta; 32,13 s |
| Categorias | Falha segura no limite de geração |
| Promoções | Falha segura no limite de geração |
| Políticas | Falha segura no limite de geração |
| Pergunta combinada | Falha segura no limite de geração |
| Fora do escopo | Sem evidências; nenhuma afirmação externa |
| Dados pessoais | Bloqueio antes de inferência |
| Tentativa de instrução maliciosa | Sem evidências; nenhuma execução |

Após simplificar os esquemas opcionais e reforçar a solicitação direta de ferramentas, uma rodada direcionada observada aprovou categorias em 26,69 s e políticas em 38,23 s, com página fictícia correta. Promoções e pergunta combinada continuaram falhando em aproximadamente 43–44 s: o modelo atingiu 512 tokens sem uma chamada de ferramenta válida. As falhas não foram convertidas em respostas inventadas. Não há aprovação global nem garantia de repetibilidade desses tempos.

Conclusão: homologação real parcial, obrigatoriamente pendente antes do uso real. Não foi relaxada a validação para aceitar análise ou texto não fundamentado. O próximo trabalho deve estabilizar chamadas nativas e repetir toda a matriz, com critérios explícitos de correção e latência.

## G. Testes e qualidade

Na raiz:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/testes -q
backend/.venv/Scripts/ruff.exe check backend
backend/.venv/Scripts/ruff.exe format --check backend
```

Resultado final: **278 aprovados**; Ruff check e formatação aprovados. Permanece um aviso de depreciação do transporte httpx do TestClient. Os 246 testes anteriores continuam passando; três expectativas de superfície OpenAPI foram atualizadas para incluir somente os novos endpoints autorizados, mantendo a ausência de endpoints privados.

Os 32 testes acrescentados cobrem autorização, arquivo ausente/inválido, alteração de texto/fonte, revogação, referências, conteúdo fora da lista de publicação, contratos HTTP, entradas inválidas, CORS/Host/Origin, limites, timeout, concorrência, cancelamento, finalização restrita e disponibilidade sem geração.

No diretório frontend:

```powershell
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run format:check
npm.cmd run build
$env:EMPORIO_TESTAR_INTEGRACAO='1'
$env:VITE_API_URL='http://127.0.0.1:8005'
npm.cmd test
```

Resultado: **38 aprovados**, incluindo duas integrações com FastAPI real, sem teste pulado nessa execução. TypeScript, ESLint, Prettier e build aprovados. Sem a variável optativa, 36 testes são independentes e duas integrações são puladas. Portas 8005/5175 foram usadas apenas nos servidores isolados de validação, com CORS explícito correspondente; o padrão documentado continua 8000/5173.

## H. Integração

FastAPI inicializado com `emporio_ia.principal:aplicacao`. Saúde real disponível; metadados reais retornaram modelo acessível e homologação pendente. O serviço HTTP do frontend validou saúde e bloqueio de pergunta pessoal. No Edge, envio por Enter produziu uma mensagem do usuário e uma resposta segura, sem persistir conteúdo, sem erro JavaScript; nova conversa limpou e devolveu o foco.

Cancelamento também verificado por conexão HTTP real: AbortController interrompeu consulta e uma nova pergunta bloqueada retornou 200, comprovando liberação da vaga. Os testes assíncronos cobrem cancelamento da tarefa e liberação por deadline. Não houve alegação de cancelamento garantido de computação interna no servidor Ollama.

## I. Arquivos

Backend: novos módulos `api/atendimento.py`, `api/protecao_atendimento.py`, `aplicacao/atendimento.py`, `dominio/publicacao.py`, `infraestrutura/publicacao.py`, `infraestrutura/composicao_agente.py` e `revisar_publicacao.py`; alterações de composição, configuração, adaptação Ollama, seleção/fundamentação e testes.

Frontend: App e CSS renovados; quatro componentes, hooks de conversa/tema, serviço/DTO de atendimento e testes. Cliente HTTP central preserva API local. SVG original e dependências mantidos.

Documentação: README, exemplos de ambiente, arquitetura do atendimento, atualização da visão geral, ADR 0005, exemplo vazio de autorização e este relatório. Artefatos de inspeção e ensaios ficaram exclusivamente em `.local/`, ignorado.

## J. Git

Branch `main` preservada; alterações estão na working tree para revisão. Nenhum stage, commit, push, branch, merge ou deploy executado. `data/` e `.local/` ignorados, sem arquivos rastreados nesses diretórios; staging vazio; `git diff --check` aprovado.

Commit sugerido, não executado: `feat: implementa interface de chat e integracao com agente`.

## K. Limitações

Homologação real incompleta; inferência pode falhar ou levar dezenas de segundos. Fontes comerciais precisam de revisão e aprovação explícita antes de divulgação. Sem autenticação, autorização por cliente, atendimento pela internet, múltiplos workers, streaming, OCR ou memória entre perguntas. Busca documental permanece lexical. Inspeção headless não substitui teste com leitor de tela nem dispositivo físico. Cancelar uma tarefa não interrompe necessariamente uma leitura SQLite já delegada a thread. Dependências e alertas históricos não foram novamente auditados nem atualizados nesta fase.

## L. Próxima fase

Estabilizar chamadas de ferramentas e finalização no modelo local; repetir os dez cenários com métricas observadas; revisar as evidências que poderão ser divulgadas; complementar acessibilidade e preparar demonstração somente depois de homologação integral. Manter os controles de publicação e confidencialidade durante todo esse processo.
