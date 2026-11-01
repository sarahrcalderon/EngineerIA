"""Normalização de busca, sem alterar nomes ou valores armazenados."""

import re

from emporio_ia.dominio.busca_documental import normalizar_plural
from emporio_ia.dominio.validacao import chave_busca


def normalizar_busca_produto(texto: str) -> str:
    # Preservar pontuação literal: % e _ nunca se tornam curingas.
    return re.sub(
        r"[^\W_]+",
        lambda palavra: normalizar_plural(palavra.group()),
        chave_busca(texto.strip()),
    )
