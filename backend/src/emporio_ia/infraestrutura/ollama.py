import asyncio
import json

import httpx

from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import (
    ChamadaFerramenta,
    ErroModelo,
    Mensagem,
    TurnoModelo,
)


class AdaptadorOllama:
    def __init__(
        self,
        configuracao: ConfiguracaoAplicacao,
        transporte: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.configuracao = configuracao
        self.transporte = transporte

    async def _requisitar(
        self,
        cliente: httpx.AsyncClient,
        metodo: str,
        rota: str,
        dados: dict[str, object] | None = None,
    ) -> dict[str, object]:
        try:
            async with cliente.stream(metodo, rota, json=dados) as resposta:
                if resposta.status_code == 404:
                    raise ErroModelo("modelo_inexistente")
                if resposta.status_code != 200:
                    raise ErroModelo("http_invalido")
                conteudo = bytearray()
                async for parte in resposta.aiter_bytes():
                    conteudo.extend(parte)
                    if len(conteudo) > self.configuracao.agente_resposta_bytes:
                        raise ErroModelo("resposta_excessiva")
                retorno = json.loads(conteudo)
                if not isinstance(retorno, dict) or "error" in retorno:
                    raise ErroModelo("resposta_invalida")
                return retorno
        except asyncio.CancelledError:
            raise
        except httpx.TimeoutException:
            raise ErroModelo("timeout") from None
        except httpx.HTTPError:
            raise ErroModelo("conexao") from None
        except (ValueError, UnicodeError):
            raise ErroModelo("resposta_invalida") from None

    async def responder(
        self, mensagens: tuple[Mensagem, ...], ferramentas: list[dict[str, object]]
    ) -> TurnoModelo:
        async with httpx.AsyncClient(
            base_url=self.configuracao.ollama_url,
            timeout=self.configuracao.ollama_timeout,
            trust_env=False,
            follow_redirects=False,
            transport=self.transporte,
        ) as cliente:
            versao = await self._requisitar(cliente, "GET", "/api/version")
            if not isinstance(versao.get("version"), str):
                raise ErroModelo("versao_invalida")
            detalhes = await self._requisitar(
                cliente, "POST", "/api/show", {"model": self.configuracao.ollama_modelo}
            )
            if detalhes.get("remote_host") or detalhes.get("remote_model"):
                raise ErroModelo("modelo_remoto_bloqueado")
            capacidades = detalhes.get("capabilities")
            if not isinstance(capacidades, list) or "tools" not in capacidades:
                raise ErroModelo("ferramentas_nao_suportadas")
            historico = []
            for mensagem in mensagens:
                item: dict[str, object] = {
                    "role": mensagem.papel,
                    "content": mensagem.conteudo,
                }
                if mensagem.chamadas:
                    item["tool_calls"] = [
                        {
                            "function": {
                                "name": chamada.nome,
                                "arguments": chamada.argumentos,
                            }
                        }
                        for chamada in mensagem.chamadas
                    ]
                if mensagem.ferramenta is not None:
                    item["tool_name"] = mensagem.ferramenta
                historico.append(item)
            dados: dict[str, object] = {
                "model": self.configuracao.ollama_modelo,
                "stream": False,
                "messages": historico,
                "tools": ferramentas,
                "options": {
                    "temperature": self.configuracao.ollama_temperatura,
                    "num_predict": self.configuracao.ollama_tokens,
                    "num_ctx": self.configuracao.ollama_contexto_tokens,
                },
            }
            if "thinking" in capacidades:
                dados["think"] = False
            if (
                len(json.dumps(dados, ensure_ascii=False).encode())
                > self.configuracao.agente_contexto_bytes
            ):
                raise ErroModelo("contexto_excessivo")
            retorno = await self._requisitar(cliente, "POST", "/api/chat", dados)
        return self._interpretar(retorno)

    def _interpretar(self, retorno: dict[str, object]) -> TurnoModelo:
        mensagem = retorno.get("message")
        if (
            retorno.get("done") is not True
            or retorno.get("done_reason") not in {None, "stop"}
            or not isinstance(mensagem, dict)
            or mensagem.get("role") != "assistant"
        ):
            raise ErroModelo("resposta_invalida")
        conteudo = mensagem.get("content", "")
        chamadas = mensagem.get("tool_calls", [])
        if (
            not isinstance(conteudo, str)
            or not isinstance(chamadas, list)
            or len(chamadas) > self.configuracao.agente_maximo_chamadas
        ):
            raise ErroModelo("resposta_invalida")
        interpretadas = []
        for chamada in chamadas:
            funcao = chamada.get("function") if isinstance(chamada, dict) else None
            if (
                not isinstance(funcao, dict)
                or not isinstance(funcao.get("name"), str)
                or not isinstance(funcao.get("arguments"), dict)
            ):
                raise ErroModelo("resposta_invalida")
            interpretadas.append(ChamadaFerramenta(funcao["name"], funcao["arguments"]))
        return TurnoModelo(conteudo, tuple(interpretadas))
