# Visão geral da arquitetura

## Objetivos

Estabelecer uma fundação pequena, tipada, testável e local. Separar apresentação, transporte HTTP e configuração sem criar classes ou camadas sem comportamento concreto.

## Responsabilidades atuais

- Frontend: apresentação acessível, estado de conexão e nova tentativa. Componentes não conhecem detalhes do transporte.
- Serviços HTTP: URL por ambiente, cancelamento, timeout, verificação de status e validação do contrato recebido.
- API: rota de saúde e modelos Pydantic. A dependência de configuração pode ser substituída nos testes.
- Composição: fábrica FastAPI registra rotas, CORS explícito e tratamento básico de erros. Exceções não devolvem parâmetros ou conteúdo interno.
- Configuração: variáveis tipadas e validadas, com nomes e versão centralizados.
- Domínio: entidades operacionais, filtros, invariantes de conversão e exceções sem dependências de FastAPI ou SQLite.
- Aplicação: serviços internos de catálogo e pedidos dependentes de contratos de repositório.
- Infraestrutura: importador CSV transacional, tabelas SQLite e adaptadores de consulta somente para leitura. SQL permanece fora das rotas.

## Fluxo

```mermaid
sequenceDiagram
    participant Pessoa
    participant Interface
    participant API
    Pessoa->>Interface: Abre a página
    Interface->>Interface: Verificando conexão
    Interface->>API: GET /api/saude
    API-->>Interface: 200 com contrato Pydantic
    Interface-->>Pessoa: API disponível
    Note over Interface,API: Falha, timeout ou contrato inválido: API indisponível
```

Não há acesso a `data/` nesse fluxo. OpenAPI permanece disponível em `/docs` e `/openapi.json`.

## Evolução planejada

Na Fase 2, domínio, aplicação e infraestrutura estão implementados para os dados operacionais. O importador usa as conversões do domínio e grava um snapshot completo de seis conjuntos dentro de uma única transação. Os serviços internos dependem de contratos implementados pelos repositórios SQLite. A API permanece sem ligação com esses serviços. O [contrato dos dados](dados-operacionais.md) detalha modelagem e limitações.

Consultas estruturadas usam `csv`, `Decimal`, centavos inteiros e SQL parametrizado. As conexões de consulta abrem o banco em modo somente leitura e ativam chaves estrangeiras. A validação de identidade e autorização para pedidos ainda deverá anteceder qualquer exposição: filtrar pelo identificador de cliente não autentica o chamador.

Ollama será um adaptador local, sujeito à capacidade do computador. A orquestração Python controlará quais ferramentas podem ser chamadas e validará argumentos e resultados. O modelo não terá acesso irrestrito a arquivos ou SQL. Seu uso, modelo e desempenho ainda não foram validados.

A recuperação futura de políticas exigirá extração de PDF com licença adequada, fragmentos e referências verificáveis. Documentos e respostas de ferramentas serão tratados como dados não confiáveis, com controles contra instruções maliciosas. Essas estratégias permanecem propostas, sem implementação nesta fase.

## Segurança e privacidade

`/data/`, segredos, bancos e logs são ignorados. Nenhum dado real integra testes ou documentação. Não há telemetria nem serviços pagos. O frontend não recebe credenciais. CORS permite apenas origens explícitas e não substitui autenticação. O comando documentado desativa logs de acesso, que poderiam registrar parâmetros de requisição.

Os erros retornam mensagens estáveis e genéricas. Observabilidade estruturada e sanitização de logs devem ser definidas antes das integrações com dados pessoais. Não há publicação automática ou deploy nesta etapa.

## Limitações conhecidas

A saúde comprova somente que a API responde; não verifica modelos, bancos ou documentos. A disponibilidade é consultada na abertura e por nova tentativa após erro, sem monitoramento contínuo. Testes de interface usam JSDOM; verificação visual em navegador e tecnologias assistivas complementa esses testes. Persistência existe apenas localmente; não há identidade de cliente, criptografia do SQLite ou exposição HTTP dos serviços operacionais. Promoções não têm período de validade na origem e itens de pedido não têm preço histórico.
