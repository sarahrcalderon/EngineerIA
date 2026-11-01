import asyncio
import json
from dataclasses import replace

import pytest

from emporio_ia.aplicacao.atendimento import ServicoAtendimentoVisitante
from emporio_ia.dominio.agente import (
    ChamadaFerramenta,
    DadoFerramenta,
    Evidencia,
    RespostaAgente,
)
from emporio_ia.dominio.publicacao import (
    ErroPublicacao,
    PublicacaoVisitante,
    resumo_evidencia,
)
from emporio_ia.infraestrutura.publicacao import FerramentasVisitante, PublicacaoArquivo


def test_manifesto_ausente_nega_tudo(tmp_path):
    publicacao = PublicacaoArquivo(tmp_path / "ausente.json").carregar()
    assert not publicacao.permite(
        DadoFerramenta("catalogo", "Texto fictício", "produto:201")
    )


def test_publicacao_de_desenvolvimento_nao_migra_para_outro_ambiente(tmp_path):
    caminho = tmp_path / "local.json"
    caminho.write_text(
        json.dumps({"versao": 1, "ambiente": "desenvolvimento", "evidencias": {}}),
        encoding="utf-8",
    )
    assert PublicacaoArquivo(caminho, "desenvolvimento").estado() == "pendente"
    with pytest.raises(ErroPublicacao):
        PublicacaoArquivo(caminho, "teste").carregar()


@pytest.mark.parametrize(
    "conteudo",
    [
        "{}",
        '{"versao":2,"evidencias":{}}',
        '{"versao":1,"evidencias":{"produto:201":"invalido"}}',
        "segredo-invalido",
        "x" * 70000,
    ],
)
def test_manifesto_invalido_falha_fechado(conteudo, tmp_path):
    caminho = tmp_path / "publicacao.json"
    caminho.write_text(conteudo, encoding="utf-8")
    with pytest.raises(ErroPublicacao) as erro:
        PublicacaoArquivo(caminho).carregar()
    assert "segredo" not in str(erro.value)
    assert str(tmp_path) not in str(erro.value)


def test_hash_vincula_texto_e_fonte():
    dado = DadoFerramenta("catalogo", "Preço sintético: R$ 10,10", "produto:201")
    publicacao = PublicacaoVisitante({dado.referencia: resumo_evidencia(dado)})
    assert publicacao.permite(dado)
    assert not publicacao.permite(replace(dado, texto="Preço alterado"))
    assert not publicacao.permite(replace(dado, fonte="politicas"))
    pessoal = DadoFerramenta("catalogo", "Texto pessoal sintético", "cliente:801")
    assert not PublicacaoVisitante(
        {pessoal.referencia: resumo_evidencia(pessoal)}
    ).permite(pessoal)


def test_filtra_antes_do_modelo(contexto_publico):
    _, ferramentas = contexto_publico
    visitante = FerramentasVisitante(ferramentas, PublicacaoVisitante({}))
    with pytest.raises(ErroPublicacao):
        asyncio.run(
            visitante.executar(
                ChamadaFerramenta("consultar_produto", {"identificador": 201})
            )
        )
    assert {f["function"]["name"] for f in visitante.descrever()} == {
        "buscar_produtos",
        "consultar_produto",
        "consultar_categorias",
        "consultar_promocoes",
        "buscar_politicas",
    }


def test_revogacao_antes_da_resposta(contexto_publico):
    _, ferramentas = contexto_publico
    dado = ferramentas._executar(
        ChamadaFerramenta("consultar_produto", {"identificador": 201})
    )[0]
    aprovada = PublicacaoVisitante({dado.referencia: resumo_evidencia(dado)})
    leituras = iter([aprovada, PublicacaoVisitante({})])

    class Agente:
        async def processar_pergunta(self, pergunta):
            return RespostaAgente(
                "fundamentada", "texto interno", evidencias=(Evidencia("E1", dado),)
            )

    servico = ServicoAtendimentoVisitante(
        lambda publicacao: Agente(), lambda: next(leituras)
    )
    with pytest.raises(ErroPublicacao):
        asyncio.run(servico.atender("Preço?"))


def test_nao_confia_em_texto_livre_mesmo_em_erro():
    class Agente:
        async def processar_pergunta(self, pergunta):
            return RespostaAgente("sem_evidencias", "segredo-pessoal-sintetico")

    servico = ServicoAtendimentoVisitante(
        lambda publicacao: Agente(), lambda: PublicacaoVisitante({})
    )
    assert "segredo" not in asyncio.run(servico.atender("Pergunta")).resposta


def test_politica_aprovada_tem_pagina_real(contexto_publico):
    _, ferramentas = contexto_publico
    dado = ferramentas._executar(
        ferramentas.validar(
            ChamadaFerramenta("buscar_politicas", {"pergunta": "troca"})
        )
    )[0]
    publicacao = PublicacaoVisitante({dado.referencia: resumo_evidencia(dado)})

    class Agente:
        async def processar_pergunta(self, pergunta):
            return RespostaAgente(
                "fundamentada",
                "hash-interno-nao-publico",
                evidencias=(Evidencia("E1", dado),),
            )

    servico = ServicoAtendimentoVisitante(lambda politica: Agente(), lambda: publicacao)
    resposta = asyncio.run(servico.atender("Troca?"))
    assert resposta.referencias[0].pagina == 3
    assert "página 3" in resposta.referencias[0].titulo
    assert "hash-interno" not in resposta.resposta
    assert "b" * 64 not in str(resposta.referencias)
