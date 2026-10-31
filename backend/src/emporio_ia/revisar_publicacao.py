"""Exibir fingerprints para revisão local; não autoriza nem grava publicação."""

import argparse
import asyncio
import json
import sys

from pydantic import ValidationError
from pydantic_settings.exceptions import SettingsError

from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import ChamadaFerramenta
from emporio_ia.dominio.excecoes import ErroDados
from emporio_ia.dominio.publicacao import resumo_evidencia
from emporio_ia.infraestrutura.composicao_agente import criar_ferramentas


def executar() -> int:
    argumentos = argparse.ArgumentParser(
        description="Gerar metadados de evidências para revisão local."
    )
    argumentos.add_argument("ferramenta")
    argumentos.add_argument(
        "argumentos", help="Objeto JSON com argumentos da ferramenta."
    )
    opcoes = argumentos.parse_args()
    try:
        dados = json.loads(opcoes.argumentos)
        if not isinstance(dados, dict):
            raise ValueError
        ferramentas = criar_ferramentas(ConfiguracaoAplicacao())
        chamada = ferramentas.validar(ChamadaFerramenta(opcoes.ferramenta, dados))
        evidencias = asyncio.run(ferramentas.executar(chamada))
    except (ErroDados, ValueError, ValidationError, SettingsError):
        print("Não foi possível preparar a revisão local.", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "versao": 1,
                "evidencias": {
                    dado.referencia: resumo_evidencia(dado) for dado in evidencias
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
