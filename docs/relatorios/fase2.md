# Relatório técnico — Fase 2

Data: 31/10/2026. Escopo: engenharia de dados, SQLite e consultas operacionais internas.

## A. Diagnóstico inicial

A branch `main` estava limpa, no commit `f5aecc4`, com backend e frontend da Fase 1. Os oito testes Python originais, Ruff lint e Ruff format check passaram antes das mudanças. A referência remota `main` foi consultada e apontava para o mesmo commit local. O histórico disponível não registra `data/`; nenhum arquivo da pasta estava rastreado. Não houve publicação, reescrita de histórico ou mudança de branch.

Foram calculados hashes SHA-256 dos sete arquivos originais antes do trabalho e comparados após a importação e reimportação: todos permaneceram iguais. A inspeção imprimiu somente cabeçalhos, tipos, contagens e agregados. O PDF foi apenas incluído na verificação de integridade binária, sem extração ou interpretação.

## B. Estrutura dos CSVs

Os seis CSVs possuem o prefixo `desafio_tecnico_ai_eng - ` e usam UTF-8 e vírgula. O importador reconhece esse sufixo sem renomear fontes.

| Conjunto   | Registros | Chaves e tipos                                                                                                                             |
| ---------- | --------: | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Categorias |         9 | Identificador inteiro; nome e descrição textuais                                                                                           |
| Clientes   |        50 | Identificador inteiro; nome, telefone, email e cidade textuais                                                                             |
| Produtos   |        65 | Identificador e categoria inteiros; preço decimal; estoque inteiro; nome, descrição, estado e especificações textuais; criação em data ISO |
| Pedidos    |        20 | Identificador e cliente inteiros; total decimal; data ISO; estado e pagamento textuais; rastreamento, entrega e observações opcionais      |
| Itens      |        22 | Pedido, produto e quantidade inteiros                                                                                                      |
| Promoções  |        25 | Identificador e produto inteiros; desconto percentual; descrição textual; indicador ativo 0/1                                              |

Os cabeçalhos completos, campos opcionais e as cinco relações confirmadas estão em [dados operacionais](../arquitetura/dados-operacionais.md). Não há órfãos ou chaves primárias repetidas. Há um email repetido entre identificadores diferentes, sem deduplicação automática. Não há datas de promoção nem preço unitário histórico nos itens.

## C. Modelagem

Foram implementadas seis tabelas `STRICT`: `categorias`, `clientes`, `produtos`, `pedidos`, `itens_pedido` e `promocoes`. Cada uma preserva as informações fornecidas, com nomes internos em português. Há chaves primárias, relações estrangeiras, restrições de intervalos e obrigatoriedade. Itens usam chave composta pedido/produto; duplicatas são recusadas, nunca agregadas silenciosamente.

Preços e totais ficam em centavos inteiros; percentuais, em pontos-base. Datas ficam em ISO. `nome_busca` é uma projeção derivada do nome, sem acentos e sem distinção de caixa. Índices apoiam categoria e preço de produtos, cliente de pedidos e referências de produto em itens e promoções. Não foi criado índice ineficaz para busca por substring.

O SQLite utilizado é 3.43.1. `integrity_check` e `foreign_key_check` passaram na base real local. A estratégia está registrada na [ADR 0002](../decisoes/0002-persistencia-operacional.md).

## D. Importação

O comando `python -m emporio_ia.importar` utiliza configuração centralizada e caminhos ancorados na raiz, sem depender do diretório do terminal. Há flags para dados e banco. A CLI lê variáveis do processo, sem carregar `.env` implicitamente, e emite apenas estado e contagens.

Cabeçalhos, tipos, valores obrigatórios, datas, moeda, percentuais, quantidades, duplicatas e referências são validados. Rastreamento, entrega e observações vazios tornam-se `NULL`. Os seis conjuntos devem ser não vazios. O importador aceita UTF-8 com BOM e ordem alternativa dos cabeçalhos, mas não colunas desconhecidas ou ambíguas.

Uma transação explícita inclui esquema, limpeza e todas as inserções. Falhas e interrupções provocam rollback, inclusive após escrita parcial. A reimportação substitui o snapshot completo, sem duplicar registros. Não há merge ou preservação de alterações manuais no banco derivado. Bancos sem versão reconhecida ou com versão futura são recusados.

A importação real e uma nova execução a partir de `backend/` concluíram com as mesmas contagens. O banco local está em `.local/emporio.sqlite3`, ignorado. Nenhum arquivo original foi alterado.

## E. Consultas

`ServicoCatalogo` oferece identificador, nome, categoria, intervalo de preços, estoque, disponibilidade e paginação de produtos; também permite listar categorias e filtrar promoções por produto e indicador ativo. Ausência retorna `None` ou lista vazia. Preço consultado é `Decimal`; não há `float` financeiro.

