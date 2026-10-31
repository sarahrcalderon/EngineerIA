from collections import deque

import pytest

from emporio_ia.aplicacao.documentos import ServicoRecuperacao
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import Mensagem, TurnoModelo
from emporio_ia.dominio.documentos import DocumentoPoliticas, PaginaDocumento
from emporio_ia.dominio.segmentacao import dividir_em_trechos
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos
from emporio_ia.infraestrutura.ferramentas_agente import FerramentasLeitura


class ModeloSimulado:
    def __init__(self, *turnos: TurnoModelo | Exception) -> None:
        self.turnos = deque(turnos)
        self.recebidas: list[tuple[Mensagem, ...]] = []

    async def responder(self, mensagens, ferramentas) -> TurnoModelo:
        self.recebidas.append(mensagens)
        if not self.turnos:
            raise AssertionError("Simulador sem resposta programada.")
        turno = self.turnos.popleft()
        if isinstance(turno, Exception):
            raise turno
        return turno


@pytest.fixture
def configuracao_agente() -> ConfiguracaoAplicacao:
    return ConfiguracaoAplicacao(ambiente="teste")


@pytest.fixture
def ferramentas_agente(catalogo, tmp_path, configuracao_agente) -> FerramentasLeitura:
    documento = DocumentoPoliticas(
        "politicas_ficticias",
        "a" * 64,
        (
            PaginaDocumento(
                1,
                "Trocas sintéticas exigem etiqueta violeta. "
                "O prazo fictício depende da etiqueta.",
            ),
        ),
        "teste",
    )
    indice = RepositorioTrechos(BancoSQLite(tmp_path / "politicas-agente.sqlite3"))
    indice.substituir_documento(documento, dividir_em_trechos(documento), "teste")
    return FerramentasLeitura(
        catalogo,
        ServicoRecuperacao(indice),
        configuracao_agente.agente_maximo_resultados,
    )
