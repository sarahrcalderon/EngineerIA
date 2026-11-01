# Consultas estruturadas ao catálogo

Data: 01/11/2026, America/Sao_Paulo. Escopo local: classificação, filtros e quantidade no catálogo autorizado.

## Causa comprovada

A pergunta “Quais são os 3 produtos mais baratos da loja?” foi reproduzida na API TCP 8001 antes da alteração: HTTP 200, `sem_evidencias`, nenhum produto. No rastreamento adicional com FastAPI, Ollama real e as mesmas fontes operacionais, o modelo solicitou `buscar_produtos` com `termo="3 produto mais barato"` e `limite=3`. A ferramenta retornou zero resultados. A recuperação tentou `termo="sao 3 mais barato loja"`, também com zero resultados.

O código confirmou o caminho: a ferramenta expunha somente termo e limite, e a consulta SQLite usava busca literal com `instr` e ordem por identificador. Os filtros monetários e de disponibilidade existentes no domínio não estavam acessíveis ao agente; não havia ordenação por preço. O vazio surgiu antes do filtro de evidências, não por inexistência do catálogo. Além disso, o limite geral padrão de três resultados impediria cumprir pedidos explícitos de cinco itens.

## Implementação

`buscar_produtos` mantém seu nome e passa a aceitar termo, categoria, disponibilidade, preços mínimo/máximo em centavos inteiros, ordenação (`identificador`, `preco_crescente`, `preco_decrescente`) e limite. JSONSchema e Pydantic validam tipos estritos, intervalos, enum e faixa não invertida. SQL continua composto apenas por fragmentos constantes; todos os valores são parâmetros.

A interpretação conservadora de critérios explícitos fica em `aplicacao/consulta_catalogo.py`. Reconhece quantidades numéricas ou por extenso até dez, classificação, famílias de instrumentos, disponibilidade e valores brasileiros, com ou sem milhares. “Menos de” exclui o centavo do limite; “até” inclui o limite. Prazos sem contexto comercial e ordenações contraditórias não viram critérios monetários. Não há fatos de produto ou preços embutidos nesse interpretador.

Ollama continua participando da escolha de ferramenta. Argumentos e ferramenta são validados antes de aplicar os critérios explícitos interpretados da pergunta; a consulta canônica impede que “mais baratos” seja tratado como nome de produto. Quando a seleção válida omite uma consulta necessária, a recuperação existente usa o mesmo plano estruturado. Erros de transporte, modelo, JSON ou ferramentas proibidas continuam falhando com segurança.

O repositório aplica filtros e `ORDER BY preco_centavos ASC/DESC, identificador ASC`, com desempate estável. Valores nulos, não inteiros ou negativos não participam da consulta; zero continua válido conforme o contrato existente de preço, sem convertê-lo em ausência. A apresentação BRL preserva centavos e separadores brasileiros.

Para consultas somente de catálogo com critérios reconhecidos, o resultado ordenado e verificado da ferramenta constitui o conjunto da resposta. A aplicação finaliza usando os identificadores dessas evidências, sem pedir ao modelo para reduzir ou reorganizar os itens. As validações finais de evidências e publicação continuam ativas. Perguntas combinadas com políticas continuam exigindo ambas as fontes.

O catálogo admite até 20 itens por chamada explícita, limite seguro específico desta ferramenta. Sem quantidade, o padrão configurado continua três. Os limites de outras ferramentas, etapas, chamadas, contexto, tempo e corpo não foram ampliados. Solicitações acima de 20 ficam limitadas a 20; não se promete atender quantidades ilimitadas.

## Publicação antes do limite final

O filtro de visitantes usa o contrato `ContratoConsultaPublicada`. Para busca de produtos, o SQL restringe candidatos aos identificadores de produto presentes no manifesto. As projeções são regeneradas e seus hashes exatos conferidos antes de preencher as vagas finais. Paginação interna de 200 itens cobre o máximo de 500 referências do manifesto, sem enviar candidatos privados ao modelo. Hash desatualizado ou item sem autorização não consome uma vaga; a busca pode preencher com o próximo elegível. O filtro externo e a revalidação imediatamente antes da resposta permanecem.

Não foram incluídas novas autorizações nem alterados os hashes aprovados. O manifesto continua com 106 evidências exclusivamente de desenvolvimento. Clientes, pedidos, descrições livres e documentos integrais não entram nesse fluxo.

## API e frontend

A resposta acrescenta `introducao`, um texto estático de apresentação dos critérios, sem fatos gerados. Os campos `produtos`, `complemento` e referências são preservados. O frontend valida e transporta a introdução e reutiliza todos os cards existentes, na ordem retornada, incluindo imagens ilustrativas, disponibilidade, avatar e fontes expansíveis. Produtos de referências distintas não são eliminados por terem campos visíveis iguais.

O histórico visual e as mensagens anteriores são preservados. As perguntas continuam independentes no backend; não foi introduzida memória contextual implícita.

## Validação real

Onze perguntas na API 8001 com Ollama `qwen3:4b` e fontes operacionais passaram. A validação comparou em memória todos os produtos HTTP com as projeções autorizadas elegíveis; não foram persistidos nomes, valores ou trechos privados no relatório.

