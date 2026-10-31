from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from emporio_ia.api.esquemas import RespostaErro
from emporio_ia.api.rotas import rotas
from emporio_ia.configuracao import ConfiguracaoAplicacao, obter_configuracao


def criar_resposta_erro(codigo: int, detalhe: str) -> JSONResponse:
    return JSONResponse(
        status_code=codigo,
        content=RespostaErro(detalhe=detalhe).model_dump(),
    )


async def tratar_erro_http(requisicao: Request, erro: HTTPException) -> JSONResponse:
    detalhe = (
        "Recurso não encontrado." if erro.status_code == 404 else "Falha na requisição."
    )
    resposta = criar_resposta_erro(erro.status_code, detalhe)
    if erro.headers:
        resposta.headers.update(erro.headers)
    return resposta


async def tratar_validacao(
    requisicao: Request, erro: RequestValidationError
) -> JSONResponse:
    return criar_resposta_erro(422, "Requisição inválida.")


async def tratar_erro_inesperado(requisicao: Request, erro: Exception) -> JSONResponse:
    # Não reproduzir exceções, parâmetros ou dados pessoais na resposta.
    return criar_resposta_erro(500, "Erro interno do serviço.")


def criar_aplicacao(configuracao: ConfiguracaoAplicacao | None = None) -> FastAPI:
    configuracao = configuracao or obter_configuracao()
    aplicacao = FastAPI(
        title=configuracao.nome_servico,
        version=configuracao.versao,
        description="Fundação técnica do assistente do Empório da Música.",
    )
    aplicacao.state.configuracao = configuracao
    aplicacao.add_middleware(
        CORSMiddleware,
        allow_origins=configuracao.origens_cors,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )
    aplicacao.add_exception_handler(HTTPException, tratar_erro_http)
    aplicacao.add_exception_handler(RequestValidationError, tratar_validacao)
    aplicacao.add_exception_handler(Exception, tratar_erro_inesperado)
    aplicacao.include_router(rotas)
    return aplicacao


aplicacao = criar_aplicacao()
