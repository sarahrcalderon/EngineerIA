import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from emporio_ia.aplicacao.contratos_agente import ContratoFerramentas
from emporio_ia.dominio.agente import ChamadaFerramenta, DadoFerramenta
from emporio_ia.dominio.publicacao import ErroPublicacao, PublicacaoVisitante


class ManifestoPublicacao(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)
    versao: Literal[1]
    ambiente: Literal["desenvolvimento", "teste"] | None = None
    evidencias: dict[str, str] = Field(max_length=500)

    @field_validator("evidencias")
    @classmethod
    def validar_hashes(cls, evidencias: dict[str, str]) -> dict[str, str]:
        if any(
            len(chave) > 300 or not re.fullmatch(r"[a-f0-9]{64}", valor)
            for chave, valor in evidencias.items()
        ):
            raise ValueError("A publicação exige referências e hashes válidos.")
        return evidencias


class PublicacaoArquivo:
    def __init__(self, caminho: Path, ambiente: str = "desenvolvimento") -> None:
        self.caminho = caminho
        self.ambiente = ambiente

    def carregar(self) -> PublicacaoVisitante:
        try:
            with self.caminho.open("rb") as arquivo:
                conteudo = arquivo.read(65537)
            if len(conteudo) > 65536:
                raise ErroPublicacao("Manifesto de publicação inválido.")
            manifesto = ManifestoPublicacao.model_validate(json.loads(conteudo))
            if manifesto.ambiente is not None and manifesto.ambiente != self.ambiente:
                raise ErroPublicacao("A publicação não está liberada neste ambiente.")
            return PublicacaoVisitante(manifesto.evidencias)
        except FileNotFoundError:
            return PublicacaoVisitante({})
        except (OSError, ValueError, ValidationError):
            raise ErroPublicacao(
                "Não foi possível validar a publicação local."
            ) from None

    def estado(self) -> str:
        try:
            return "configurada" if self.carregar().autorizadas else "pendente"
        except ErroPublicacao:
            return "indisponivel"


class FerramentasVisitante:
    """Filtrar antes do resultado entrar no contexto do modelo."""

    def __init__(
        self, ferramentas: ContratoFerramentas, publicacao: PublicacaoVisitante
    ) -> None:
        self.ferramentas = ferramentas
        self.publicacao = publicacao

    def descrever(self) -> list[dict[str, object]]:
        return self.ferramentas.descrever()

    def validar(self, chamada: ChamadaFerramenta) -> ChamadaFerramenta:
        return self.ferramentas.validar(chamada)

    async def executar(self, chamada: ChamadaFerramenta) -> tuple[DadoFerramenta, ...]:
        dados = await self.ferramentas.executar(chamada)
        autorizados = tuple(dado for dado in dados if self.publicacao.permite(dado))
        if dados and not autorizados:
            raise ErroPublicacao(
                "As fontes da consulta não foram liberadas para atendimento."
            )
        return autorizados
