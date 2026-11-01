import asyncio
import json

import pytest

from emporio_ia.aplicacao.agente import ServicoAgente
from emporio_ia.aplicacao.atendimento import ServicoAtendimentoVisitante
from emporio_ia.aplicacao.linguagem import (
    consultas_de_recuperacao,
    permite_recuperacao,
    resposta_social,
)
from emporio_ia.dominio.agente import ChamadaFerramenta, ErroModelo, TurnoModelo
from emporio_ia.dominio.busca_produtos import normalizar_busca_produto
from emporio_ia.dominio.excecoes import ErroDados


@pytest.mark.parametrize(
    "pergunta",
    ["Olá!", "Oi", "Bom dia", "Boa tarde", "Boa noite", "Obrigado", "Até mais"],
)
def test_social_sem_publicacao_banco_ou_modelo(pergunta):
    def proibido(*args):
        raise AssertionError("Atos sociais não devem consultar dependências.")

    servico = ServicoAtendimentoVisitante(proibido, proibido)
    resposta = asyncio.run(servico.atender(pergunta))
    assert resposta.estado == "social"
    assert not resposta.referencias


@pytest.mark.parametrize(
    "pergunta", ["Olá, quanto custa um violão?", "Olá\0", "Oi CPF"]
)
def test_social_nao_absorve_consulta_ou_controle(pergunta):
    assert resposta_social(pergunta) is None


@pytest.mark.parametrize("termo", ["violão", "violões", "VIOLÕES"])
def test_plural_acentos(termo):
    assert normalizar_busca_produto(termo) == "violao"


@pytest.mark.parametrize(
    ("pergunta", "argumentos"),
    [
        ("Quais produtos vocês vendem?", {}),
        ("Vocês têm violões?", {"termo": "violao"}),
        ("Olá, qual o preço de um violão?", {"termo": "violao"}),
        ("Vocês vendem guitarras?", {"termo": "guitarra"}),
    ],
)
def test_consulta_canonica_sem_fatos_embutidos(pergunta, argumentos):
    assert consultas_de_recuperacao(pergunta, {"catalogo"}) == [
        ChamadaFerramenta("buscar_produtos", argumentos)
    ]


def test_busca_categoria_e_listagem(ferramentas_agente):
    categoria = ferramentas_agente._executar(
        ferramentas_agente.validar(
            ChamadaFerramenta("buscar_produtos", {"termo": "corda"})
        )
    )
    geral = ferramentas_agente._executar(
        ferramentas_agente.validar(ChamadaFerramenta("buscar_produtos", {}))
    )
    assert categoria and geral
    assert any(d.referencia == "produto:201" for d in categoria)
    assert len(geral) >= len(categoria)


class ModeloSemSelecao:
    async def responder(self, mensagens, ferramentas):
        ids = [
            e["identificador"]
            for m in mensagens
            if m.papel == "tool"
            for e in json.loads(m.conteudo)
        ]
        return TurnoModelo(
            json.dumps(
                {"tipo": "responder" if ids else "esclarecer", "evidencias": ids}
            )
        )


@pytest.mark.parametrize(
    ("pergunta", "fontes"),
    [
        ("Quais produtos vocês vendem?", {"catalogo"}),
        ("Qual a política de troca?", {"politicas"}),
        (
            "Qual o preço do produto 201 e a política de troca?",
            {"catalogo", "politicas"},
        ),
        ("Quais promoções estão cadastradas?", {"promocoes"}),
    ],
)
def test_recupera_omissao_do_modelo_com_fontes_reais_da_fixture(
    pergunta, fontes, ferramentas_agente, configuracao_agente
):
    agente = ServicoAgente(ModeloSemSelecao(), ferramentas_agente, configuracao_agente)
    resposta = asyncio.run(agente.processar_pergunta(pergunta))
    assert resposta.estado == "fundamentada"
    assert {e.dado.fonte for e in resposta.evidencias} >= fontes


@pytest.mark.parametrize(
    "conteudo", ["texto livre", "[]", '{"tipo":"responder","evidencias":["E99"]}']
)
def test_recuperacao_nao_contorna_formato_ou_ids(conteudo):
    assert not permite_recuperacao(conteudo)


def test_banco_indisponivel_nao_equivale_a_catalogo_vazio(
    ferramentas_agente, configuracao_agente, monkeypatch
):
    async def falhar(chamada):
        raise ErroDados("Falha fictícia")

    monkeypatch.setattr(ferramentas_agente, "executar", falhar)
    agente = ServicoAgente(ModeloSemSelecao(), ferramentas_agente, configuracao_agente)
    resposta = asyncio.run(agente.processar_pergunta("Quais produtos vocês vendem?"))
    assert resposta.estado == "indisponivel"
    assert resposta.categoria_erro == "fonte_indisponivel"
    assert not resposta.evidencias


def test_modelo_indisponivel_nao_aciona_recuperacao(
    ferramentas_agente, configuracao_agente, monkeypatch
):
    class ModeloFora:
        async def responder(self, mensagens, ferramentas):
            raise ErroModelo("indisponivel")

    async def proibido(chamada):
        raise AssertionError("Não deve mascarar infraestrutura com recuperação.")

    monkeypatch.setattr(ferramentas_agente, "executar", proibido)
    agente = ServicoAgente(ModeloFora(), ferramentas_agente, configuracao_agente)
    resposta = asyncio.run(agente.processar_pergunta("Quais produtos vocês vendem?"))
    assert resposta.estado == "indisponivel"
    assert not resposta.evidencias
