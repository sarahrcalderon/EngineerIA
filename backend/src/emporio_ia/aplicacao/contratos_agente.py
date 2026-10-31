from typing import Protocol

from emporio_ia.dominio.agente import (
    ChamadaFerramenta,
    DadoFerramenta,
    Mensagem,
    TurnoModelo,
)


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
