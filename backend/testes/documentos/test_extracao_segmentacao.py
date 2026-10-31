import hashlib
from pathlib import Path

import pytest

from emporio_ia.dominio.documentos import (
    DocumentoPoliticas,
    ErroDocumento,
    PaginaDocumento,
)
from emporio_ia.dominio.segmentacao import (
    dividir_em_trechos,
    normalizar_texto_documental,
)
from emporio_ia.infraestrutura.documentos.pdf import ExtratorPdf

from .conftest import gravar_pdf


def test_pdf_valido_paginas_e_hash_preservados(pdf_sintetico: Path) -> None:
    antes = pdf_sintetico.read_bytes()
    documento = ExtratorPdf().extrair_paginas(pdf_sintetico)
    assert [pagina.numero for pagina in documento.paginas] == [1, 2, 3]
    assert "17 dias" in documento.paginas[0].texto
    assert "R$ 12,34; código A-7." in documento.paginas[0].texto
    assert "23 dias" in documento.paginas[1].texto
    assert documento.hash_pdf == hashlib.sha256(antes).hexdigest()
    assert pdf_sintetico.read_bytes() == antes
    assert "17 dias" not in repr(documento)


def test_pdf_inexistente(tmp_path: Path) -> None:
    with pytest.raises(ErroDocumento, match="não encontrado"):
        ExtratorPdf().extrair_paginas(tmp_path / "ausente.pdf")


def test_pdf_corrompido_nao_vaza_conteudo(tmp_path: Path, caplog, capsys) -> None:
    caminho = tmp_path / "corrompido.pdf"
    caminho.write_bytes(b"%PDF-1.7\nsegredo-documental-sintetico\n%%EOF")
    with pytest.raises(ErroDocumento) as erro:
        ExtratorPdf().extrair_paginas(caminho)
    assert "segredo-documental" not in str(erro.value)
    assert str(tmp_path) not in str(erro.value)
    assert "segredo-documental" not in caplog.text
    assert capsys.readouterr().err == ""


def test_pdf_sem_texto_explicita_ausencia_de_ocr(tmp_path: Path) -> None:
    caminho = tmp_path / "sem-texto.pdf"
    gravar_pdf(caminho, ["", ""])
    with pytest.raises(ErroDocumento, match="OCR não está habilitado"):
        ExtratorPdf().extrair_paginas(caminho)


def test_pagina_vazia_preserva_numeracao(tmp_path: Path) -> None:
    caminho = tmp_path / "pagina-vazia.pdf"
    gravar_pdf(caminho, ["Texto inicial fictício.", "", "Texto final fictício."])
    documento = ExtratorPdf().extrair_paginas(caminho)
    assert [pagina.numero for pagina in documento.paginas] == [1, 2, 3]
    assert documento.paginas[1].texto == ""
    assert {trecho.pagina for trecho in dividir_em_trechos(documento)} == {1, 3}


def test_pdf_criptografado_nao_tenta_decriptar(tmp_path: Path) -> None:
    caminho = tmp_path / "protegido.pdf"
    gravar_pdf(caminho, ["Texto privado sintético."], senha="senha-sintetica")
    with pytest.raises(ErroDocumento, match="senha"):
        ExtratorPdf().extrair_paginas(caminho)


def test_normalizacao_preserva_valores_e_paragrafos() -> None:
    entrada = "  Taxa\t fictícia: R$  12,34; 7 dias. \n\n\n Código: A-7. \n"
    assert (
        normalizar_texto_documental(entrada)
        == "Taxa fictícia: R$ 12,34; 7 dias.\n\nCódigo: A-7."
    )


def test_trechos_estaveis_origem_e_cobertura(pdf_sintetico: Path) -> None:
    documento = ExtratorPdf().extrair_paginas(pdf_sintetico)
    primeiro = dividir_em_trechos(documento)
    assert primeiro == dividir_em_trechos(documento)
    assert len({trecho.identificador for trecho in primeiro}) == len(primeiro)
    assert [trecho.ordem for trecho in primeiro] == list(range(len(primeiro)))
    for pagina in documento.paginas:
        trechos = [trecho for trecho in primeiro if trecho.pagina == pagina.numero]
        for trecho in trechos:
            assert trecho.texto == pagina.texto[trecho.inicio : trecho.fim]
            assert (
                trecho.hash_conteudo
                == hashlib.sha256(trecho.texto.encode()).hexdigest()
            )
            assert len(trecho.texto) <= 1200
        cobertura = "".join(trecho.texto for trecho in trechos)
        assert "".join(cobertura.split()) == "".join(pagina.texto.split())
    assert any(trecho.secao == "1. Trocas Sintéticas" for trecho in primeiro)


def test_segmentacao_quebra_paragrafo_longo_apenas_entre_frases() -> None:
    frase = "Uma condição fictícia preserva o sentido completo da regra."
    texto = " ".join([frase] * 12)
    documento = DocumentoPoliticas(
        "teste", "hash", (PaginaDocumento(1, texto),), "teste"
    )
    trechos = dividir_em_trechos(documento, 200)
    assert len(trechos) > 1
    assert all(
        len(trecho.texto) <= 200 and trecho.texto.endswith(".") for trecho in trechos
    )
    assert " ".join(trecho.texto for trecho in trechos) == texto


def test_frase_longa_nao_e_cortada_nem_truncada() -> None:
    texto = ("Palavras de uma única condição extensa\n" * 12).strip() + "."
    documento = DocumentoPoliticas(
        "teste", "hash", (PaginaDocumento(1, texto),), "teste"
    )
    with pytest.raises(ErroDocumento, match="aumente"):
        dividir_em_trechos(documento, 200)


@pytest.mark.parametrize("maximo", [0, 199, 10001, True])
def test_tamanho_invalido(maximo: int, pdf_sintetico: Path) -> None:
    with pytest.raises(ErroDocumento):
        dividir_em_trechos(ExtratorPdf().extrair_paginas(pdf_sintetico), maximo)
