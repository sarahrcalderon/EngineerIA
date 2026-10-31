from dataclasses import dataclass

from emporio_ia.dominio.excecoes import ErroDados


class ErroDocumento(ErroDados):
    """Falha documental sanitizada, sem conteúdo, caminhos ou detalhes do parser."""


@dataclass(frozen=True, slots=True, repr=False)
class PaginaDocumento:
    numero: int
    texto: str


@dataclass(frozen=True, slots=True, repr=False)
class DocumentoPoliticas:
    identificador: str
    hash_pdf: str
    paginas: tuple[PaginaDocumento, ...]
    versao_extracao: str


@dataclass(frozen=True, slots=True, repr=False)
class TrechoDocumento:
    identificador: str
    documento_id: str
    pagina: int
    secao: str | None
    texto: str
    ordem: int
    inicio: int
    fim: int
    hash_conteudo: str


@dataclass(frozen=True, slots=True, repr=False)
class TrechoRecuperado:
    trecho: TrechoDocumento
    hash_pdf: str
    pontuacao_bm25: float


@dataclass(frozen=True, slots=True)
class ResumoIndexacao:
    paginas: int
    paginas_sem_texto: int
    trechos: int
    alterado: bool
