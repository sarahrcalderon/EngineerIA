from dataclasses import dataclass
from typing import Literal

from emporio_ia.dominio.excecoes import ErroDados


class ErroModelo(ErroDados):
    def __init__(self, categoria: str) -> None:
        super().__init__("Não foi possível utilizar o modelo local.")
        self.categoria = categoria


class ErroFerramenta(ErroDados):
    def __init__(self, categoria: str) -> None:
        super().__init__("A operação solicitada não foi autorizada ou confirmada.")
        self.categoria = categoria


@dataclass(frozen=True, slots=True, repr=False)
class ChamadaFerramenta:
    nome: str
    argumentos: dict[str, object]


@dataclass(frozen=True, slots=True, repr=False)
class Mensagem:
    papel: Literal["system", "user", "assistant", "tool"]
    conteudo: str
    chamadas: tuple[ChamadaFerramenta, ...] = ()
    ferramenta: str | None = None


@dataclass(frozen=True, slots=True, repr=False)
class TurnoModelo:
    conteudo: str
    chamadas: tuple[ChamadaFerramenta, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class DadoFerramenta:
    fonte: Literal["catalogo", "categorias", "promocoes", "politicas"]
    texto: str
    referencia: str
    pontuacao_bm25: float | None = None


@dataclass(frozen=True, slots=True, repr=False)
class Evidencia:
    identificador: str
    dado: DadoFerramenta


@dataclass(frozen=True, slots=True, repr=False)
class RespostaAgente:
    estado: str
    texto: str
    referencias: tuple[str, ...] = ()
    evidencias: tuple[Evidencia, ...] = ()
    categoria_erro: str | None = None
