import asyncio
from dataclasses import asdict
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from emporio_ia.aplicacao.atendimento import ServicoAtendimentoVisitante
from emporio_ia.dominio.excecoes import ErroDados

rotas_atendimento = APIRouter(prefix="/api/atendimento", tags=["Atendimento local"])


class EntradaMensagem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)
    mensagem: str = Field(min_length=1, max_length=1000)

    @field_validator("mensagem")
    @classmethod
    def validar_mensagem(cls, valor: str) -> str:
        if not valor.strip() or any(
            ord(letra) < 32 and letra not in "\n\t" for letra in valor
        ):
            raise ValueError("Mensagem inválida.")
        return valor.strip()


class ReferenciaResposta(BaseModel):
    tipo: Literal["politica", "catalogo", "categorias", "promocoes"]
    titulo: str
    pagina: int | None = Field(default=None, ge=1, le=500)


class SaidaMensagem(BaseModel):
    estado: Literal[
        "fundamentada",
        "sem_evidencias",
        "esclarecer",
        "fora_escopo",
        "bloqueada",
        "limite",
        "entrada_invalida",
    ]
    resposta: str = Field(max_length=16000)
    referencias: list[ReferenciaResposta] = Field(max_length=20)
    requisicao_id: str


def obter_atendimento(requisicao: Request) -> ServicoAtendimentoVisitante:
    return requisicao.app.state.atendimento_visitante


def erro_atendimento(codigo: str, detalhe: str, status: int) -> JSONResponse:
    return JSONResponse({"codigo": codigo, "detalhe": detalhe}, status_code=status)


async def aguardar_desconexao(requisicao: Request) -> None:
    # O corpo já foi consumido pelo FastAPI. Só este observador lê a desconexão.
    # Evitar CancelScopes de polling que podem absorver cancelamentos externos.
    while True:
        mensagem = await requisicao.receive()
        if mensagem["type"] == "http.disconnect":
            return


@rotas_atendimento.post("/mensagens", response_model=SaidaMensagem)
async def enviar_mensagem(
    entrada: EntradaMensagem,
    requisicao: Request,
    atendimento: Annotated[ServicoAtendimentoVisitante, Depends(obter_atendimento)],
) -> SaidaMensagem | JSONResponse:
    configuracao = requisicao.app.state.configuracao
    if len(entrada.mensagem) > configuracao.agente_maximo_pergunta:
        return erro_atendimento(
            "mensagem_invalida", "Mensagem acima do limite permitido.", 422
        )
    limites = requisicao.app.state.limites_atendimento
    if not limites.ocupar():
        resposta = erro_atendimento(
            "ocupado", "Outra consulta está em andamento. Aguarde.", 429
        )
        resposta.headers["Retry-After"] = "2"
        return resposta
    tarefa = asyncio.create_task(atendimento.atender(entrada.mensagem))
    desconexao = asyncio.create_task(aguardar_desconexao(requisicao))
    try:
        async with asyncio.timeout(configuracao.agente_timeout_total):
            concluidas, _ = await asyncio.wait(
                {tarefa, desconexao}, return_when=asyncio.FIRST_COMPLETED
            )
            if desconexao in concluidas:
                return erro_atendimento("cancelada", "Consulta cancelada.", 499)
            resultado = await tarefa
        if resultado.categoria_erro == "timeout":
            return erro_atendimento(
                "timeout", "A consulta excedeu o tempo permitido.", 504
            )
        if resultado.estado == "indisponivel":
            if resultado.categoria_erro in {
                "resposta_invalida",
                "geracao_interrompida",
                "contexto_excessivo",
                "resposta_excessiva",
            }:
                return erro_atendimento(
                    "geracao_interrompida"
                    if resultado.categoria_erro == "geracao_interrompida"
                    else "resposta_modelo_invalida",
                    "O modelo não concluiu uma resposta válida. Tente novamente.",
                    502,
                )
            return erro_atendimento(
                "modelo_indisponivel", "O modelo local está indisponível.", 503
            )
        return SaidaMensagem(
            estado=resultado.estado,
            resposta=resultado.resposta,
            referencias=[
                ReferenciaResposta(**asdict(ref)) for ref in resultado.referencias
            ],
            requisicao_id=str(uuid4()),
        )
    except TimeoutError:
        return erro_atendimento("timeout", "A consulta excedeu o tempo permitido.", 504)
    except ErroDados:
        return erro_atendimento(
            "publicacao_indisponivel",
            "As informações autorizadas não estão disponíveis.",
            503,
        )
    except Exception:
        return erro_atendimento(
            "servico_indisponivel", "Não foi possível concluir a consulta.", 503
        )
    finally:
        for pendente in (tarefa, desconexao):
            if not pendente.done():
                pendente.cancel()
        await asyncio.gather(tarefa, desconexao, return_exceptions=True)
        limites.liberar()


@rotas_atendimento.get("/disponibilidade")
async def consultar_disponibilidade(requisicao: Request) -> dict[str, object]:
    cfg = requisicao.app.state.configuracao
    try:
        async with asyncio.timeout(cfg.atendimento_disponibilidade_timeout):
            acessivel = await requisicao.app.state.verificar_modelo_visitante()
    except (TimeoutError, ErroDados):
        acessivel = False
    return {
        "api": "disponivel",
        "modelo": "acessivel" if acessivel else "indisponivel",
        "homologacao": "pendente",
        "limite_mensagem": min(1000, cfg.agente_maximo_pergunta),
    }
