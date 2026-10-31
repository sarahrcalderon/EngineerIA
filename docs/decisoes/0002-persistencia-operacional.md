# ADR 0002 — Persistência operacional local e importação transacional

Estado: aceita para a Fase 2.

## Contexto

Os seis CSVs privados têm identificadores e relações explícitas. Precisamos de consultas confiáveis, preservando fontes, precisão monetária e isolamento em relação à API pública. O conjunto cabe em processamento local. Não existe necessidade atual de ORM, servidor de banco ou dependência adicional.

## Decisão

Usar `csv`, `decimal` e `sqlite3` da biblioteca padrão. A modelagem deriva exclusivamente dos cabeçalhos inspecionados. Nomes externos permanecem no adaptador CSV; tabelas, entidades, contratos e serviços usam português.

Persistir valores monetários em centavos inteiros e descontos em pontos-base percentuais. Conversões usam `Decimal` com contexto local de precisão suficiente, sem aceitar separadores ambíguos, notação científica, negativos ou mais de duas casas. Não há arredondamento automático. Datas seguem ISO sem horário, conforme a origem.

Uma transação `BEGIN IMMEDIATE` abrange DDL, remoção do snapshot antigo e inserções na ordem das referências. Não usamos `executescript`, que pode confirmar transações implicitamente no modo de controle selecionado. Executamos instruções fixas individualmente. O rollback cobre erros de validação, integridade, leitura e interrupção. O banco usa `user_version = 1`; versões futuras e bancos não vazios sem versão reconhecida são recusados.

Reimportação substitui as seis tabelas integralmente; não há merge com alterações locais. O banco é um snapshot derivado e dedicado, sem outras fontes. Chaves estrangeiras permanecem ativas, inclusive durante a substituição. Leituras usam URI `mode=ro`, `query_only` e transação para consistência entre consultas de cabeçalho e itens.

Tabelas `STRICT` e `CHECK` reforçam tipos e intervalos. O par pedido/produto é a chave dos itens, pois a origem não possui identificador de item e não contém pares repetidos. Caso esse contrato mude, a importação rejeitará a ambiguidade em vez de somar quantidades ou inventar identificadores. Email não é chave e não é único: a origem contém repetição entre identificadores distintos.

Serviços internos dependem de protocolos pequenos; os adaptadores SQLite implementam os contratos. A composição é explícita, sem container de injeção ou cache. Não se adicionam endpoints de catálogo, clientes ou pedidos.

## Segurança e limites

As mensagens apresentam apenas conjunto lógico, linha, coluna e classe da falha; nunca o valor rejeitado ou SQL interno. O comando emite contagens. Projeções de pedidos omitem contatos e observações; dados privados não aparecem em `repr` das entidades pessoais. A restrição pelo par pedido/cliente não concede acesso: autenticação e autorização permanecem futuras, e o serviço deve ser chamado apenas em contexto interno confiável.

O banco e seus journals/backups ficam em `.local/`, ignorada pelo Git. A base não é criptografada; depende das permissões locais. Git ignore não é controle de acesso e não protege histórico já publicado. Não há envio de dados a serviços externos.

Não se inventa vigência de promoção: existe apenas `is_active`. Não se recalcula total de pedido com preço atual, pois não há preço histórico nos itens. A busca de nome usa uma coluna derivada sem acentos e sem distinção de caixa, preservando o nome original; substring literal usa `instr`, sem curingas de `LIKE`.

## Consequências

Instalação mantém as dependências da Fase 1. Importar exige as seis fontes completas e não vazias, UTF-8 com ou sem BOM, separadas por vírgula. A origem não é modificada. O snapshot é idempotente por conteúdo, mas não promete arquivo binário idêntico. Uma falha inicial pode deixar um arquivo SQLite vazio, sem tabelas ou dados confirmados. Migrações, histórico operacional, autenticação, extração de PDF e IA não fazem parte desta decisão.

## Referências

- [Controle transacional do sqlite3](https://docs.python.org/3/library/sqlite3.html#transaction-control).
- [Chaves estrangeiras por conexão](https://www.sqlite.org/foreignkeys.html).
