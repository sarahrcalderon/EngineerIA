"""Comando local de indexação. Não imprime texto nem cria rotas HTTP."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from pydantic import ValidationError
from pydantic_settings.exceptions import SettingsError

from emporio_ia.aplicacao.documentos import IndexadorPoliticas
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.excecoes import ErroDados
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.documentos.pdf import ExtratorPdf
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos


def executar() -> int:
    argumentos = argparse.ArgumentParser(
        description="Indexar políticas locais com FTS5."
    )
    argumentos.add_argument("--pdf", type=Path)
    argumentos.add_argument("--indice", type=Path)
    argumentos.add_argument("--tamanho-maximo", type=int)
    opcoes = argumentos.parse_args()
    configuracoes = {
        nome: valor
        for nome, valor in (
            ("caminho_pdf_politicas", opcoes.pdf),
            ("caminho_indice_politicas", opcoes.indice),
            ("tamanho_maximo_trecho", opcoes.tamanho_maximo),
        )
        if valor is not None
    }
    try:
        configuracao = ConfiguracaoAplicacao(**configuracoes)
        indice = RepositorioTrechos(BancoSQLite(configuracao.caminho_indice_politicas))
        indexador = IndexadorPoliticas(
            ExtratorPdf(), indice, configuracao.tamanho_maximo_trecho
        )
        resumo = indexador.indexar(configuracao.caminho_pdf_politicas)
    except (ValidationError, SettingsError):
        print("Configuração documental inválida.", file=sys.stderr)
        return 1
    except ErroDados as erro:
        print(f"Indexação cancelada: {erro}", file=sys.stderr)
        return 1
    print(json.dumps({"estado": "concluida", **asdict(resumo)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
