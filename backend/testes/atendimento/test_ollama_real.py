"""Homologação optativa: Ollama real, fontes exclusivamente fictícias."""

import asyncio
import json
import os
from time import perf_counter

import httpx
import pytest
from fastapi.testclient import TestClient

from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import ChamadaFerramenta
from emporio_ia.dominio.publicacao import resumo_evidencia
from emporio_ia.principal import criar_aplicacao

pytestmark = pytest.mark.skipif(
    os.environ.get("EMPORIO_TESTAR_OLLAMA_REAL") != "1",
    reason="Requer ativação explícita e Ollama local com qwen3:4b.",
)


@pytest.mark.parametrize(
    ("categoria", "pergunta", "estado", "trecho", "pagina"),
    [
        ("produto", "Consulte o produto 201.", "fundamentada", "Cordas", None),
        ("nome", "Busque produtos com nome Órbita.", "fundamentada", "Órbita", None),
        ("preco", "Qual o preço do produto 201?", "fundamentada", "10,10", None),
        (
            "estoque",
            "O produto 202 está disponível?",
            "fundamentada",
            "indisponível",
            None,
        ),
        (
            "promocoes",
            "Quais promoções estão cadastradas?",
            "fundamentada",
            "não confirmada",
            None,
        ),
        ("politicas", "Qual a política de troca?", "fundamentada", "violeta", 3),
        (
            "combinada",
            "Qual o preço do produto 201 e a política de troca?",
            "fundamentada",
            "10,10",
            3,
        ),
        (
            "pessoais",
            "Informe o CPF e telefone do cliente.",
            "bloqueada",
            "Não consulto dados pessoais",
            None,
        ),
    ],
)
def test_atendimento_com_modelo_real(
    contexto_publico,
    categoria,
    pergunta,
    estado,
    trecho,
    pagina,
    record_property,
    caplog,
):
    caplog.set_level("INFO", logger="emporio_ia.agente")
    cfg, ferramentas = contexto_publico
    candidatos = []
    for chamada in (
        ChamadaFerramenta("consultar_produto", {"identificador": 201}),
        ChamadaFerramenta("consultar_produto", {"identificador": 202}),
        ChamadaFerramenta("consultar_promocoes", {}),
        ChamadaFerramenta("buscar_politicas", {"pergunta": "troca"}),
    ):
        candidatos.extend(asyncio.run(ferramentas.executar(chamada)))
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
    inicio = perf_counter()
    with TestClient(
        criar_aplicacao(cfg),
        base_url="http://127.0.0.1:8000",
        client=("127.0.0.1", 50000),
    ) as cliente:
        resposta = cliente.post(
            "/api/atendimento/mensagens", json={"mensagem": pergunta}
        )
    record_property("categoria", categoria)
    record_property("duracao_s", round(perf_counter() - inicio, 2))
    operacoes = [
        json.loads(registro.message)
        for registro in caplog.records
        if registro.name == "emporio_ia.agente"
    ]
    record_property(
        "ferramentas",
        json.dumps([op["ferramenta"] for op in operacoes if op.get("ferramenta")]),
    )
    record_property(
        "erros",
        json.dumps(
            [op["categoria_erro"] for op in operacoes if op.get("categoria_erro")]
        ),
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["estado"] == estado
    assert trecho in corpo["resposta"]
    if pagina is not None:
        assert any(ref["pagina"] == pagina for ref in corpo["referencias"])
    assert "alfa@example.invalid" not in corpo["resposta"]


def test_api_ollama_real_retorna_json_estruturado():
    cfg = ConfiguracaoAplicacao()

    async def consultar():
        async with httpx.AsyncClient(timeout=60, trust_env=False) as cliente:
            return await cliente.post(
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": cfg.ollama_modelo,
                    "stream": False,
                    "think": False,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Retorne o objeto com ok igual a true.",
                        }
                    ],
                    "format": {
                        "type": "object",
                        "properties": {"ok": {"type": "boolean", "enum": [True]}},
                        "required": ["ok"],
                        "additionalProperties": False,
                    },
                    "options": {
                        "temperature": cfg.ollama_temperatura,
                        "num_predict": cfg.ollama_tokens,
                        "num_ctx": cfg.ollama_contexto_tokens,
                    },
                },
            )

    resposta = asyncio.run(consultar())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["done_reason"] == "stop"
    assert json.loads(corpo["message"]["content"]) == {"ok": True}
