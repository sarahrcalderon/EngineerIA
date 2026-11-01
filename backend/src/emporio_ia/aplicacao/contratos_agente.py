from typing import Protocol, runtime_checkable

from emporio_ia.dominio.agente import (
    ChamadaFerramenta,
    DadoFerramenta,
    Mensagem,
    TurnoModelo,
)
from emporio_ia.dominio.publicacao import PublicacaoVisitante


class ContratoModelo(Protocol):
    async def responder(
        self, mensagens: tuple[Mensagem, ...], ferramentas: list[dict[str, object]]
    ) -> TurnoModelo: ...


class ContratoFerramentas(Protocol):
    def descrever(self) -> list[dict[str, object]]: ...

    def validar(self, chamada: ChamadaFerramenta) -> ChamadaFerramenta: ...

    async def executar(
        self, chamada: ChamadaFerramenta
    ) -> tuple[DadoFerramenta, ...]: ...


@runtime_checkable
class ContratoConsultaPublicada(Protocol):
    async def executar_publicada(
        self, chamada: ChamadaFerramenta, publicacao: PublicacaoVisitante
    ) -> tuple[DadoFerramenta, ...]: ...
