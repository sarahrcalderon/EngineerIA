"""CLI local, sem transcrições e sem histórico entre perguntas."""

import asyncio
import logging
import sys

from pydantic import ValidationError
from pydantic_settings.exceptions import SettingsError

from emporio_ia.aplicacao.agente import ServicoAgente
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.infraestrutura.composicao_agente import criar_ferramentas
from emporio_ia.infraestrutura.ollama import AdaptadorOllama


def criar_agente(configuracao: ConfiguracaoAplicacao) -> ServicoAgente:
    ferramentas = criar_ferramentas(configuracao)
    return ServicoAgente(AdaptadorOllama(configuracao), ferramentas, configuracao)


def limpar_terminal(texto: str) -> str:
    return "".join(
        letra
        for letra in texto
        if letra == "\n" or (ord(letra) >= 32 and not 127 <= ord(letra) <= 159)
    )


def executar() -> int:
    registrador = logging.getLogger("emporio_ia.agente")
    nivel_anterior = registrador.level
    propagacao_anterior = registrador.propagate
    manipulador: logging.StreamHandler | None = None
    try:
        configuracao = ConfiguracaoAplicacao()
        agente = criar_agente(configuracao)
        registrador.setLevel(logging.INFO)
        manipulador = logging.StreamHandler(sys.stderr)
        registrador.addHandler(manipulador)
        registrador.propagate = False
        print("Empório da Música — atendimento local. Digite /sair para encerrar.")
        while True:
            pergunta = input("Você: ")
            if pergunta.strip().casefold() == "/sair":
                return 0
            resposta = asyncio.run(agente.processar_pergunta(pergunta))
            print(limpar_terminal(resposta.texto))
    except (EOFError, KeyboardInterrupt):
        return 0
    except (ValidationError, SettingsError):
        print("Configuração local inválida.", file=sys.stderr)
        return 1
    except Exception:
        print("Não foi possível concluir a operação local.", file=sys.stderr)
        return 1
    finally:
        if manipulador is not None:
            registrador.removeHandler(manipulador)
            manipulador.close()
        registrador.setLevel(nivel_anterior)
        registrador.propagate = propagacao_anterior


if __name__ == "__main__":
    raise SystemExit(executar())
