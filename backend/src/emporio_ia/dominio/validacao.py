"""Conversões estritas: não adivinhar formatos nem arredondar dados de origem."""

import re
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext

from emporio_ia.dominio.excecoes import ErroValidacao

LIMITE_INTEIRO = 2**63 - 1


def normalizar_texto(valor: str) -> str:
    return unicodedata.normalize("NFC", valor.strip())


def chave_busca(valor: str) -> str:
    decomposto = unicodedata.normalize("NFKD", valor)
    return "".join(
        letra for letra in decomposto if not unicodedata.combining(letra)
    ).casefold()


def validar_texto(valor: str) -> str:
    texto = normalizar_texto(valor)
    if not texto or "\x00" in texto:
        raise ErroValidacao("Texto obrigatório ausente ou inválido.")
    return texto


def validar_opcional(valor: str) -> str | None:
    return validar_texto(valor) if valor.strip() else None


def validar_inteiro(valor: str, *, minimo: int = 1) -> int:
    texto = valor.strip()
    if not re.fullmatch(r"[0-9]+", texto):
        raise ErroValidacao("Inteiro inválido.")
    try:
        numero = int(texto)
    except ValueError:
        raise ErroValidacao("Inteiro fora do limite suportado.") from None
    if numero < minimo or numero > LIMITE_INTEIRO:
        raise ErroValidacao("Inteiro fora do intervalo permitido.")
    return numero


def converter_decimal_exato(valor: str, *, maximo: Decimal | None = None) -> int:
    texto = valor.strip()
    # Ponto decimal observado nos arquivos; não aceitar milhares, vírgula ou expoentes.
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", texto):
        raise ErroValidacao("Decimal inválido; use ponto e até duas casas decimais.")
    try:
        with localcontext() as contexto:
            contexto.prec = 40
            numero = Decimal(texto)
            if numero > Decimal(LIMITE_INTEIRO) / 100:
                raise ErroValidacao("Decimal fora do limite suportado.")
            if maximo is not None and numero > maximo:
                raise ErroValidacao("Decimal fora do intervalo permitido.")
            return int(numero * 100)
    except (InvalidOperation, ValueError, OverflowError):
        raise ErroValidacao("Decimal inválido.") from None


def normalizar_preco(valor: str) -> int:
    """Converter reais em centavos exatos, sem uso de float."""
    return converter_decimal_exato(valor)


def normalizar_percentual(valor: str) -> int:
    """Preservar duas casas percentuais como pontos-base (100% = 10000)."""
    return converter_decimal_exato(valor, maximo=Decimal(100))


def validar_data(valor: str) -> date:
    texto = valor.strip()
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", texto):
        raise ErroValidacao("Data inválida; use AAAA-MM-DD.")
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ErroValidacao("Data de calendário inválida.") from None


def validar_data_opcional(valor: str) -> date | None:
    return validar_data(valor) if valor.strip() else None


def validar_booleano(valor: str) -> bool:
    if valor.strip() not in {"0", "1"}:
        raise ErroValidacao("Indicador booleano deve ser 0 ou 1.")
    return valor.strip() == "1"
