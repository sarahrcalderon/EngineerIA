from typing import Literal

from pydantic import BaseModel


class RespostaSaude(BaseModel):
    estado: Literal["disponivel"] = "disponivel"
    servico: str
    versao: str


class RespostaErro(BaseModel):
    detalhe: str
