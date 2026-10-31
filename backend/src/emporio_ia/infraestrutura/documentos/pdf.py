import hashlib
import logging
import warnings
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, __version__

from emporio_ia.dominio.documentos import (
    DocumentoPoliticas,
    ErroDocumento,
    PaginaDocumento,
)
from emporio_ia.dominio.segmentacao import normalizar_texto_documental

# O parser pode registrar conteúdo de objetos PDF em avisos. Não propagá-los.
registrador_pdf = logging.getLogger("pypdf")
registrador_pdf.addHandler(logging.NullHandler())
registrador_pdf.propagate = False


class ExtratorPdf:
    def extrair_paginas(self, caminho: Path) -> DocumentoPoliticas:
        try:
            with caminho.open("rb") as arquivo:
                conteudo = arquivo.read(20 * 1024 * 1024 + 1)
            if len(conteudo) > 20 * 1024 * 1024:
                raise ErroDocumento("PDF acima do limite local de 20 MiB.")
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", module=r"pypdf(?:\..*)?")
                leitor = PdfReader(BytesIO(conteudo), strict=True)
                if leitor.is_encrypted:
                    raise ErroDocumento("PDF protegido por senha não é suportado.")
                if not 1 <= len(leitor.pages) <= 500:
                    raise ErroDocumento("PDF deve conter entre 1 e 500 páginas.")
                paginas = tuple(
                    PaginaDocumento(
                        numero,
                        normalizar_texto_documental(
                            pagina.extract_text(extraction_mode="layout") or ""
                        ),
                    )
                    for numero, pagina in enumerate(leitor.pages, 1)
                )
            if not any(pagina.texto for pagina in paginas):
                raise ErroDocumento("PDF sem texto extraível; OCR não está habilitado.")
            return DocumentoPoliticas(
                identificador="politicas_loja",
                hash_pdf=hashlib.sha256(conteudo).hexdigest(),
                paginas=paginas,
                versao_extracao=f"pypdf-{__version__}-layout-v1",
            )
        except ErroDocumento:
            raise
        except FileNotFoundError:
            raise ErroDocumento("PDF de políticas não encontrado.") from None
        except Exception:
            # Fronteira com parser externo: não deixar exceções contendo objetos PDF.
            raise ErroDocumento(
                "Não foi possível ler ou extrair o PDF local."
            ) from None
