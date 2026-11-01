"""Interpretação conservadora de critérios explícitos, sem fatos do catálogo."""

import re

from emporio_ia.dominio.busca_produtos import normalizar_busca_produto
from emporio_ia.dominio.validacao import chave_busca

NUMEROS = {
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "tres": 3,
    "quatro": 4,
    "cinco": 5,
    "seis": 6,
    "sete": 7,
    "oito": 8,
    "nove": 9,
    "dez": 10,
}
VALOR = r"(?:r\$\s*)?(\d+(?:\.\d{3})*(?:,\d{1,2})?)"


def centavos(texto: str) -> int:
    partes = texto.replace(".", "").split(",")
    return int(partes[0]) * 100 + int(
        (partes[1] if len(partes) > 1 else "").ljust(2, "0")
    )


def interpretar_consulta_catalogo(pergunta: str) -> dict[str, object] | None:
    texto = chave_busca(pergunta)
    barato = bool(
        re.search(r"\bmais (?:barat[oa]s?|em conta)|menor(?:es)? precos?\b", texto)
    )
    caro = bool(re.search(r"\bmais car[oa]s?|maior(?:es)? precos?\b", texto))
    if barato and caro:
        return None
    quantidade = re.search(
        r"\b(\d+|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez)\s+(?:produtos?|opcoes|instrumentos?|violoes|guitarras|baixos|teclados|baterias)\b",
        texto,
    )
    faixa = re.search(r"\bentre\s+" + VALOR + r"\s+e\s+" + VALOR, texto)
    teto = re.search(r"\b(ate|menos de|abaixo de|no maximo)\s+" + VALOR, texto)
    piso = re.search(r"\b(a partir de|mais de|acima de|no minimo)\s+" + VALOR, texto)
    contexto_comercial = bool(
        re.search(
            r"r\$|\b(produtos?|instrumentos?|catalogo|precos?|custam?|violao|violoes|"
            r"guitarras?|baixos?|teclados?|baterias?|acessorios)\b",
            texto,
        )
    )
    if not contexto_comercial:
        faixa = teto = piso = None
    disponivel = contexto_comercial and bool(re.search(r"\bdisponiveis\b", texto))
    if not any((barato, caro, quantidade, faixa, teto, piso, disponivel)):
        return None
    argumentos: dict[str, object] = {}
    if quantidade:
        token = quantidade[1]
        argumentos["limite"] = min(
            20, max(1, int(token) if token.isdigit() else NUMEROS[token])
        )
    elif re.search(r"\b(?:o|a)\s+\w+\s+mais\s+(?:barato|barata|caro|cara)\b", texto):
        argumentos["limite"] = 1
    if barato or caro:
        argumentos["ordenacao"] = "preco_crescente" if barato else "preco_decrescente"
    if faixa:
        argumentos["preco_minimo_centavos"] = centavos(faixa[1])
        argumentos["preco_maximo_centavos"] = centavos(faixa[2])
    if teto:
        argumentos["preco_maximo_centavos"] = centavos(teto[2]) - (
            teto[1] in {"menos de", "abaixo de"}
        )
    if piso:
        argumentos["preco_minimo_centavos"] = centavos(piso[2]) + (
            piso[1] in {"mais de", "acima de"}
        )
    if disponivel:
        argumentos["disponiveis"] = True
    instrumento = re.search(
        r"\b(violao|violoes|guitarras?|baixos?|teclados?|baterias?|acessorios)\b", texto
    )
    if instrumento:
        argumentos["termo"] = normalizar_busca_produto(instrumento[1])
    categoria = re.search(
        r"\bcategoria\s+(.+?)(?=\s+(?:com|ate|entre|mais|disponiveis|que)\b|[?.!]|$)",
        texto,
    )
    if categoria:
        argumentos["categoria"] = categoria[1].strip()
    return argumentos


def introducao_catalogo(argumentos: dict[str, object]) -> str:
    if argumentos.get("ordenacao") == "preco_crescente":
        return "Encontrei estas opções com os menores preços do catálogo autorizado:"
    if argumentos.get("ordenacao") == "preco_decrescente":
        return "Encontrei estas opções com os maiores preços do catálogo autorizado:"
    return "Encontrei estas opções que atendem aos critérios da sua consulta:"
