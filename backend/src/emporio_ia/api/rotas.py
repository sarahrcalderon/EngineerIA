from typing import Annotated

from fastapi import APIRouter, Depends

from emporio_ia.api.dependencias import obter_configuracao_requisicao
from emporio_ia.api.esquemas import RespostaSaude
from emporio_ia.configuracao import ConfiguracaoAplicacao

rotas = APIRouter(prefix="/api")


@rotas.get("/saude", response_model=RespostaSaude, tags=["Saúde"])
def consultar_saude(
    configuracao: Annotated[
        ConfiguracaoAplicacao, Depends(obter_configuracao_requisicao)
    ],
) -> RespostaSaude:
    return RespostaSaude(
        servico=configuracao.nome_servico,
        versao=configuracao.versao,
    )
