import asyncio
import json
import logging
from dataclasses import asdict, replace
from time import perf_counter

from emporio_ia.aplicacao.contratos_agente import ContratoFerramentas, ContratoModelo
from emporio_ia.aplicacao.fundamentacao import (
    FONTES_FERRAMENTAS,
    INSTRUCOES_AGENTE,
    finalizar_resposta,
    fontes_necessarias,
    pergunta_pessoal,
)
from emporio_ia.aplicacao.linguagem import (
    consultas_de_recuperacao,
    permite_recuperacao,
    resposta_social,
)
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.dominio.agente import (
    ErroFerramenta,
    ErroModelo,
    Evidencia,
    Mensagem,
    RespostaAgente,
    TurnoModelo,
)
from emporio_ia.dominio.excecoes import ErroDados
from emporio_ia.dominio.publicacao import ErroPublicacao

registrador = logging.getLogger("emporio_ia.agente")


def registrar_operacao(
    operacao: str,
    inicio: float,
    estado: str,
    *,
    ferramenta: str | None = None,
    quantidade: int = 0,
    categoria: str | None = None,
) -> None:
    registrador.info(
        json.dumps(
            {
                "operacao": operacao,
                "duracao_ms": round((perf_counter() - inicio) * 1000),
                "estado": estado,
                "ferramenta": ferramenta,
                "quantidade": quantidade,
                "categoria_erro": categoria,
            }
        )
    )


