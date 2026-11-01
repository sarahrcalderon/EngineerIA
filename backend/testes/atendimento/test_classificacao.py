import asyncio
import json
import os

import pytest
from fastapi.testclient import TestClient

from emporio_ia.aplicacao.agente import ServicoAgente
from emporio_ia.aplicacao.atendimento import ServicoAtendimentoVisitante
from emporio_ia.aplicacao.consulta_catalogo import interpretar_consulta_catalogo
from emporio_ia.dominio.agente import ChamadaFerramenta, ErroFerramenta
from emporio_ia.dominio.publicacao import PublicacaoVisitante, resumo_evidencia
from emporio_ia.infraestrutura.publicacao import FerramentasVisitante
from emporio_ia.principal import criar_aplicacao

from .conftest import ModeloConsulta


@pytest.fixture
def classificacao(contexto_publico):
    cfg, ferramentas = contexto_publico
    banco = ferramentas.catalogo.produtos.banco
    with banco.conectar(escrita=True) as con:
        con.execute("UPDATE categorias SET nome='Violões' WHERE identificador=901")
        con.execute("UPDATE categorias SET nome='Guitarras' WHERE identificador=902")
        for id_, nome, preco, cat, estoque in [
            (201, "Violão Alfa fictício", 30000, 901, 3),
            (202, "Guitarra Beta fictícia", 90000, 902, 0),
            (203, "Violão Gama fictício", 30000, 901, 2),
            (204, "Guitarra Delta fictícia", 10000, 902, 1),
        ]:
            con.execute(
                "UPDATE produtos SET nome=?, nome_busca=lower(?), "
                "preco_centavos=?, categoria_id=?, quantidade_estoque=?, "
                "estado='active' WHERE identificador=?",
                (nome, nome, preco, cat, estoque, id_),
            )
        for id_, preco, cat in [
            (205, 20000, 901),
            (206, 1890000, 902),
            (207, 500, 902),
        ]:
            con.execute(
                "INSERT INTO produtos (identificador,preco_centavos,nome,"
                "categoria_id,descricao,quantidade_estoque,estado,especificacoes,"
                "criado_em,nome_busca) SELECT ?, ?, ?, categoria_id, descricao, "
                "quantidade_estoque, estado, especificacoes, criado_em, ? "
                "FROM produtos WHERE identificador=201",
                (id_, preco, f"Item fictício {id_}", f"item ficticio {id_}"),
            )
            con.execute(
                "UPDATE produtos SET categoria_id=? WHERE identificador=?", (cat, id_)
            )
    dados = ferramentas._executar(
        ferramentas.validar(ChamadaFerramenta("buscar_produtos", {"limite": 20}))
    )
    publicacao = PublicacaoVisitante(
        {
            d.referencia: resumo_evidencia(d)
            for d in dados
            if d.referencia != "produto:207"
        }
    )
    cfg.caminho_publicacao.write_text(
        json.dumps({"versao": 1, "evidencias": dict(publicacao.autorizadas)}),
        encoding="utf8",
    )
    return cfg, ferramentas, publicacao


@pytest.mark.parametrize(
    ("argumentos", "ids"),
    [
        ({"ordenacao": "preco_crescente", "limite": 3}, [204, 205, 201]),
        ({"ordenacao": "preco_decrescente", "limite": 5}, [206, 202, 201, 203, 205]),
        ({"categoria": "Violões", "limite": 20}, [201, 203, 205]),
        ({"categoria": "Violões", "preco_maximo_centavos": 20000}, [205]),
        ({"categoria": "Violões", "ordenacao": "preco_crescente"}, [205, 201, 203]),
        ({"disponiveis": True, "limite": 20}, [201, 203, 204, 205, 206]),
        ({"limite": 20}, [201, 202, 203, 204, 205, 206]),
        ({"preco_maximo_centavos": 50}, []),
        (
            {
                "preco_minimo_centavos": 20000,
                "preco_maximo_centavos": 80000,
                "limite": 20,
            },
            [201, 203, 205],
        ),
    ],
)
def test_filtros_sql_e_publicacao_antes_do_limite(classificacao, argumentos, ids):
    _, f, p = classificacao
    dados = asyncio.run(
        FerramentasVisitante(f, p).executar(
            ChamadaFerramenta("buscar_produtos", argumentos)
        )
    )
    assert [int(d.referencia.split(":")[1]) for d in dados] == ids
    assert all(p.permite(d) for d in dados)


def test_hash_desatualizado_nao_consume_vaga(classificacao):
    _, f, p = classificacao
    hashes = dict(p.autorizadas)
    hashes["produto:204"] = "0" * 64
    dados = asyncio.run(
        FerramentasVisitante(f, PublicacaoVisitante(hashes)).executar(
            ChamadaFerramenta(
                "buscar_produtos", {"ordenacao": "preco_crescente", "limite": 3}
            )
        )
    )
    assert [d.referencia for d in dados] == [
        "produto:205",
        "produto:201",
        "produto:203",
    ]


