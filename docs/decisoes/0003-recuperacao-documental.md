# ADR 0003 — Recuperação lexical de políticas com pypdf e FTS5

Estado: aceita para a Fase 3.

## Contexto

O PDF privado pode ser extraído localmente, possui oito páginas com texto e não requer OCR nesta instalação. O SQLite 3.43.1 disponível possui FTS5, verificado com criação de tabela virtual em memória. Precisamos recuperar evidências com origem verificável, sem respostas geradas ou serviços externos, preservando o banco operacional da Fase 2.

## Decisão

Usar pypdf 6.21.4, biblioteca leve sob BSD-3-Clause, sem dependências adicionais nesta instalação. O modo `layout` foi escolhido pela organização estrutural observada na inspeção local; o modo padrão fragmentava linhas em palavras. Documento sem texto não ativa OCR automaticamente, e arquivo protegido por senha é recusado.

Manter extração e persistência atrás de protocolos da aplicação. Domínio contém entidades, normalização, segmentação e termos, sem importar pypdf ou SQLite. A composição fica na CLI. Não criar rotas de documento, busca ou administração.

Segmentar por página, títulos heurísticos e parágrafos, limitando tamanho em caracteres e dividindo blocos longos entre frases. Não usar sobreposição: páginas e seções já fornecem contexto e offsets/hash permitem verificar cada ocorrência. Recusar uma frase que exceda o limite em vez de cortá-la arbitrariamente. Não declarar leitura semântica infalível de títulos, abreviações ou tabelas.

Guardar índice em banco dedicado `.local/politicas.sqlite3`. Marcar propriedade do arquivo com `application_id`, controlar versão com `user_version` e validar identidade antes de escrever. Atualizar integralmente metadados, trechos e FTS numa transação; nenhuma tabela operacional é acessada. SHA-256 binário e assinatura do processamento registram a versão de origem e parâmetros. Reindexação é idempotente por conteúdo; detecção não depende de datas do sistema de arquivos.

Usar FTS5 `unicode61 remove_diacritics 2` sobre termos do trecho e seção. Normalizar caixa, acentos, palavras comuns e plurais limitados sem usar Porter inglês ou alegar um stemmer completo de português. Construir busca conjuntiva com termos literais e SQL parametrizado. Ordenar por BM25, página e ordem; remover repetições por hash. Não usar embeddings ou depender de modelos.

Rejeitar consultas somente genéricas/numéricas e correspondências parciais: sem todos os termos significativos, retornar lista vazia. A evidência não equivale a resposta ou certeza. Não calibramos um corte de BM25 com métricas inexistentes. O filtro pode perder respostas válidas e não oferece sinônimos nem semântica.

## Consequências

Só uma biblioteca nova é necessária. O índice contém texto confidencial e exige a mesma proteção do PDF, mesmo com os dados operacionais separados. Não há cópias temporárias de conteúdo em disco; o parser processa bytes locais em memória. Logs do parser são silenciados por privacidade, com mensagens públicas sanitizadas. A investigação de arquivos problemáticos deverá ocorrer localmente sem publicar o documento.

O esquema mantém apenas o snapshot documental atual. Reindexar é uma ação explícita, inclusive após atualizar a estratégia; buscas não verificam o arquivo a cada pergunta. Citações incluem o hash do PDF para evitar confundir versões. Resultados são testados com documentos fictícios; não há métrica de qualidade semântica inventada para o corpus privado.

Ollama, roteamento entre ferramentas, geração fundamentada e controle de instruções do futuro agente permanecem para outra fase.

## Referências

- [pypdf: extração e ausência de camada semântica no PDF](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).
- [SQLite FTS5](https://www.sqlite.org/fts5.html).
- Licença BSD-3-Clause confirmada nos metadados da distribuição pypdf instalada.
