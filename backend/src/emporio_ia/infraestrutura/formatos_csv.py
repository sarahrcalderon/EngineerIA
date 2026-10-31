"""Mapeamento explícito dos cabeçalhos externos para as colunas internas."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from emporio_ia.dominio.validacao import (
    normalizar_percentual,
    normalizar_preco,
    validar_booleano,
    validar_data,
    validar_data_opcional,
    validar_inteiro,
    validar_opcional,
    validar_texto,
)

type ValorConvertido = str | int | bool | date | None


@dataclass(frozen=True, slots=True)
class CampoCsv:
    cabecalho: str
    converter: Callable[[str], ValorConvertido]


@dataclass(frozen=True, slots=True)
class FormatoCsv:
    nome_arquivo: str
    nome_conjunto: str
    campos: tuple[CampoCsv, ...]
    inserir_sql: str
    posicoes_chave: tuple[int, ...] = (0,)


def validar_estoque(valor: str) -> int:
    return validar_inteiro(valor, minimo=0)


FORMATOS = (
    FormatoCsv(
        "categories.csv",
        "categorias",
        (
            CampoCsv("category_id", validar_inteiro),
            CampoCsv("name", validar_texto),
            CampoCsv("description", validar_texto),
        ),
        "INSERT INTO categorias (identificador, nome, descricao) VALUES (?, ?, ?)",
    ),
    FormatoCsv(
        "customers.csv",
        "clientes",
        (
            CampoCsv("customer_id", validar_inteiro),
            CampoCsv("name", validar_texto),
            CampoCsv("phone", validar_texto),
            CampoCsv("email", validar_texto),
            CampoCsv("city", validar_texto),
        ),
        """INSERT INTO clientes (identificador, nome, telefone, email, cidade)
           VALUES (?, ?, ?, ?, ?)""",
    ),
    FormatoCsv(
        "products.csv",
        "produtos",
        (
            CampoCsv("product_id", validar_inteiro),
            CampoCsv("price_brl", normalizar_preco),
            CampoCsv("name", validar_texto),
            CampoCsv("category_id", validar_inteiro),
            CampoCsv("description", validar_texto),
            CampoCsv("stock_quantity", validar_estoque),
            CampoCsv("status", validar_texto),
            CampoCsv("specs", validar_texto),
            CampoCsv("created_at", validar_data),
        ),
        """INSERT INTO produtos (
            identificador, preco_centavos, nome, categoria_id, descricao,
            quantidade_estoque, estado, especificacoes, criado_em, nome_busca
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ),
    FormatoCsv(
        "orders.csv",
        "pedidos",
        (
            CampoCsv("order_id", validar_inteiro),
            CampoCsv("customer_id", validar_inteiro),
            CampoCsv("order_date", validar_data),
            CampoCsv("status", validar_texto),
            CampoCsv("total_brl", normalizar_preco),
            CampoCsv("payment_method", validar_texto),
            CampoCsv("tracking_code", validar_opcional),
            CampoCsv("estimated_delivery", validar_data_opcional),
            CampoCsv("notes", validar_opcional),
        ),
        """INSERT INTO pedidos (
            identificador, cliente_id, data_pedido, estado, total_centavos,
            meio_pagamento, codigo_rastreamento, entrega_estimada, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    ),
    FormatoCsv(
        "order_items.csv",
        "itens_pedido",
        (
            CampoCsv("order_id", validar_inteiro),
            CampoCsv("quantity", validar_inteiro),
            CampoCsv("product_id", validar_inteiro),
        ),
        """INSERT INTO itens_pedido (pedido_id, quantidade, produto_id)
           VALUES (?, ?, ?)""",
        posicoes_chave=(0, 2),
    ),
    FormatoCsv(
        "promotions.csv",
        "promocoes",
        (
            CampoCsv("promotion_id", validar_inteiro),
            CampoCsv("product_id", validar_inteiro),
            CampoCsv("discount_percent", normalizar_percentual),
            CampoCsv("description", validar_texto),
            CampoCsv("is_active", validar_booleano),
        ),
        """INSERT INTO promocoes (
            identificador, produto_id, desconto_pontos_base, descricao, ativa
        ) VALUES (?, ?, ?, ?, ?)""",
    ),
)
