import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from emporio_ia.aplicacao.documentos import IndexadorPoliticas, ServicoRecuperacao
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.busca_documental import preparar_pergunta
from emporio_ia.dominio.documentos import (
    DocumentoPoliticas,
    ErroDocumento,
    PaginaDocumento,
)
from emporio_ia.dominio.excecoes import ErroValidacao
from emporio_ia.dominio.segmentacao import dividir_em_trechos
from emporio_ia.infraestrutura.documentos.pdf import ExtratorPdf
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos

from .conftest import gravar_pdf


def test_reindexacao_idempotente(
    indexador: IndexadorPoliticas, indice: RepositorioTrechos, pdf_sintetico: Path
) -> None:
    primeiro = indexador.indexar(pdf_sintetico)
    evidencias = ServicoRecuperacao(indice).recuperar_politicas("prazo trocas")
    segundo = indexador.indexar(pdf_sintetico)
    assert primeiro.alterado is True
    assert segundo.alterado is False
    assert primeiro.trechos == segundo.trechos
    assert ServicoRecuperacao(indice).recuperar_politicas("prazo trocas") == evidencias
    with indice.banco.conectar() as conexao:
        assert (
            conexao.execute("SELECT COUNT(*) FROM trechos").fetchone()[0]
            == segundo.trechos
        )
        assert (
            conexao.execute("SELECT COUNT(*) FROM busca_trechos").fetchone()[0]
            == segundo.trechos
        )


def test_alteracao_substitui_evidencias(
    indexador: IndexadorPoliticas, indice: RepositorioTrechos, pdf_sintetico: Path
) -> None:
    indexador.indexar(pdf_sintetico)
    anterior = ServicoRecuperacao(indice).recuperar_politicas("prazo trocas")[0]
    gravar_pdf(pdf_sintetico, ["Entregas fictícias usam apenas transporte lunar."])
    assert indexador.indexar(pdf_sintetico).alterado is True
    servico = ServicoRecuperacao(indice)
    assert servico.recuperar_politicas("prazo trocas") == []
    assert (
        servico.recuperar_politicas("transporte lunar")[0].hash_pdf != anterior.hash_pdf
    )


def test_parametros_de_segmentacao_detectam_alteracao(
    indexador: IndexadorPoliticas, indice: RepositorioTrechos, pdf_sintetico: Path
) -> None:
    indexador.indexar(pdf_sintetico)
    outro = IndexadorPoliticas(ExtratorPdf(), indice, tamanho_maximo=500)
    assert outro.indexar(pdf_sintetico).alterado is True
    assert outro.indexar(pdf_sintetico).alterado is False


def test_rollback_preserva_indice_anterior(
    recuperacao: ServicoRecuperacao, indice: RepositorioTrechos, pdf_sintetico: Path
) -> None:
    antes = recuperacao.recuperar_politicas("prazo trocas")
    documento = ExtratorPdf().extrair_paginas(pdf_sintetico)
    trechos = dividir_em_trechos(documento)
    invalidos = (*trechos[:-1], replace(trechos[-1], pagina=0))
    with pytest.raises(ErroDocumento):
        indice.substituir_documento(documento, invalidos, "teste-rollback")
    assert recuperacao.recuperar_politicas("prazo trocas") == antes


def test_falha_na_extracao_nao_apaga_indice(
    recuperacao: ServicoRecuperacao, indexador: IndexadorPoliticas, pdf_sintetico: Path
) -> None:
    antes = recuperacao.recuperar_politicas("prazo trocas")
    pdf_sintetico.write_bytes(b"corrompido")
    with pytest.raises(ErroDocumento):
        indexador.indexar(pdf_sintetico)
    assert recuperacao.recuperar_politicas("prazo trocas") == antes


@pytest.mark.parametrize(
    "pergunta", ["QUAL O PRAZO DAS TROCAS?", "qual o prazo de troca", "Prazo, troca!"]
)
def test_busca_termos_caixa_pontuacao_e_plural(
    recuperacao: ServicoRecuperacao, pergunta: str
) -> None:
    resultados = recuperacao.recuperar_politicas(pergunta)
    assert resultados
    assert all(resultado.trecho.pagina == 1 for resultado in resultados)
    assert any("17 dias" in resultado.trecho.texto for resultado in resultados)


