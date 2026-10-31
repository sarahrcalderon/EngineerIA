from pathlib import Path
from typing import Protocol

from emporio_ia.dominio.busca_documental import VERSAO_BUSCA, preparar_pergunta
from emporio_ia.dominio.documentos import (
    DocumentoPoliticas,
    ResumoIndexacao,
    TrechoDocumento,
    TrechoRecuperado,
)
from emporio_ia.dominio.excecoes import ErroValidacao
from emporio_ia.dominio.segmentacao import VERSAO_SEGMENTACAO, dividir_em_trechos


class ContratoExtratorPdf(Protocol):
    def extrair_paginas(self, caminho: Path) -> DocumentoPoliticas: ...


class ContratoIndicePoliticas(Protocol):
    def substituir_documento(
        self,
        documento: DocumentoPoliticas,
        trechos: tuple[TrechoDocumento, ...],
        assinatura: str,
    ) -> ResumoIndexacao: ...

    def buscar_trechos(
        self, termos: tuple[str, ...], limite: int
    ) -> list[TrechoRecuperado]: ...


class IndexadorPoliticas:
    def __init__(
        self,
        extrator: ContratoExtratorPdf,
        indice: ContratoIndicePoliticas,
        tamanho_maximo: int = 1200,
    ) -> None:
        self.extrator = extrator
        self.indice = indice
        self.tamanho_maximo = tamanho_maximo

    def indexar(self, caminho: Path) -> ResumoIndexacao:
        documento = self.extrator.extrair_paginas(caminho)
        trechos = dividir_em_trechos(documento, self.tamanho_maximo)
        assinatura = ":".join(
            (
                documento.versao_extracao,
                VERSAO_SEGMENTACAO,
                VERSAO_BUSCA,
                str(self.tamanho_maximo),
            )
        )
        return self.indice.substituir_documento(documento, trechos, assinatura)


class ServicoRecuperacao:
    def __init__(self, indice: ContratoIndicePoliticas) -> None:
        self.indice = indice

    def recuperar_politicas(
        self, pergunta: str, limite: int = 5
    ) -> list[TrechoRecuperado]:
        if type(limite) is not int or not 1 <= limite <= 20:
            raise ErroValidacao("O limite deve estar entre 1 e 20 resultados.")
        termos = preparar_pergunta(pergunta)
        if not termos:
            return []
        return self.indice.buscar_trechos(termos, limite)
