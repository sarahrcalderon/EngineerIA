import asyncio
from dataclasses import replace

import pytest

from emporio_ia.aplicacao.agente import ServicoAgente
from emporio_ia.aplicacao.atendimento import ServicoAtendimentoVisitante
from emporio_ia.dominio.agente import ChamadaFerramenta, Evidencia, RespostaAgente
from emporio_ia.dominio.apresentacao import preco_brl
from emporio_ia.dominio.publicacao import (
    ErroPublicacao,
    PublicacaoVisitante,
    resumo_evidencia,
)
from emporio_ia.infraestrutura.composicao_agente import criar_ferramentas
from emporio_ia.infraestrutura.publicacao import FerramentasVisitante

from .conftest import ModeloConsulta


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (59990, "R$ 599,90"),
        (1890000, "R$ 18.900,00"),
        (100000000, "R$ 1.000.000,00"),
        (0, "R$ 0,00"),
    ],
)
def test_brl_sem_arredondar_centavos(valor, esperado):
    assert preco_brl(valor) == esperado


@pytest.mark.parametrize("identificador", [201, 202])
def test_produto_estruturado_natural_e_sem_campos_privados(api_publica, identificador):
    cliente, app, cfg, _ = api_publica
    ferramentas = criar_ferramentas(cfg)
    dado = ferramentas._executar(
        ChamadaFerramenta("consultar_produto", {"identificador": identificador})
    )[0]
    publicacao = PublicacaoVisitante({dado.referencia: resumo_evidencia(dado)})
    app.state.atendimento_visitante = ServicoAtendimentoVisitante(
        lambda p: ServicoAgente(
            ModeloConsulta(
                (
                    ChamadaFerramenta(
                        "consultar_produto", {"identificador": identificador}
                    ),
                )
            ),
            FerramentasVisitante(ferramentas, p),
            cfg,
        ),
        lambda: publicacao,
    )
    corpo = cliente.post(
        "/api/atendimento/mensagens", json={"mensagem": f"Produto {identificador}"}
    ).json()
    assert corpo["estado"] == "fundamentada"
    assert corpo["produtos"][0] == {
        "nome": dado.apresentacao.nome,
        "preco_centavos": dado.apresentacao.preco_centavos,
        "disponivel": identificador == 201,
        "categoria": dado.apresentacao.categoria,
    }
    assert "cadastrado" not in corpo["resposta"]
    assert "descricao" not in corpo["produtos"][0]
    assert "produto:" not in str(corpo)


def test_metadados_adulterados_nao_herdam_autorizacao(contexto_publico):
    _, ferramentas = contexto_publico
    dado = ferramentas._executar(
        ChamadaFerramenta("consultar_produto", {"identificador": 201})
    )[0]
    publicacao = PublicacaoVisitante({dado.referencia: resumo_evidencia(dado)})
    adulterado = replace(
        dado, apresentacao=replace(dado.apresentacao, preco_centavos=1)
    )

    class Agente:
        async def processar_pergunta(self, pergunta):
            return RespostaAgente(
                "fundamentada", "", evidencias=(Evidencia("E1", adulterado),)
            )

    servico = ServicoAtendimentoVisitante(lambda p: Agente(), lambda: publicacao)
    with pytest.raises(ErroPublicacao):
        asyncio.run(servico.atender("Preço do produto"))


def test_projecoes_preservam_exatamente_texto_aprovado(contexto_publico):
    _, ferramentas = contexto_publico
    for chamada in [
        ChamadaFerramenta("buscar_produtos", {}),
        ChamadaFerramenta("consultar_categorias", {}),
        ChamadaFerramenta("consultar_promocoes", {}),
    ]:
        dados = ferramentas._executar(ferramentas.validar(chamada))
        assert dados
        for dado in dados:
            assert dado.apresentacao.texto_original() == dado.texto


@pytest.mark.parametrize(
    "ferramenta", ["buscar_produtos", "consultar_categorias", "consultar_promocoes"]
)
def test_apresenta_todas_evidencias_selecionadas_sem_termos_tecnicos(
    contexto_publico, ferramenta
):
    _, ferramentas = contexto_publico
    dados = ferramentas._executar(
        ferramentas.validar(ChamadaFerramenta(ferramenta, {}))
    )
    publicacao = PublicacaoVisitante({d.referencia: resumo_evidencia(d) for d in dados})

    class Agente:
        async def processar_pergunta(self, pergunta):
            return RespostaAgente(
                "fundamentada",
                "",
                evidencias=tuple(Evidencia(f"E{i}", d) for i, d in enumerate(dados)),
            )

    resposta = asyncio.run(
        ServicoAtendimentoVisitante(lambda p: Agente(), lambda: publicacao).atender(
            "Consulta comercial"
        )
    )
    assert "cadastrad" not in resposta.resposta.lower()
    if ferramenta == "buscar_produtos":
        assert len(resposta.produtos) == len(dados) > 1
        assert all(p.nome in resposta.resposta for p in resposta.produtos)
    elif ferramenta == "consultar_promocoes":
        assert "Vigência temporal não confirmada" in resposta.resposta
        assert not resposta.produtos
    else:
        assert all(d.apresentacao.nome in resposta.resposta for d in dados)
