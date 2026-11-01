# Correção do atendimento conversacional

Data: 01/11/2026, America/Sao_Paulo. Validação local de desenvolvimento; este relatório complementa os diagnósticos históricos das Fases 6 e 6.1.

## 1. Causa raiz

A instância operacional não tinha `.local/publicacao.json`. As fontes existiam e a recuperação direta de troca encontrava trechos, mas o filtro de visitantes removia todas as evidências. O resultado vazio era apresentado como falta de informação. Os testes de integração criavam manifestos temporários com autorizações fictícias, por isso passavam sem comprovar a preparação do atendimento operacional.

Além disso, saudações passavam pelo agente comercial; a busca exigia termo e pesquisava apenas o nome literal normalizado, sem categoria ou equivalência de plural. A consulta direta por “violão” retornava vazia antes da correção. Erros de banco também eram convertidos em ausência de evidência.

## 2. Instância e fontes verificadas

O módulo realmente servido pelo Vite em `127.0.0.1:5173` indicou `VITE_API_URL=http://127.0.0.1:8001`. A porta 8000 não tinha API ativa no diagnóstico inicial. Não havia `.env.local` no frontend. A API 8001 usava Uvicorn sem `--reload`; foi reiniciada exclusivamente essa instância para carregar a correção. Ollama e Vite preexistentes foram preservados.

Configuração local resolvida: `C:\Users\PICHAU\EngineerIA\.local\emporio.sqlite3`, `C:\Users\PICHAU\EngineerIA\.local\politicas.sqlite3` e `C:\Users\PICHAU\EngineerIA\.local\publicacao.json`. O identificador de configuração devolvido pela API atual coincidiu com o cálculo local sobre ambiente, esses caminhos, URL e modelo. Ollama acessível em `127.0.0.1:11434`, modelo `qwen3:4b` mantido.

Catálogo, categorias e promoções estavam preenchidos. Índice documental e FTS5 estavam preenchidos; a ferramenta direta de políticas encontrou troca. Ambos os bancos tiveram integridade `ok` e zero violações de chaves estrangeiras. Não houve importação, reindexação ou alteração das fontes.

## 3. Liberação autorizada

O operador autorizou expressamente a proposta privada `.local/publicacao.proposta-conversa.json` após apresentar seu escopo. Antes de aplicar, as referências e os hashes foram regenerados a partir das fontes em leitura e comparados integralmente à proposta: 65 projeções de catálogo, 3 categorias, 25 promoções e 13 trechos documentais, total de 106 evidências.

Foi criado `.local/publicacao.json` com `ambiente=desenvolvimento`. O catálogo publica somente nome, preço, disponibilidade e categoria; promoções mantêm a ressalva de vigência; políticas publicam apenas os trechos selecionados. Não foram autorizados clientes, pedidos, descrições livres, dados pessoais ou o PDF integral. O manifesto permanece privado e ignorado pelo Git. Alterações futuras nos textos ou referências exigem nova revisão.

## 4. Correções

Saudações, agradecimentos e despedidas isoladas recebem resposta cordial determinística, estado `social`, sem modelo, banco ou manifesto. Uma saudação acompanhada de pergunta comercial segue o atendimento normal.

A busca permite listar sem termo e consultar nome ou categoria, com normalização de acentos e plural por função SQLite registrada apenas na conexão de leitura. Valores SQL continuam parametrizados, inclusive caracteres `%` e `_` literais.

Quando o modelo omite uma consulta necessária em uma finalização estruturada válida, ou faz uma busca vazia com frase inadequada, o agente pode recuperar uma consulta canônica limitada por fonte. Usa o mesmo executor, validação de argumentos, whitelist, limites e filtro de publicação. Não substitui falhas de infraestrutura, não aceita JSON inválido e não inventa fatos. A resposta continua reconstruída exclusivamente das evidências selecionadas e autorizadas.

Ausência efetiva de produto/política/promoção tem mensagem específica. Resultados existentes sem autorização geram `503 publicacao_indisponivel`; falha de fonte gera `503 consulta_indisponivel`. Disponibilidade informa estado da publicação e identificador de configuração, sem expor caminhos ou conteúdo por HTTP.

## 5. Arquivos

| Área | Arquivos principais |
| --- | --- |
| Linguagem e busca | `aplicacao/linguagem.py`, `dominio/busca_produtos.py`, `infraestrutura/repositorios/produtos.py`, `infraestrutura/ferramentas_agente.py` |
| Orquestração e evidências | `aplicacao/agente.py`, `aplicacao/fundamentacao.py`, `dominio/agente.py`, `aplicacao/atendimento.py` |
| Publicação e API | `infraestrutura/publicacao.py`, `configuracao.py`, `principal.py`, `api/atendimento.py` |
| Frontend | `src/tipos/atendimento.ts`, `src/servicos/atendimento.ts`, `src/testes/atendimento.test.ts` |
| Regressões backend | `testes/agente/test_conversa.py`, `testes/agente/test_orquestracao.py`, `testes/atendimento/test_http.py`, `testes/atendimento/test_publicacao.py` |
| Documentação | README, arquitetura de atendimento web e este relatório |

