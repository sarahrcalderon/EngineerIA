"""Entrada local: python -m emporio_ia.importar. Não cria endpoints de dados."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.excecoes import ErroDados
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.importacao import ImportadorDados


def executar() -> int:
    argumentos = argparse.ArgumentParser(
        description="Importar CSVs operacionais locais."
    )
    argumentos.add_argument("--diretorio-dados", type=Path)
    argumentos.add_argument("--banco", type=Path)
    opcoes = argumentos.parse_args()
    configuracoes = {}
    if opcoes.diretorio_dados is not None:
        configuracoes["diretorio_dados"] = opcoes.diretorio_dados
    if opcoes.banco is not None:
        configuracoes["caminho_banco"] = opcoes.banco
    try:
        configuracao = ConfiguracaoAplicacao(**configuracoes)
        importador = ImportadorDados(BancoSQLite(configuracao.caminho_banco))
        resumo = importador.importar(configuracao.diretorio_dados)
    except ValidationError:
        print("Configuração de importação inválida.", file=sys.stderr)
        return 1
    except ErroDados as erro:
        print(f"Importação cancelada: {erro}", file=sys.stderr)
        return 1
    print(json.dumps({"estado": "concluida", "registros": resumo}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