def test_preco_invalido_nao_participa_da_classificacao(classificacao):
    _, f, p = classificacao
    with f.catalogo.produtos.banco.conectar(escrita=True) as con:
        con.execute("PRAGMA ignore_check_constraints=ON")
        con.execute("UPDATE produtos SET preco_centavos=-1 WHERE identificador=204")
    dados = asyncio.run(
        FerramentasVisitante(f, p).executar(
            ChamadaFerramenta(
                "buscar_produtos", {"ordenacao": "preco_crescente", "limite": 3}
            )
        )
    )
    assert all(d.apresentacao.preco_centavos >= 0 for d in dados)
    assert dados[0].referencia == "produto:205"


@pytest.mark.parametrize(
    ("pergunta", "criterios"),
    [
        (
            "Quais são os 3 produtos mais baratos da loja?",
            {"limite": 3, "ordenacao": "preco_crescente"},
        ),
        (
            "Mostre os 5 produtos mais caros.",
            {"limite": 5, "ordenacao": "preco_decrescente"},
        ),
        (
            "Quais violões custam menos de R$ 1.000?",
            {"termo": "violao", "preco_maximo_centavos": 99999},
        ),
        (
            "Liste 4 guitarras disponíveis.",
            {"termo": "guitarra", "limite": 4, "disponiveis": True},
        ),
        (
            "Quais produtos estão entre R$ 200 e R$ 800?",
            {"preco_minimo_centavos": 20000, "preco_maximo_centavos": 80000},
        ),
        (
            "Mostre os 3 violões mais baratos.",
            {"termo": "violao", "limite": 3, "ordenacao": "preco_crescente"},
        ),
        ("Vocês têm instrumentos até R$ 500?", {"preco_maximo_centavos": 50000}),
        ("Tem alguma coisa mais em conta?", {"ordenacao": "preco_crescente"}),
        ("Mostre cinco opções.", {"limite": 5}),
        (
            "Qual é o violão mais barato?",
            {"termo": "violao", "limite": 1, "ordenacao": "preco_crescente"},
        ),
    ],
)
def test_interpreta_criterios_sem_buscar_frase_literal(pergunta, criterios):
    assert interpretar_consulta_catalogo(pergunta) == criterios


@pytest.mark.parametrize(
    "pergunta",
    [
        "Qual o prazo de entrega até 5 dias?",
        "Quais políticas estão disponíveis?",
        "Quais produtos mais baratos e mais caros?",
    ],
)
def test_nao_converte_prazo_ou_ambiguidade_em_preco(pergunta):
    assert interpretar_consulta_catalogo(pergunta) is None


@pytest.mark.parametrize(
    "argumentos",
    [
        {"ordenacao": "preco ASC; DROP TABLE produtos"},
        {"preco_minimo_centavos": 200, "preco_maximo_centavos": 100},
        {"preco_maximo_centavos": 1.5},
        {"preco_maximo_centavos": "100,00"},
        {"disponiveis": "true"},
        {"limite": 21},
    ],
)
def test_rejeita_filtros_invalidos_sem_sql_do_modelo(contexto_publico, argumentos):
    _, ferramentas = contexto_publico
    with pytest.raises(ErroFerramenta):
        ferramentas.validar(ChamadaFerramenta("buscar_produtos", argumentos))


def test_fastapi_preserva_todos_itens_ordem_e_introducao(classificacao):
    cfg, f, p = classificacao
    app = criar_aplicacao(cfg)

    def criar(publicacao):
        # Reproduz o erro original: o modelo escolhe uma busca literal.
        return ServicoAgente(
            ModeloConsulta(
                (
                    ChamadaFerramenta(
                        "buscar_produtos", {"termo": "3 produtos mais baratos"}
                    ),
                )
            ),
            FerramentasVisitante(f, publicacao),
            cfg,
        )

    app.state.atendimento_visitante = ServicoAtendimentoVisitante(criar, lambda: p)
    with TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as c:
        for pergunta, precos in [
            ("Quais são os 3 produtos mais baratos da loja?", [10000, 20000, 30000]),
            ("Mostre os 5 produtos mais caros.", [1890000, 90000, 30000, 30000, 20000]),
        ]:
            r = c.post("/api/atendimento/mensagens", json={"mensagem": pergunta})
            assert r.status_code == 200
            corpo = r.json()
            assert [p["preco_centavos"] for p in corpo["produtos"]] == precos
            assert corpo["introducao"].startswith("Encontrei estas opções")
            assert "Produto cadastrado" not in corpo["resposta"]
            assert (
                "R$ 18.900,00" in corpo["resposta"]
                if len(precos) == 5
                else "R$ 100,00" in corpo["resposta"]
            )


@pytest.mark.skipif(
    os.environ.get("EMPORIO_TESTAR_OLLAMA_REAL") != "1",
    reason="Requer Ollama local real.",
)
def test_classificacao_com_ollama_real(classificacao):
    cfg, _, _ = classificacao
    with TestClient(
        criar_aplicacao(cfg), base_url="http://127.0.0.1", client=("127.0.0.1", 50000)
    ) as c:
        r = c.post(
            "/api/atendimento/mensagens",
            json={"mensagem": "Quais são os 3 produtos mais baratos da loja?"},
        )
        assert r.status_code == 200
        assert [p["preco_centavos"] for p in r.json()["produtos"]] == [
            10000,
            20000,
            30000,
        ]
