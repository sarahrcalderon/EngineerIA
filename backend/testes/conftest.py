"""Fixtures criadas do zero; não ler nem copiar os arquivos operacionais."""

import csv
from pathlib import Path

import pytest

from emporio_ia.aplicacao.catalogo import ServicoCatalogo
from emporio_ia.aplicacao.pedidos import ServicoPedidos
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.importacao import ImportadorDados
from emporio_ia.infraestrutura.repositorios.catalogo import (
    RepositorioCategorias,
    RepositorioPromocoes,
)
from emporio_ia.infraestrutura.repositorios.pedidos import RepositorioPedidos
from emporio_ia.infraestrutura.repositorios.produtos import RepositorioProdutos

type DadosSinteticos = dict[str, list[dict[str, str]]]


def gravar_csvs(diretorio: Path, dados: DadosSinteticos) -> None:
    diretorio.mkdir(parents=True, exist_ok=True)
    for nome, registros in dados.items():
        with (diretorio / nome).open("w", encoding="utf-8-sig", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(registros[0]))
            escritor.writeheader()
            escritor.writerows(registros)


@pytest.fixture
def dados_sinteticos() -> DadosSinteticos:
    return {
        "categories.csv": [
            {
                "category_id": "901",
                "name": "Cordas de teste",
                "description": "Sintético",
            },
            {
                "category_id": "902",
                "name": "Áudio de teste",
                "description": "Sintético",
            },
        ],
        "customers.csv": [
            {
                "customer_id": "801",
                "name": "Pessoa Sintética Alfa",
                "phone": "+00-000-0000",
                "email": "alfa@example.invalid",
                "city": "Cidade fictícia",
            },
            {
                "customer_id": "802",
                "name": "Pessoa Sintética Beta",
                "phone": "+00-000-0001",
                "email": "alfa@example.invalid",
                "city": "Cidade fictícia",
            },
        ],
        "products.csv": [
            {
                "product_id": "201",
                "price_brl": "10.10",
                "name": "Cordas Órbita Sintética",
                "category_id": "901",
                "description": "Descrição de teste",
                "stock_quantity": "3",
                "status": "active",
                "specs": "Especificação sintética",
                "created_at": "2025-01-02",
            },
            {
                "product_id": "202",
                "price_brl": "20.20",
                "name": "Amplificador Laboratório",
                "category_id": "902",
                "description": "Descrição de teste",
                "stock_quantity": "0",
                "status": "active",
                "specs": "Especificação sintética",
                "created_at": "2025-01-03",
            },
            {
                "product_id": "203",
                "price_brl": "30.30",
                "name": "Produto 100%_teste",
                "category_id": "901",
                "description": "Descrição de teste",
                "stock_quantity": "4",
                "status": "discontinued",
                "specs": "Especificação sintética",
                "created_at": "2025-01-04",
            },
            {
                "product_id": "204",
                "price_brl": "0.10",
                "name": "Produto Futuro Sintético",
                "category_id": "902",
                "description": "Descrição de teste",
                "stock_quantity": "8",
                "status": "coming_soon",
                "specs": "Especificação sintética",
                "created_at": "2025-01-05",
            },
        ],
        "orders.csv": [
            {
                "order_id": "701",
                "customer_id": "801",
                "order_date": "2025-02-03",
                "status": "pending",
                "total_brl": "20.20",
                "payment_method": "sintético",
                "tracking_code": "",
                "estimated_delivery": "",
                "notes": "",
            },
            {
                "order_id": "702",
                "customer_id": "802",
                "order_date": "2025-02-04",
                "status": "shipped",
                "total_brl": "20.20",
                "payment_method": "sintético",
                "tracking_code": "RASTREAMENTO-SINTETICO",
                "estimated_delivery": "2025-02-12",
                "notes": "Observação privada sintética",
            },
        ],
        "order_items.csv": [
            {"order_id": "701", "quantity": "2", "product_id": "201"},
            {"order_id": "702", "quantity": "1", "product_id": "202"},
        ],
        "promotions.csv": [
            {
                "promotion_id": "601",
                "product_id": "201",
                "discount_percent": "12.50",
                "description": "Sintético",
                "is_active": "1",
            },
            {
                "promotion_id": "602",
                "product_id": "202",
                "discount_percent": "10",
                "description": "Sintético",
                "is_active": "0",
            },
        ],
    }


@pytest.fixture
def diretorio_csv(tmp_path: Path, dados_sinteticos: DadosSinteticos) -> Path:
    diretorio = tmp_path / "fontes"
    gravar_csvs(diretorio, dados_sinteticos)
    return diretorio


@pytest.fixture
def banco(tmp_path: Path) -> BancoSQLite:
    return BancoSQLite(tmp_path / "privado" / "teste.sqlite3")


@pytest.fixture
def importador(banco: BancoSQLite) -> ImportadorDados:
    return ImportadorDados(banco)


@pytest.fixture
def banco_importado(banco: BancoSQLite, diretorio_csv: Path) -> BancoSQLite:
    ImportadorDados(banco).importar(diretorio_csv)
    return banco


@pytest.fixture
def catalogo(banco_importado: BancoSQLite) -> ServicoCatalogo:
    return ServicoCatalogo(
        RepositorioProdutos(banco_importado),
        RepositorioCategorias(banco_importado),
        RepositorioPromocoes(banco_importado),
    )


@pytest.fixture
def pedidos(banco_importado: BancoSQLite) -> ServicoPedidos:
    return ServicoPedidos(RepositorioPedidos(banco_importado))
