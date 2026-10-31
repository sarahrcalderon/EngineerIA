import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from emporio_ia.aplicacao.agente import ServicoAgente
from emporio_ia.aplicacao.atendimento import ServicoAtendimentoVisitante
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import ChamadaFerramenta, TurnoModelo
from emporio_ia.dominio.documentos import DocumentoPoliticas, PaginaDocumento
from emporio_ia.dominio.publicacao import resumo_evidencia
from emporio_ia.dominio.segmentacao import dividir_em_trechos
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.composicao_agente import criar_ferramentas
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos
from emporio_ia.infraestrutura.publicacao import FerramentasVisitante, PublicacaoArquivo
from emporio_ia.principal import criar_aplicacao


class ModeloConsulta:
    def __init__(self, chamadas=None) -> None:
        self.chamadas = chamadas or (
            ChamadaFerramenta("consultar_produto", {"identificador": 201}),
        )
        self.recebidas = []

    async def responder(self, mensagens, ferramentas):
        self.recebidas.append(mensagens)
        if mensagens[-1].papel == "tool":
            ids = [
                e["identificador"]
                for m in mensagens
                if m.papel == "tool"
                for e in json.loads(m.conteudo)
            ]
            return TurnoModelo(
                json.dumps(
                    {
                        "tipo": "responder" if ids else "sem_evidencias",
                        "evidencias": ids,
                    }
                )
            )
        return TurnoModelo("", self.chamadas)


@pytest.fixture
def contexto_publico(tmp_path: Path, banco_importado):
    indice = RepositorioTrechos(BancoSQLite(tmp_path / "documentos-publicos.sqlite3"))
    doc = DocumentoPoliticas(
        "politicas_ficticias",
        "b" * 64,
        (PaginaDocumento(3, "Trocas fictícias exigem etiqueta violeta."),),
        "teste",
    )
    indice.substituir_documento(doc, dividir_em_trechos(doc), "teste")
    cfg = ConfiguracaoAplicacao(
        caminho_banco=banco_importado.caminho,
        caminho_indice_politicas=indice.banco.caminho,
        caminho_publicacao=tmp_path / "publicacao.json",
    )
    ferramentas = criar_ferramentas(cfg)
    return cfg, ferramentas


@pytest.fixture
def api_publica(contexto_publico):
    cfg, ferramentas = contexto_publico
    candidatos = [
        *ferramentas._executar(
            ferramentas.validar(
                ChamadaFerramenta("consultar_produto", {"identificador": 201})
            )
        ),
        *ferramentas._executar(
            ferramentas.validar(
                ChamadaFerramenta("buscar_politicas", {"pergunta": "troca"})
            )
        ),
        *ferramentas._executar(
            ferramentas.validar(
                ChamadaFerramenta("consultar_promocoes", {"produto_id": 201})
            )
        ),
    ]
    cfg.caminho_publicacao.write_text(
        json.dumps(
            {
                "versao": 1,
                "evidencias": {
                    dado.referencia: resumo_evidencia(dado) for dado in candidatos
                },
            }
        ),
        encoding="utf-8",
    )
    app = criar_aplicacao(cfg)
    modelos = []

    def fabricar(publicacao):
        modelo = ModeloConsulta()
        modelos.append(modelo)
        return ServicoAgente(modelo, FerramentasVisitante(ferramentas, publicacao), cfg)

    app.state.atendimento_visitante = ServicoAtendimentoVisitante(
        fabricar, PublicacaoArquivo(cfg.caminho_publicacao).carregar
    )

    async def modelo_indisponivel():
        return False

    app.state.verificar_modelo_visitante = modelo_indisponivel
    with TestClient(
        app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 50000)
    ) as cliente:
        yield cliente, app, cfg, modelos