| Cenário | Itens | Resultado | Tempo |
| --- | ---: | --- | ---: |
| Pergunta original: três mais baratos | 3 | Fundamentada; ordem crescente; igualdade com catálogo autorizado | 12,04 s |
| Cinco mais caros | 5 | Fundamentada; ordem decrescente e desempate conferidos | 2,74 s |
| Violões abaixo de R$ 1.000 | 3 | Critério estrito respeitado | 8,06 s |
| Quatro guitarras disponíveis | 4 | Disponibilidade conferida | 5,41 s |
| Entre R$ 200 e R$ 800 | 3 | Faixa inclusiva respeitada | 8,45 s |
| Três violões mais baratos | 3 | Família e ordem conferidas | 7,73 s |
| Instrumentos até R$ 500 | 3 | Teto respeitado | 4,14 s |
| “Quero ver os mais baratos” | 3 | Ordenação sem nome específico | 2,91 s |
| “Tem alguma coisa mais em conta?” | 3 | Ordenação sem busca literal | 8,11 s |
| “Mostre cinco opções” | 5 | Quantidade por extenso | 7,79 s |
| “Qual é o violão mais barato?” | 1 | Menor preço elegível | 7,33 s |

Esses tempos são amostras, não benchmark ou garantia de desempenho. O hash do manifesto foi comparado antes e depois dos ensaios, sem alteração.

No navegador real (Vite 5173 → FastAPI 8001 → Ollama), a pergunta original exibiu três cards, introdução, avatar e três ilustrações. Os nomes e os preços BRL no DOM coincidiram com a resposta HTTP capturada; a ordem crescente foi confirmada e nenhuma exceção JavaScript foi observada. O ensaio foi repetido após os últimos ajustes da interpretação. A API atualizada permanece em 8001; Vite e Ollama preexistentes foram preservados.

## Testes e arquivos

Testes cobrem os 14 pontos solicitados: menores/maiores preços, categoria e combinações, disponibilidade, menos itens que o limite, ausência de elegíveis, empate por identificador, preço inválido, exclusão de não autorizados, hash desatualizado sem ocupar vaga, BRL, mensagens sucessivas e todos os cards. Incluem rejeição de ordenação SQL arbitrária, faixa invertida, float, preço textual, booleano textual e limite excessivo.

Criados `backend/src/emporio_ia/aplicacao/consulta_catalogo.py`, `backend/testes/atendimento/test_classificacao.py` e este relatório. Modificados: domínio de consultas/publicação; contratos, linguagem, fundamentação, agente e apresentação; repositório de produtos; ferramentas e filtro de visitantes; DTO FastAPI. Frontend: tipos, serviço, hook de conversa, área de mensagens e testes de apresentação/aplicação. A arquitetura de atendimento documenta o contrato atualizado.

| Diretório | Arquivos alterados |
| --- | --- |
| `backend/src/emporio_ia/aplicacao/` | `agente.py`, `atendimento.py`, `contratos_agente.py`, `fundamentacao.py`, `linguagem.py` |
| `backend/src/emporio_ia/dominio/` | `consultas.py`, `publicacao.py` |
| `backend/src/emporio_ia/infraestrutura/` | `ferramentas_agente.py`, `publicacao.py`, `repositorios/produtos.py` |
| `backend/src/emporio_ia/api/` | `atendimento.py` |
| `backend/testes/atendimento/` | `test_apresentacao.py`, além da nova suíte de classificação |
| `frontend/src/` | `tipos/atendimento.ts`, `servicos/atendimento.ts`, `hooks/useConversa.ts`, `componentes/AreaMensagens.tsx`, `testes/App.test.tsx`, `testes/Apresentacao.test.tsx` |
| `docs/arquitetura/` | `atendimento-web.md` |

Regressão comum: **374 testes backend aprovados, 12 optativos pulados**. Frontend: **71 aprovados**, incluindo duas integrações HTTP reais. Ruff check/format, ESLint, TypeScript/build e Prettier aprovados. O aviso preexistente de depreciação TestClient/httpx permanece. A execução optativa final passou com **43 aprovações em 80,21 s**: 12 cenários com Ollama real e 31 testes de classificação. Foram preservados produto, nome, preço, estoque, promoções, políticas, combinação, JSON, recusa de dados pessoais, injection e fora do escopo, além da nova pergunta de ordenação.

## Integridade e limites

Os nove arquivos operacionais originais mantiveram seus hashes. Não houve importação, reindexação, atualização de banco, instalação de dependências, mudança de modelo ou escrita no manifesto. A auditoria do checkout não encontrou valores privados no escopo examinado. Artefatos de validação permaneceram no diretório temporário do sistema. Sem staging, commit ou push.

A interpretação cobre critérios explícitos e valores no formato brasileiro, não linguagem universal, conversão cambial ou memória de turnos anteriores. Categorias e termos pesquisam os nomes autorizados existentes; não criam uma taxonomia nova. Perguntas não cobertas continuam no fluxo conservador do modelo/esclarecimento. Disponibilidade usa a regra já existente do cadastro e não promete reserva ou estoque em tempo real. Apenas os cenários executados estão comprovados nesta instalação local.