`ServicoPedidos` retorna status, data, total original, itens e informações de entrega para o par pedido/cliente informado por um chamador interno confiável. A projeção não contém nome, telefone, email, cidade, pagamento ou observações. O filtro não autentica nem autoriza o usuário; a exposição dependerá de controles futuros e não há endpoint para esses serviços.

Promoções retornam validade temporal indisponível: não é possível implementar classificação como vigente/expirada nem testar expiração real sem campos de período. Foram testados estados ativo/inativo e a indicação explícita dessa limitação. Não há combinação de descontos ou reprecificação histórica.

As consultas reais foram exercitadas localmente sem imprimir registros, confirmando catálogo, preço, estoque, pedido e isolamento entre clientes. Não há consultas SQL nas rotas.

## F. Segurança

- `data/`, `.local/`, bancos, journals, WAL/SHM e backups previstos estão ignorados.
- Sete hashes das fontes permaneceram idênticos.
- Valores SQL são parâmetros; fragmentos de SQL são constantes internos.
- Conexões de leitura usam `mode=ro` e `query_only`; todas ativam chaves estrangeiras.
- Erros não reproduzem valores pessoais, caminhos ou SQL interno; não há logs de registros.
- Testes usam apenas fontes sintéticas geradas em diretórios temporários.
- O contrato OpenAPI continua contendo apenas `/api/saude`; pedidos, clientes, catálogo e fontes não são servidos por HTTP.
- Não há staging de arquivo confidencial nem publicação.

Limites: o banco não é criptografado e depende das permissões locais. `.gitignore` não substitui controle de acesso ou impede adição forçada. O serviço interno de pedidos não é um mecanismo de autorização. A revisão futura dessas fronteiras deverá preceder qualquer integração exposta ao usuário.

## G. Arquivos

Criados:

- `backend/src/emporio_ia/dominio/`: entidades, consultas/filtros, validações e exceções.
- `backend/src/emporio_ia/aplicacao/`: contratos, catálogo e pedidos.
- `backend/src/emporio_ia/infraestrutura/`: conexões, esquema, formatos e leitura CSV, importação e repositórios.
- `backend/src/emporio_ia/importar.py`: CLI local.
- `backend/testes/conftest.py` e testes de importação, consultas, validação e privacidade.
- Contrato de dados, ADR 0002 e este relatório.

Atualizados: `.gitignore`, `.env.example`, configuração central, README, visão arquitetural e referência de evolução na ADR 0001. Não houve mudanças no frontend, nos testes originais da Fase 1 ou nas dependências.

## H. Testes e validações executados

| Verificação                                             | Resultado                             |
| ------------------------------------------------------- | ------------------------------------- |
| `python -m pytest backend/testes` pelo ambiente virtual | 117 testes passaram                   |
| `ruff check backend`                                    | Aprovado                              |
| `ruff format --check backend`                           | Aprovado                              |
| Importação real e reimportação em outro diretório       | Concluídas; mesmas contagens          |
| Consultas internas reais, sem saída de registros        | Aprovadas                             |
| `PRAGMA integrity_check` e `foreign_key_check`          | Aprovados                             |
| `GET /api/saude` por HTTP real                          | 200, contrato preservado              |
| CORS com origem local explicitamente permitida          | Cabeçalho correto                     |
| OpenAPI e rotas operacionais ausentes                   | Verificados                           |
| `npm.cmd run typecheck`                                 | Aprovado                              |
| `npm.cmd run lint`                                      | Aprovado                              |
| `npm.cmd run format:check`                              | Aprovado                              |
| Vitest com `EMPORIO_TESTAR_INTEGRACAO=1`                | 6 testes passaram, incluindo API real |
| `npm.cmd run build`                                     | Aprovado                              |
| Página do build servida por HTTP local                  | 200; título UTF-8 correto             |
| SHA-256 dos sete originais                              | Sem alterações                        |
| Git ignore de fontes, banco, journals e backups         | Verificado                            |

O pytest mantém um aviso de depreciação do transporte `httpx` no TestClient do Starlette. Não houve teste visual em navegador nesta sessão. Não foi repetida auditoria de dependências; os 12 alertas moderados do frontend registrados na Fase 1 não foram tratados neste escopo.

## I. Git

Branch: `main`. Working tree contém somente os arquivos de implementação e documentação descritos acima; staging vazio. Nenhum `git add`, commit, push, branch adicional ou operação destrutiva de histórico foi executado. A revisão das mudanças permanece necessária antes de autorizar um único commit.

Mensagem sugerida: `feat: implementa persistencia e consultas operacionais`.

## J. Próxima fase

Definir recuperação das políticas em PDF: escolher biblioteca gratuita com licença adequada, estratégia de extração, fragmentação, referências e testes sintéticos. O PDF original deve permanecer intacto. Essa recuperação, assim como LLM, Ollama, RAG, Function Calling e chat, não foi implementada.

As Fases 1 e 2 contaram com assistência de código do OpenAI Codex. A revisão final e a responsabilidade pelo desafio permanecem com a pessoa candidata.
