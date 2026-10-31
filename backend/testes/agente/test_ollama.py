import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import ErroModelo, Mensagem
from emporio_ia.infraestrutura.ollama import AdaptadorOllama


def executar_chat(
    retorno=None,
    *,
    status=200,
    capacidades=None,
    erro=None,
    configuracao=None,
    mensagens=None,
):
    recebidas = []

    def tratar(requisicao):
        recebidas.append(requisicao)
        if erro is not None:
            raise erro
        if requisicao.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.12.0"})
        if requisicao.url.path == "/api/show":
            return httpx.Response(
                200,
                json=capacidades
                if capacidades is not None
                else {"capabilities": ["tools", "thinking"]},
            )
        return httpx.Response(
            status,
            content=retorno
            if isinstance(retorno, bytes)
            else json.dumps(
                retorno
                or {
                    "message": {
                        "role": "assistant",
                        "content": '{"tipo":"esclarecer","evidencias":[]}',
                    },
                    "done": True,
                }
            ),
        )

    adaptador = AdaptadorOllama(
        configuracao or ConfiguracaoAplicacao(), httpx.MockTransport(tratar)
    )
    return asyncio.run(
        adaptador.responder(mensagens or (Mensagem("user", "Pergunta fictícia"),), [])
    ), recebidas


def test_api_protocolo_local_sem_streaming():
    turno, recebidas = executar_chat()
    assert turno.conteudo
    dados = json.loads(recebidas[-1].content)
    assert dados["stream"] is False and dados["think"] is False
    assert dados["options"]["temperature"] == 0
    assert dados["model"] == "qwen3:4b"
    assert all(requisicao.url.host == "127.0.0.1" for requisicao in recebidas)


def test_finalizacao_restringe_escolha_as_evidencias_recebidas():
    _, recebidas = executar_chat(
        mensagens=(
            Mensagem("system", "Instrução fictícia"),
            Mensagem(
                "tool", json.dumps([{"identificador": "E1"}, {"identificador": "E2"}])
            ),
        )
    )
    dados = json.loads(recebidas[-1].content)
    assert dados["messages"][0]["content"].endswith("/no_think")
    evidencias = dados["format"]["properties"]["evidencias"]
    assert evidencias["items"]["enum"] == ["E1", "E2"]
    assert evidencias["maxItems"] == 2
    assert "resposta" not in dados["format"]["properties"]


def test_disponibilidade_verifica_metadados_sem_gerar_resposta():
    recebidas = []

    def tratar(requisicao):
        recebidas.append(requisicao.url.path)
        if requisicao.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.40.13"})
        assert requisicao.url.path == "/api/show"
        return httpx.Response(200, json={"capabilities": ["tools"]})

    adaptador = AdaptadorOllama(ConfiguracaoAplicacao(), httpx.MockTransport(tratar))
    assert asyncio.run(adaptador.verificar_disponibilidade())
    assert recebidas == ["/api/version", "/api/show"]


def test_interpreta_ferramentas():
    turno, _ = executar_chat(
        {
            "done": True,
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "consultar_produto",
                            "arguments": {"identificador": 201},
                        }
                    }
                ],
            },
        }
    )
    assert turno.chamadas[0].nome == "consultar_produto"


@pytest.mark.parametrize(
    "retorno",
    [
        b"invalido",
        b"[]",
        {"error": "detalhe-privado"},
        {"done": False},
        {"done": True, "message": {"role": "system", "content": "vazamento"}},
        {"done": True, "message": {"role": "assistant", "content": 12}},
        {
            "done": True,
            "message": {
                "role": "assistant",
                "tool_calls": [{"function": {"name": "sql", "arguments": "valor"}}],
            },
        },
    ],
)
def test_resposta_malformada(retorno):
    with pytest.raises(ErroModelo):
        executar_chat(retorno)


@pytest.mark.parametrize("status", [404, 500, 302])
def test_http_erro_sem_corpo(status):
    with pytest.raises(ErroModelo) as erro:
        executar_chat(b"segredo-privado", status=status)
    assert "segredo" not in str(erro.value)


@pytest.mark.parametrize(
    "erro", [httpx.ConnectError("segredo"), httpx.ReadTimeout("segredo")]
)
def test_conexao_timeout_sanitizados(erro):
    with pytest.raises(ErroModelo) as capturado:
        executar_chat(erro=erro)
    assert "segredo" not in str(capturado.value)


@pytest.mark.parametrize(
    "capacidades",
    [
        {"capabilities": []},
        {"capabilities": ["tools"], "remote_host": "https://externo.example"},
        {"capabilities": ["tools"], "remote_model": "modelo-remoto"},
    ],
)
def test_recusa_modelo_incompativel_ou_remoto(capacidades):
    with pytest.raises(ErroModelo):
        executar_chat(capacidades=capacidades)


def test_resposta_tem_limite_de_bytes():
    configuracao = ConfiguracaoAplicacao(agente_resposta_bytes=1024)
    with pytest.raises(ErroModelo, match="modelo local"):
        executar_chat(b"x" * 2048, configuracao=configuracao)


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example",
        "http://192.168.0.1:11434",
        "http://127.0.0.1:11434/externo",
        "http://usuario:senha@localhost:11434",
        "http://localhost:11434?x=1",
    ],
)
def test_url_ollama_restrita_a_loopback(url):
    with pytest.raises(ValidationError):
        ConfiguracaoAplicacao(ollama_url=url)


def test_configuracao_normaliza_localhost_e_recusa_cloud():
    assert (
        ConfiguracaoAplicacao(ollama_url="http://localhost:11434").ollama_url
        == "http://127.0.0.1:11434"
    )
    with pytest.raises(ValidationError):
        ConfiguracaoAplicacao(ollama_modelo="modelo:cloud")


def test_erro_de_configuracao_nao_reproduz_credenciais():
    with pytest.raises(ValidationError) as erro:
        ConfiguracaoAplicacao(ollama_url="http://usuario:credencial-secreta@localhost")
    assert "credencial-secreta" not in str(erro.value)
