from fastapi import Request

from emporio_ia.configuracao import ConfiguracaoAplicacao


def obter_configuracao_requisicao(requisicao: Request) -> ConfiguracaoAplicacao:
    return requisicao.app.state.configuracao
