"""DDL fixo; executado instrução por instrução dentro da transação de importação."""

VERSAO_ESQUEMA = 1

INSTRUCOES_ESQUEMA = (
    """CREATE TABLE IF NOT EXISTS categorias (
        identificador INTEGER PRIMARY KEY CHECK (identificador > 0),
        nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
        descricao TEXT NOT NULL CHECK (length(trim(descricao)) > 0)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS clientes (
        identificador INTEGER PRIMARY KEY CHECK (identificador > 0),
        nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
        telefone TEXT NOT NULL CHECK (length(trim(telefone)) > 0),
        email TEXT NOT NULL CHECK (length(trim(email)) > 0),
        cidade TEXT NOT NULL CHECK (length(trim(cidade)) > 0)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS produtos (
        identificador INTEGER PRIMARY KEY CHECK (identificador > 0),
        preco_centavos INTEGER NOT NULL CHECK (preco_centavos >= 0),
        nome TEXT NOT NULL CHECK (length(trim(nome)) > 0),
        nome_busca TEXT NOT NULL,
        categoria_id INTEGER NOT NULL REFERENCES categorias(identificador),
        descricao TEXT NOT NULL CHECK (length(trim(descricao)) > 0),
        quantidade_estoque INTEGER NOT NULL CHECK (quantidade_estoque >= 0),
        estado TEXT NOT NULL CHECK (length(trim(estado)) > 0),
        especificacoes TEXT NOT NULL CHECK (length(trim(especificacoes)) > 0),
        criado_em TEXT NOT NULL
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS pedidos (
        identificador INTEGER PRIMARY KEY CHECK (identificador > 0),
        cliente_id INTEGER NOT NULL REFERENCES clientes(identificador),
        data_pedido TEXT NOT NULL,
        estado TEXT NOT NULL CHECK (length(trim(estado)) > 0),
        total_centavos INTEGER NOT NULL CHECK (total_centavos >= 0),
        meio_pagamento TEXT NOT NULL CHECK (length(trim(meio_pagamento)) > 0),
        codigo_rastreamento TEXT,
        entrega_estimada TEXT,
        observacoes TEXT
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS itens_pedido (
        pedido_id INTEGER NOT NULL REFERENCES pedidos(identificador),
        quantidade INTEGER NOT NULL CHECK (quantidade > 0),
        produto_id INTEGER NOT NULL REFERENCES produtos(identificador),
        PRIMARY KEY (pedido_id, produto_id)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS promocoes (
        identificador INTEGER PRIMARY KEY CHECK (identificador > 0),
        produto_id INTEGER NOT NULL REFERENCES produtos(identificador),
        desconto_pontos_base INTEGER NOT NULL
            CHECK (desconto_pontos_base BETWEEN 0 AND 10000),
        descricao TEXT NOT NULL CHECK (length(trim(descricao)) > 0),
        ativa INTEGER NOT NULL CHECK (ativa IN (0, 1))
    ) STRICT""",
    "CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria_id)",
    "CREATE INDEX IF NOT EXISTS idx_produtos_preco ON produtos(preco_centavos)",
    "CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id)",
    "CREATE INDEX IF NOT EXISTS idx_itens_produto ON itens_pedido(produto_id)",
    "CREATE INDEX IF NOT EXISTS idx_promocoes_produto ON promocoes(produto_id)",
)

# Filhos primeiro: não desativar foreign_keys durante a substituição do snapshot.
INSTRUCOES_LIMPEZA = (
    "DELETE FROM promocoes",
    "DELETE FROM itens_pedido",
    "DELETE FROM pedidos",
    "DELETE FROM produtos",
    "DELETE FROM clientes",
    "DELETE FROM categorias",
)
