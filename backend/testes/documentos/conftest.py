"""PDFs mínimos criados em memória com texto fictício, sem fontes privadas."""

from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from emporio_ia.aplicacao.documentos import IndexadorPoliticas, ServicoRecuperacao
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.documentos.pdf import ExtratorPdf
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos


def gravar_pdf(caminho: Path, paginas: list[str], *, senha: str | None = None) -> None:
    escritor = PdfWriter()
    for texto in paginas:
        pagina = escritor.add_blank_page(width=595, height=842)
        if not texto:
            continue
        fonte = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
                NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
            }
        )
        pagina[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): fonte})}
        )
        comandos = ["BT /F1 12 Tf 36 790 Td"]
        for linha in texto.splitlines():
            hexadecimal = linha.encode("cp1252").hex()
            comandos.append(f"<{hexadecimal}> Tj")
            comandos.append("0 -16 Td")
        comandos.append("ET")
        fluxo = DecodedStreamObject()
        fluxo.set_data("\n".join(comandos).encode("ascii"))
        pagina[NameObject("/Contents")] = escritor._add_object(fluxo)
    if senha is not None:
        escritor.encrypt(senha)
    with caminho.open("wb") as arquivo:
        escritor.write(arquivo)


@pytest.fixture
def pdf_sintetico(tmp_path: Path) -> Path:
    caminho = tmp_path / "politicas-ficticias.pdf"
    gravar_pdf(
        caminho,
        [
            "1. Trocas Sintéticas\n\n"
            "As trocas experimentais exigem o comprovante original.\n"
            "O prazo fictício é de 17 dias corridos.\n\n"
            "Taxa sintética: R$ 12,34; código A-7.",
            "2. Entregas Sintéticas\n\n"
            "As entregas do laboratório ocorrem em 23 dias úteis.\n\n"
            "A embalagem azul acompanha um código de rastreamento fictício.",
            "3. Garantias Sintéticas\n\n"
            "A garantia experimental cobre apenas falhas de fabricação.\n\n"
            "O certificado lilás deve acompanhar o produto sintético.",
        ],
    )
    return caminho


@pytest.fixture
def indice(tmp_path: Path) -> RepositorioTrechos:
    return RepositorioTrechos(BancoSQLite(tmp_path / "indice.sqlite3"))


@pytest.fixture
def indexador(indice: RepositorioTrechos) -> IndexadorPoliticas:
    return IndexadorPoliticas(ExtratorPdf(), indice)


@pytest.fixture
def recuperacao(
    indexador: IndexadorPoliticas, indice: RepositorioTrechos, pdf_sintetico: Path
) -> ServicoRecuperacao:
    indexador.indexar(pdf_sintetico)
    return ServicoRecuperacao(indice)
