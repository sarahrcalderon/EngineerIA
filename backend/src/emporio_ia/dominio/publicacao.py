import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from emporio_ia.dominio.agente import DadoFerramenta
from emporio_ia.dominio.excecoes import ErroDados


class ErroPublicacao(ErroDados):
    """A publicação de dados para visitantes não pôde ser autorizada."""


def resumo_evidencia(dado: DadoFerramenta) -> str:
    conteudo = json.dumps(
        [dado.fonte, dado.texto, dado.referencia],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(conteudo.encode()).hexdigest()


def referencia_permitida(dado: DadoFerramenta) -> bool:
    prefixos = {
        "catalogo": "produto",
        "categorias": "categoria",
        "promocoes": "promocao",
    }
    if dado.fonte in prefixos:
        return bool(
            re.fullmatch(rf"{prefixos[dado.fonte]}:[1-9][0-9]*", dado.referencia)
        )
    return dado.fonte == "politicas" and bool(
        re.fullmatch(
            r"[a-z_]+:[a-f0-9]{64}:pagina=[1-9][0-9]{0,2}:trecho=[a-f0-9]{64}",
            dado.referencia,
        )
    )


@dataclass(frozen=True, slots=True, repr=False)
class PublicacaoVisitante:
    autorizadas: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "autorizadas", MappingProxyType(dict(self.autorizadas))
        )

    def permite(self, dado: DadoFerramenta) -> bool:
        return referencia_permitida(dado) and self.autorizadas.get(
            dado.referencia
        ) == resumo_evidencia(dado)


@dataclass(frozen=True, slots=True)
class ReferenciaVisitante:
    tipo: str
    titulo: str
    pagina: int | None = None


@dataclass(frozen=True, slots=True, repr=False)
class RespostaVisitante:
    estado: str
    resposta: str
    referencias: tuple[ReferenciaVisitante, ...] = ()
    categoria_erro: str | None = None