class ServicoAgente:
    def __init__(
        self,
        modelo: ContratoModelo,
        ferramentas: ContratoFerramentas,
        configuracao: ConfiguracaoAplicacao,
    ) -> None:
        self.modelo = modelo
        self.ferramentas = ferramentas
        self.configuracao = configuracao

    async def processar_pergunta(self, pergunta: str) -> RespostaAgente:
        inicio = perf_counter()
        if (
            not isinstance(pergunta, str)
            or not pergunta.strip()
            or len(pergunta) > self.configuracao.agente_maximo_pergunta
            or any(ord(letra) < 32 and letra not in "\n\t" for letra in pergunta)
        ):
            return RespostaAgente(
                "entrada_invalida",
                "Informe uma pergunta válida dentro do limite configurado.",
            )
        if pergunta_pessoal(pergunta):
            return RespostaAgente(
                "bloqueada",
                "Consultas de clientes e pedidos individuais "
                "não estão disponíveis nesta fase.",
            )
        social = resposta_social(pergunta)
        if social is not None:
            return RespostaAgente("social", social)
        try:
            async with asyncio.timeout(self.configuracao.agente_timeout_total):
                resposta = await self._orquestrar(pergunta.strip())
            registrar_operacao("pergunta", inicio, resposta.estado)
            return resposta
        except ErroModelo as erro:
            registrar_operacao("modelo", inicio, "erro", categoria=erro.categoria)
            return RespostaAgente(
                "indisponivel",
                "O modelo local está indisponível ou retornou uma resposta inválida. "
                "Verifique o Ollama e o modelo configurado.",
                categoria_erro=erro.categoria,
            )
        except ErroFerramenta as erro:
            registrar_operacao(
                "ferramenta", inicio, "rejeitada", categoria=erro.categoria
            )
            return RespostaAgente(
                "bloqueada",
                "A solicitação de ferramenta foi rejeitada com segurança. "
                "Não confirmei a informação.",
            )
        except TimeoutError:
            registrar_operacao("pergunta", inicio, "erro", categoria="timeout")
            return RespostaAgente(
                "limite",
                "A operação excedeu o tempo permitido. Não confirmei a informação.",
                categoria_erro="timeout",
            )
        except ErroPublicacao:
            registrar_operacao(
                "publicacao", inicio, "erro", categoria="publicacao_indisponivel"
            )
            return RespostaAgente(
                "indisponivel",
                "As fontes da consulta não estão liberadas para atendimento.",
                categoria_erro="publicacao_indisponivel",
            )
        except ErroDados:
            registrar_operacao(
                "ferramenta", inicio, "erro", categoria="fonte_indisponivel"
            )
            return RespostaAgente(
                "indisponivel",
                "Não foi possível consultar as fontes locais "
                "para confirmar a informação.",
                categoria_erro="fonte_indisponivel",
            )

    async def _orquestrar(self, pergunta: str) -> RespostaAgente:
        mensagens = [Mensagem("system", INSTRUCOES_AGENTE), Mensagem("user", pergunta)]
        evidencias: list[Evidencia] = []
        fontes_consultadas: set[str] = set()
        repeticoes: set[str] = set()
        quantidade_chamadas = 0
        ferramentas = self.ferramentas.descrever()
        planos = {
            FONTES_FERRAMENTAS[c.nome]: c
            for c in consultas_de_recuperacao(pergunta, fontes_necessarias(pergunta))
        }
        recuperadas: set[str] = set()
        pendente = None
        for _ in range(self.configuracao.agente_maximo_etapas):
            tamanho = len(
                json.dumps(
                    {
                        "mensagens": [asdict(m) for m in mensagens],
                        "ferramentas": ferramentas,
                    },
                    ensure_ascii=False,
                ).encode()
            )
            if tamanho > self.configuracao.agente_contexto_bytes:
                return RespostaAgente(
                    "limite",
                    "O contexto excedeu o limite seguro. "
                    "Faça uma pergunta mais específica.",
                )
            inicio_modelo = perf_counter()
            async with asyncio.timeout(self.configuracao.ollama_timeout):
                faltantes = fontes_necessarias(pergunta) - fontes_consultadas
                concluir = bool(fontes_consultadas) and not faltantes
                disponiveis = ferramentas
                if fontes_consultadas and faltantes:
                    disponiveis = [
                        f
                        for f in ferramentas
                        if FONTES_FERRAMENTAS.get(f["function"]["name"]) in faltantes
                    ]
                operacao = "geracao"
                if pendente is not None:
                    turno = TurnoModelo("", (pendente,))
                    pendente = None
                    operacao = "recuperacao"
                else:
                    turno = await self.modelo.responder(
                        tuple(mensagens), [] if concluir else disponiveis
                    )
            registrar_operacao(
                operacao, inicio_modelo, "concluida", quantidade=len(turno.chamadas)
            )
            if not turno.chamadas:
                recuperacao = (
                    [
                        c
                        for fonte, c in planos.items()
                        if fonte in faltantes and fonte not in recuperadas
                    ]
                    if permite_recuperacao(turno.conteudo)
                    else []
                )
                if recuperacao:
                    recuperadas.update(FONTES_FERRAMENTAS[c.nome] for c in recuperacao)
                    turno = TurnoModelo("", tuple(recuperacao))
                    registrar_operacao(
                        "recuperacao",
                        inicio_modelo,
                        "iniciada",
                        quantidade=len(recuperacao),
                    )
                else:
                    resposta = finalizar_resposta(turno.conteudo, pergunta, evidencias)
                    if resposta.estado == "sem_evidencias":
                        resposta = replace(
                            resposta,
                            fontes_sem_resultado=tuple(
                                sorted(
                                    fontes_consultadas
                                    - {e.dado.fonte for e in evidencias}
                                )
                            ),
                        )
                    return resposta
            if (
                quantidade_chamadas + len(turno.chamadas)
                > self.configuracao.agente_maximo_chamadas
            ):
                break
            mensagens.append(Mensagem("assistant", "", turno.chamadas))
            for solicitada in turno.chamadas:
                chamada = self.ferramentas.validar(solicitada)
                chave = json.dumps(asdict(chamada), sort_keys=True, ensure_ascii=False)
                if chave in repeticoes:
                    return RespostaAgente(
                        "limite",
                        "O modelo repetiu uma consulta. "
                        "Não confirmei novas informações.",
                    )
                repeticoes.add(chave)
                quantidade_chamadas += 1
                inicio = perf_counter()
                async with asyncio.timeout(self.configuracao.agente_timeout_ferramenta):
                    dados = await self.ferramentas.executar(chamada)
                if len(dados) > self.configuracao.agente_maximo_resultados:
                    raise ErroFerramenta("resultado_excessivo")
                fonte = FONTES_FERRAMENTAS.get(chamada.nome)
                if fonte is not None:
                    fontes_consultadas.add(fonte)
                    if not dados and fonte not in recuperadas and fonte in planos:
                        alternativa = self.ferramentas.validar(planos[fonte])
                        chave_alternativa = json.dumps(
                            asdict(alternativa), sort_keys=True, ensure_ascii=False
                        )
                        if chave_alternativa not in repeticoes:
                            pendente = alternativa
                            recuperadas.add(fonte)
                novas = [
                    Evidencia(f"E{len(evidencias) + indice + 1}", dado)
                    for indice, dado in enumerate(dados)
                ]
                evidencias.extend(novas)
                mensagens.append(
                    Mensagem(
                        "tool",
                        json.dumps(
                            [
                                {
                                    "identificador": e.identificador,
                                    "fonte": e.dado.fonte,
                                    "texto": e.dado.texto,
                                }
                                for e in novas
                            ],
                            ensure_ascii=False,
                        ),
                        ferramenta=chamada.nome,
                    )
                )
                registrar_operacao(
                    "consulta",
                    inicio,
                    "concluida",
                    ferramenta=chamada.nome,
                    quantidade=len(dados),
                )
        return RespostaAgente(
            "limite",
            "O limite de etapas ou chamadas foi atingido. Não confirmei a informação.",
        )