@pytest.mark.parametrize(
    "pergunta", ["CÓDIGO RASTREAMENTO", "codigo rastreamento", "código rastreamento"]
)
def test_busca_acentos(recuperacao: ServicoRecuperacao, pergunta: str) -> None:
    resultados = recuperacao.recuperar_politicas(pergunta)
    assert resultados and resultados[0].trecho.pagina == 2
    assert resultados[0].hash_pdf


@pytest.mark.parametrize(
    "pergunta",
    ["astrobiologia marciana", "troca foguete", "qual a politica da loja", "!!!"],
)
def test_ausencia_de_evidencia_e_rejeicao_fraca(
    recuperacao: ServicoRecuperacao, pergunta: str
) -> None:
    assert recuperacao.recuperar_politicas(pergunta) == []


@pytest.mark.parametrize("pergunta", ["", "   ", "a" * 501, "texto\x00oculto"])
def test_pergunta_invalida(recuperacao: ServicoRecuperacao, pergunta: str) -> None:
    with pytest.raises(ErroValidacao):
        recuperacao.recuperar_politicas(pergunta)


@pytest.mark.parametrize("limite", [0, -1, 21, True])
def test_limite_invalido(recuperacao: ServicoRecuperacao, limite: int) -> None:
    with pytest.raises(ErroValidacao):
        recuperacao.recuperar_politicas("troca", limite)


def test_ranking_bm25_e_limite(indice: RepositorioTrechos) -> None:
    texto = (
        "Devolução devolução devolução sintética.\n\n"
        + "Devolução "
        + "contexto " * 80
        + "fictício."
    )
    documento = DocumentoPoliticas(
        "teste", "hash-ficticio", (PaginaDocumento(1, texto),), "teste"
    )
    indice.substituir_documento(documento, dividir_em_trechos(documento), "teste")
    resultados = ServicoRecuperacao(indice).recuperar_politicas("devolucoes")
    assert len(resultados) == 2
    assert resultados[0].pontuacao_bm25 <= resultados[1].pontuacao_bm25
    assert resultados[0].trecho.texto.startswith("Devolução devolução")
    assert len(ServicoRecuperacao(indice).recuperar_politicas("devolucao", 1)) == 1


def test_resultados_duplicados_sao_colapsados(indice: RepositorioTrechos) -> None:
    paginas = (
        PaginaDocumento(1, "Devolução fictícia com etiqueta violeta."),
        PaginaDocumento(2, "Devolução fictícia com etiqueta violeta."),
    )
    documento = DocumentoPoliticas("teste", "hash", paginas, "teste")
    trechos = dividir_em_trechos(documento)
    assert trechos[0].identificador != trechos[1].identificador
    indice.substituir_documento(documento, trechos, "teste")
    resultados = ServicoRecuperacao(indice).recuperar_politicas("devolucao")
    assert len(resultados) == 1
    assert resultados[0].trecho.pagina == 1


@pytest.mark.parametrize(
    "pergunta",
    [
        "' OR 1=1 --",
        "troca OR astrobiologia",
        "'; DROP TABLE trechos; --",
        '" NEAR(produto) *',
    ],
)
def test_consulta_nao_executa_sintaxe_sql_ou_fts(
    recuperacao: ServicoRecuperacao, pergunta: str
) -> None:
    assert recuperacao.recuperar_politicas(pergunta) == []
    assert recuperacao.recuperar_politicas("prazo troca")


def test_recusa_banco_operacional_sem_altera_lo(
    banco_importado, pdf_sintetico: Path
) -> None:
    antes = hashlib.sha256(banco_importado.caminho.read_bytes()).hexdigest()
    indexador = IndexadorPoliticas(ExtratorPdf(), RepositorioTrechos(banco_importado))
    with pytest.raises(ErroDocumento, match="compatível"):
        indexador.indexar(pdf_sintetico)
    assert hashlib.sha256(banco_importado.caminho.read_bytes()).hexdigest() == antes


def test_configuracao_proibe_mesmo_banco(tmp_path: Path) -> None:
    caminho = tmp_path / "operacional.sqlite3"
    with pytest.raises(ValidationError):
        ConfiguracaoAplicacao(caminho_banco=caminho, caminho_indice_politicas=caminho)


def test_termos_sem_sinonimos_ou_semantica() -> None:
    assert preparar_pergunta("Trocas e DEVOLUÇÕES") == ("troca", "devolucao")
    assert preparar_pergunta("troca trocas troca") == ("troca",)
