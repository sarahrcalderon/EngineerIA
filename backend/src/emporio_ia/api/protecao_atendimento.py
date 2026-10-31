import asyncio
import re
import threading
from collections import defaultdict, deque
from time import monotonic

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from emporio_ia.configuracao import ConfiguracaoAplicacao


class LimitesAtendimento:
    def __init__(self, configuracao: ConfiguracaoAplicacao) -> None:
        self.configuracao = configuracao
        self.recentes: dict[str, deque[float]] = defaultdict(deque)
        self.ativas = 0
        self.trava = threading.Lock()

    def permitir_requisicao(self, cliente: str) -> bool:
        agora = monotonic()
        with self.trava:
            janela = self.recentes[cliente]
            while janela and janela[0] <= agora - 60:
                janela.popleft()
            if len(janela) >= self.configuracao.atendimento_requisicoes_minuto:
                return False
            janela.append(agora)
            return True

    def ocupar(self) -> bool:
        with self.trava:
            if self.ativas >= self.configuracao.atendimento_concorrencia:
                return False
            self.ativas += 1
            return True

    def liberar(self) -> None:
        with self.trava:
            self.ativas -= 1


class ProtecaoAtendimento:
    def __init__(
        self,
        app: ASGIApp,
        configuracao: ConfiguracaoAplicacao,
        limites: LimitesAtendimento,
    ) -> None:
        self.app = app
        self.configuracao = configuracao
        self.limites = limites

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/atendimento/"):
            await self.app(scope, receive, send)
            return
        cabecalhos = Headers(scope=scope)
        cliente = (scope.get("client") or ("", 0))[0]
        origem = cabecalhos.get("origin")
        if (
            cliente not in {"127.0.0.1", "::1"}
            or not re.fullmatch(
                r"(?:localhost|127\.0\.0\.1|\[::1\])(?::[0-9]{1,5})?",
                cabecalhos.get("host", ""),
            )
            or (origem is not None and origem not in self.configuracao.origens_cors)
        ):
            await JSONResponse(
                {
                    "codigo": "origem_recusada",
                    "detalhe": "Acesso restrito ao atendimento local.",
                },
                status_code=403,
            )(scope, receive, send)
            return
        if not self.limites.permitir_requisicao(cliente):
            await JSONResponse(
                {
                    "codigo": "limite_requisicoes",
                    "detalhe": "Aguarde antes de tentar novamente.",
                },
                status_code=429,
                headers={"Retry-After": "60"},
            )(scope, receive, send)
            return
        if scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        if (
            cabecalhos.get("content-type", "").split(";")[0].strip()
            != "application/json"
        ):
            await JSONResponse(
                {"codigo": "formato_invalido", "detalhe": "Envie JSON."},
                status_code=415,
            )(scope, receive, send)
            return
        corpo = bytearray()
        try:
            async with asyncio.timeout(self.configuracao.atendimento_leitura_timeout):
                while True:
                    mensagem = await receive()
                    if mensagem["type"] == "http.disconnect":
                        return
                    parte = mensagem.get("body", b"")
                    if (
                        len(corpo) + len(parte)
                        > self.configuracao.atendimento_corpo_bytes
                    ):
                        await JSONResponse(
                            {
                                "codigo": "corpo_excessivo",
                                "detalhe": "Mensagem acima do limite permitido.",
                            },
                            status_code=413,
                        )(scope, receive, send)
                        return
                    corpo.extend(parte)
                    if not mensagem.get("more_body", False):
                        break
        except TimeoutError:
            await JSONResponse(
                {"codigo": "timeout_envio", "detalhe": "Tempo de envio excedido."},
                status_code=408,
            )(scope, receive, send)
            return
        entregue = False

        async def receber_limitado():
            nonlocal entregue
            if not entregue:
                entregue = True
                return {
                    "type": "http.request",
                    "body": bytes(corpo),
                    "more_body": False,
                }
            return await receive()

        await self.app(scope, receber_limitado, send)
