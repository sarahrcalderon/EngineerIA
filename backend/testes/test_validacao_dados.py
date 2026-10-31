from datetime import date
from decimal import Decimal, localcontext

import pytest

from emporio_ia.dominio.consultas import FiltroProdutos, centavos_para_decimal
from emporio_ia.dominio.excecoes import ErroValidacao
from emporio_ia.dominio.validacao import (
    normalizar_percentual,
    normalizar_preco,
    validar_data,
    validar_inteiro,
)


@pytest.mark.parametrize(
    ("entrada", "centavos"),
    [
        ("0", 0),
        ("0.10", 10),
        ("10.01", 1001),
        (" 12.5 ", 1250),
        ("92233720368547758.07", 2**63 - 1),
    ],
)
def test_valores_monetarios_exatos(entrada: str, centavos: int) -> None:
    assert normalizar_preco(entrada) == centavos
    assert centavos_para_decimal(centavos) == Decimal(entrada.strip())


@pytest.mark.parametrize(
    "entrada",
    [
        "",
        "-1",
        "-0.00",
        "1,20",
        "1.234,56",
        "1,234.56",
        "1.001",
        "1.000",
        "abc",
        "NaN",
        "Infinity",
        "1e2",
        "+1",
        "92233720368547758.08",
    ],
)
def test_rejeita_moeda_ambigua_ou_imprecisa(entrada: str) -> None:
    with pytest.raises(ErroValidacao):
        normalizar_preco(entrada)


def test_precisao_independe_do_contexto_decimal() -> None:
    with localcontext() as contexto:
        contexto.prec = 6
        assert normalizar_preco("12345678.91") == 1234567891
        assert centavos_para_decimal(1234567891) == Decimal("12345678.91")


@pytest.mark.parametrize("entrada", ["-1", "100.01", "101", "NaN", "0.001"])
def test_percentual_invalido(entrada: str) -> None:
    with pytest.raises(ErroValidacao):
        normalizar_percentual(entrada)


def test_percentual_exato() -> None:
    assert normalizar_percentual("12.50") == 1250
    assert normalizar_percentual("100") == 10000


@pytest.mark.parametrize(
    "entrada", ["2025-02-30", "03/02/2025", "20250203", "2025-02-03T10:00:00", ""]
)
def test_datas_invalidas(entrada: str) -> None:
    with pytest.raises(ErroValidacao):
        validar_data(entrada)


def test_data_valida() -> None:
    assert validar_data("2024-02-29") == date(2024, 2, 29)


@pytest.mark.parametrize("entrada", ["-1", "0", "1.0", "1e2", "abc", str(2**63)])
def test_identificador_invalido(entrada: str) -> None:
    with pytest.raises(ErroValidacao):
        validar_inteiro(entrada)


@pytest.mark.parametrize(
    "parametros",
    [
        {"limite": 201},
        {"limite": 0},
        {"limite": True},
        {"deslocamento": -1},
        {"categoria_id": 0},
        {"preco_minimo_centavos": -1},
        {"preco_minimo_centavos": 20, "preco_maximo_centavos": 10},
        {"nome": " "},
        {"disponiveis": "sim"},
    ],
)
def test_filtros_invalidos(parametros: dict) -> None:
    with pytest.raises(ErroValidacao):
        FiltroProdutos(**parametros)
