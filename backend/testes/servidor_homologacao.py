"""Servidor optativo com agente real e fontes exclusivamente fictícias.

Executar com o Python do ambiente virtual: não faz parte da aplicação operacional.
"""

import argparse
import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from conftest import dados_sinteticos, gravar_csvs

from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import ChamadaFerramenta
from emporio_ia.dominio.documentos import DocumentoPoliticas, PaginaDocumento
from emporio_ia.dominio.publicacao import resumo_evidencia
from emporio_ia.dominio.segmentacao import dividir_em_trechos
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.composicao_agente import criar_ferramentas
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos
from emporio_ia.infraestrutura.importacao import ImportadorDados
from emporio_ia.principal import criar_aplicacao


def criar_contexto_ficticio(base: Path) -> ConfiguracaoAplicacao:
    gravar_csvs(base / "fontes", dados_sinteticos.__wrapped__())
    banco = BancoSQLite(base / "operacional.sqlite3")
    ImportadorDados(banco).importar(base / "fontes")
    indice = RepositorioTrechos(BancoSQLite(base / "politicas.sqlite3"))
    documento = DocumentoPoliticas(
        "politicas_ficticias",
        "f" * 64,
        (
            PaginaDocumento(
                3,
                "Trocas fictícias exigem etiqueta violeta. "
                "O prazo fictício é de 17 dias.",
            ),
        ),
        "teste",
    )
    indice.substituir_documento(
        documento, dividir_em_trechos(documento), "homologacao-ficticia"
    )
    cfg = ConfiguracaoAplicacao(
        caminho_banco=banco.caminho,
        caminho_indice_politicas=indice.banco.caminho,
        caminho_publicacao=base / "publicacao.json",
        origens_cors=["http://127.0.0.1:5175", "http://localhost:5175"],
    )
    ferramentas = criar_ferramentas(cfg)
    evidencias = []
    for chamada in (
        ChamadaFerramenta("consultar_produto", {"identificador": 201}),
        ChamadaFerramenta("consultar_produto", {"identificador": 202}),
        ChamadaFerramenta("consultar_categorias", {}),
        ChamadaFerramenta("consultar_promocoes", {}),
        ChamadaFerramenta("buscar_politicas", {"pergunta": "troca"}),
    ):
        evidencias.extend(asyncio.run(ferramentas.executar(chamada)))
    cfg.caminho_publicacao.write_text(
        json.dumps(
            {
                "versao": 1,
                "evidencias": {
                    dado.referencia: resumo_evidencia(dado) for dado in evidencias
                },
            }
        ),
        encoding="utf-8",
    )
    return cfg


def executar() -> None:
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--porta", type=int, default=8005)
    opcoes = argumentos.parse_args()
    if not 1024 <= opcoes.porta <= 65535:
        argumentos.error("A porta deve estar entre 1024 e 65535.")
    with TemporaryDirectory(prefix="engineeria-homologacao-") as temporario:
        cfg = criar_contexto_ficticio(Path(temporario))
        print("Homologação isolada: fontes fictícias e Ollama real, somente loopback.")
        uvicorn.run(
            criar_aplicacao(cfg),
            host="127.0.0.1",
            port=opcoes.porta,
            access_log=False,
        )


if __name__ == "__main__":
    executar()