Os caminhos backend da tabela são relativos a `backend/src/emporio_ia`, exceto os explicitamente iniciados por `testes`, relativos a `backend`. Não houve redesenho do chat.

## 6. Testes automatizados

A regressão verifica atos sociais sem dependências, perguntas mistas, plural, busca por categoria, listagem, recuperação com ferramentas reais sobre fixtures, consulta combinada, rejeição de formatos/IDs inválidos, indisponibilidade de modelo/banco e segregação do manifesto por ambiente. Testes existentes de preço, centavos, SQL literal, privacidade, whitelist e revogação foram preservados.

Resultado final: **331 testes backend aprovados**, com 11 casos reais optativos pulados na suíte comum; **11 testes optativos com Ollama real aprovados em 67,48 s**; **46 testes frontend aprovados**, com duas integrações HTTP optativas puladas. Ruff check e format, ESLint, TypeScript/build, Prettier e `git diff --check` aprovados. Permanece o aviso preexistente de depreciação TestClient/httpx. A suíte optativa usa Ollama real e fontes fictícias; os ensaios operacionais e de navegador são evidências adicionais separadas.

## 7. FastAPI, Ollama e fontes operacionais

Treze consultas HTTP TCP na API 8001 passaram: Olá, bom dia, agradecimento, listagem, preço de violão com saudação, violões no plural, promoções, troca, garantia, guitarras, preço com troca, produto inexistente e dados pessoais. Consultas comerciais retornaram `fundamentada` com referências; inexistente retornou `sem_evidencias`; dados pessoais foram bloqueados.

Saudações levaram até 0,01 s. Consultas comerciais desta amostra levaram de 5,93 a 20,18 s; a combinada levou 14,65 s. Não se trata de benchmark controlado nem garantia de latência.

Uma segunda conferência de preço, promoções, troca e combinação comparou o texto integral das respostas em memória às projeções autorizadas, sem publicar valores neste relatório: quatro aprovações. Páginas HTTP coincidiram com os trechos selecionados. Promoções incluíram a ressalva de vigência. Tempos: 5,74 s, 5,37 s, 6,33 s e 12,60 s, respectivamente.

Ensaios adicionais em aplicações FastAPI isoladas, sem desligar os serviços do operador: banco inexistente, com Ollama real, retornou `503 consulta_indisponivel` em 3,04 s; transporte para porta local sem Ollama retornou `503 modelo_indisponivel` em 2,30 s. Nenhuma resposta foi tratada como catálogo vazio. O segundo caso usa conexão real recusada, sem simular o adaptador nem parar o Ollama ativo. A suíte optativa também aprovou recusa de instrução para executar SQL/ler arquivos e pergunta fora do escopo.

## 8. Navegador e exemplos

Edge headless com perfil isolado acessou o Vite real 5173, a API 8001, Ollama e as fontes operacionais autorizadas. Passaram saudação, listagem, preço de violão, troca e promoções, com referências comerciais visíveis. Tempos observados: 0,12 s, 10,02 s, 6,15 s, 6,63 s e 5,19 s. Passaram também cancelamento, retorno do foco e liberação da vaga para uma pergunta pessoal bloqueada; nenhuma exceção JavaScript observada.

Exemplo social: “Olá” recebe boas-vindas da Empório da Música. “Qual o preço de um violão?” retorna projeção comercial conferida com o cadastro. “Qual a política de troca?” retorna trecho autorizado e página de origem. “Quais promoções estão cadastradas?” retorna cadastro com vigência temporal não confirmada. Os valores e trechos privados não foram copiados para documentação ou logs de validação.

## 9. Limites

A recuperação é lexical e limitada; não oferece entendimento universal nem memória de conversa. Listagem continua limitada pela configuração, sem afirmar que a amostra seja todo o catálogo. Apenas as 106 evidências revisadas estão liberadas neste ambiente. Outros trechos recuperáveis podem continuar bloqueados até aprovação explícita. Inferência depende do modelo local e pode falhar; as validações não foram reduzidas para esconder falhas.

Leitor de tela e celular físico continuam pendentes conforme a Fase 6. Esta execução comprova os cenários documentados em desenvolvimento, sem certificar implantação pública ou homologação universal.

## 10. Integridade e Git

Os nove arquivos privados originais mantiveram os hashes SHA-256. A auditoria de arquivos rastreados e novos não ignorados não encontrou coincidências com os valores privados no escopo examinado. Nenhuma instalação, troca de modelo, alteração em `data/`, staging, commit ou push foi executada. O manifesto aplicado e artefatos locais permanecem ignorados. A API corrigida em 8001 permanece disponível para o frontend; serviços preexistentes Ollama e Vite foram preservados.
