import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.principal import criar_aplicacao


@pytest.fixture
def cliente():
    with TestClient(
        criar_aplicacao(ConfiguracaoAplicacao(ambiente="teste"))
    ) as cliente:
        yield cliente


def test_saude(cliente):
    resposta = cliente.get("/api/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "estado": "disponivel",
        "servico": "Emporio IA",
        "versao": "0.1.0",
    }


def test_openapi(cliente):
    resposta = cliente.get("/openapi.json")
    assert resposta.status_code == 200
    assert "/api/saude" in resposta.json()["paths"]
    assert cliente.get("/docs").status_code == 200


def test_rota_inexistente(cliente):
    resposta = cliente.get("/inexistente")
    assert resposta.status_code == 404
    assert resposta.json() == {"detalhe": "Recurso não encontrado."}


@pytest.mark.parametrize(
    ("origem", "permitida"),
    [("http://localhost:5173", True), ("https://origem-invalida.example", False)],
)
def test_cors(cliente, origem, permitida):
    resposta = cliente.options(
        "/api/saude",
        headers={"Origin": origem, "Access-Control-Request-Method": "GET"},
    )
    assert (resposta.status_code == 200) is permitida
    assert (resposta.headers.get("access-control-allow-origin") == origem) is permitida


def test_configuracao_por_ambiente(monkeypatch):
    monkeypatch.setenv("EMPORIO_ORIGENS_CORS", '["https://loja.example"]')
    assert ConfiguracaoAplicacao().origens_cors == ["https://loja.example"]


def test_cors_rejeita_curinga():
    with pytest.raises(ValidationError):
        ConfiguracaoAplicacao(origens_cors=["*"])


def test_erro_interno_nao_expoe_detalhes():
    aplicacao = criar_aplicacao()

    @aplicacao.get("/falha-teste")
    def provocar_falha():
        raise RuntimeError("conteudo-privado-de-teste")

    with TestClient(aplicacao, raise_server_exceptions=False) as cliente:
        resposta = cliente.get("/falha-teste")
    assert resposta.status_code == 500
    assert resposta.json() == {"detalhe": "Erro interno do serviço."}
