import asyncio
import json

import httpx
import pytest

from emporio_ia.aplicacao.agente import ServicoAgente
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import ErroModelo, Mensagem, TurnoModelo
from emporio_ia.infraestrutura.ollama import AdaptadorOllama
from emporio_ia.infraestrutura.selecao_ollama import interpretar_evidencias


def consultar(conteudo, ferramentas, *, termino="stop"):
    recebidas = []

    def responder(requisicao):
        if requisicao.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.40.13"})
        if requisicao.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["tools", "thinking"]})
        recebidas.append(json.loads(requisicao.content))
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": termino,
                "message": {"role": "assistant", "content": conteudo},
            },
        )

    adaptador = AdaptadorOllama(ConfiguracaoAplicacao(), httpx.MockTransport(responder))
    turno = asyncio.run(
        adaptador.responder(
            (Mensagem("system", "Instrução fictícia"), Mensagem("user", "Promoções?")),
            ferramentas.descrever(),
        )
    )
    return turno, recebidas[0]


def test_selecao_estruturada_executa_mesmo_contrato(ferramentas_agente):
    turno, payload = consultar(
        '{"nome":"consultar_promocoes","argumentos":{}}', ferramentas_agente
    )
    assert len(turno.chamadas) == 1
    chamada = ferramentas_agente.validar(turno.chamadas[0])
    assert chamada.nome == "consultar_promocoes"
    assert payload["tools"] == []
    assert "oneOf" in payload["format"]
    assert payload["think"] is False


@pytest.mark.parametrize(
    "conteudo",
    [
        '{"nome":"executar_sql","argumentos":{}}',
        '{"nome":"consultar_promocoes","argumentos":"sql"}',
        '{"nome":"consultar_promocoes","argumentos":{},"texto":"inventado"}',
        "Vou consultar as promoções.",
        '{"tipo":"responder","evidencias":["E999"]}',
    ],
)
def test_selecao_recusa_conteudo_fora_do_esquema(conteudo, ferramentas_agente):
    with pytest.raises(ErroModelo):
        consultar(conteudo, ferramentas_agente)


def test_corte_de_geracao_tem_categoria_propria(ferramentas_agente):
    with pytest.raises(ErroModelo) as erro:
        consultar(
            '{"nome":"consultar_promocoes"}', ferramentas_agente, termino="length"
        )
    assert erro.value.categoria == "geracao_interrompida"


def test_combinada_preserva_evidencias_em_selecoes_sequenciais(ferramentas_agente):
    conteudos = iter(
        [
            '{"nome":"consultar_produto","argumentos":{"identificador":201}}',
            '{"nome":"buscar_politicas","argumentos":{"pergunta":"troca"}}',
            '{"evidencias":["E1","E2"]}',
        ]
    )
    geracoes = []

    def responder(requisicao):
        if requisicao.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.40.13"})
        if requisicao.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["tools"]})
        geracoes.append(json.loads(requisicao.content))
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": "stop",
                "message": {"role": "assistant", "content": next(conteudos)},
            },
        )

    cfg = ConfiguracaoAplicacao()
    modelo = AdaptadorOllama(cfg, httpx.MockTransport(responder))
    resposta = asyncio.run(
        ServicoAgente(modelo, ferramentas_agente, cfg).processar_pergunta(
            "Qual o preço do produto 201 e a política de troca?"
        )
    )
    assert resposta.estado == "fundamentada"
    assert {e.dado.fonte for e in resposta.evidencias} == {"catalogo", "politicas"}
    assert len(geracoes) == 3
    contexto_produto = json.loads(geracoes[1]["messages"][-1]["content"])
    assert set(contexto_produto[0]) == {"identificador", "fonte", "texto"}
    assert "referencia" not in contexto_produto[0]
    assert len(resposta.referencias) == 2
    nomes_restantes = {
        alternativa["properties"]["nome"]["const"]
        for alternativa in geracoes[1]["format"]["oneOf"]
        if "nome" in alternativa["properties"]
    }
    assert nomes_restantes == {"buscar_politicas"}
    assert "tipo" not in geracoes[-1]["format"]["properties"]
    assert all(
        len(json.dumps(g, ensure_ascii=False).encode()) <= 6000 for g in geracoes
    )
    assert geracoes[-1]["format"]["properties"]["evidencias"]["items"]["enum"] == [
        "E1",
        "E2",
    ]


@pytest.mark.parametrize(
    "conteudo",
    [
        "Texto comercial livre",
        '{"evidencias":[],"resposta":"inventada"}',
        '{"evidencias":[3]}',
    ],
)
def test_selecao_final_nao_aceita_prosa_campos_extras_ou_ids_invalidos(conteudo):
    with pytest.raises(ErroModelo):
        interpretar_evidencias(TurnoModelo(conteudo))


def test_selecao_final_vazia_preserva_abstencao():
    turno = interpretar_evidencias(TurnoModelo('{"evidencias":[]}'))
    assert json.loads(turno.conteudo) == {"tipo": "sem_evidencias", "evidencias": []}


def test_consulta_vazia_finaliza_sem_repetir_ou_inventar(ferramentas_agente):
    conteudos = iter(
        [
            '{"nome":"consultar_produto","argumentos":{"identificador":999999}}',
            '{"evidencias":[]}',
        ]
    )
    geracoes = []

    def responder(requisicao):
        if requisicao.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.40.13"})
        if requisicao.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["tools"]})
        geracoes.append(json.loads(requisicao.content))
        return httpx.Response(
            200,
            json={
                "done": True,
                "done_reason": "stop",
                "message": {"role": "assistant", "content": next(conteudos)},
            },
        )

    cfg = ConfiguracaoAplicacao()
    resposta = asyncio.run(
        ServicoAgente(
            AdaptadorOllama(cfg, httpx.MockTransport(responder)),
            ferramentas_agente,
            cfg,
        ).processar_pergunta("Consulte o produto 999999.")
    )
    assert resposta.estado == "sem_evidencias"
    assert len(geracoes) == 2
    assert "oneOf" not in geracoes[-1]["format"]
    assert geracoes[-1]["format"]["properties"]["evidencias"]["maxItems"] == 0
