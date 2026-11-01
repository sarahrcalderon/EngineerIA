"""Seleção restrita de ferramentas no transporte JSON do Ollama."""

import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from emporio_ia.aplicacao.fundamentacao import FinalizacaoModelo
from emporio_ia.dominio.agente import ChamadaFerramenta, ErroModelo, TurnoModelo


class SelecaoFerramenta(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    nome: str = Field(min_length=1, max_length=100)
    argumentos: dict[str, object] = Field(max_length=10)


class SelecaoEvidencias(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    evidencias: list[str] = Field(max_length=60)


def interpretar_evidencias(turno: TurnoModelo) -> TurnoModelo:
    try:
        if turno.chamadas:
            raise ValueError
        selecao = SelecaoEvidencias.model_validate_json(turno.conteudo)
    except (ValueError, ValidationError):
        raise ErroModelo("resposta_invalida") from None
    return TurnoModelo(
        json.dumps(
            {
                "tipo": "responder" if selecao.evidencias else "sem_evidencias",
                "evidencias": selecao.evidencias,
            }
        )
    )


def formato_selecao(ferramentas: list[dict[str, object]]) -> dict[str, object]:
    alternativas = []
    for ferramenta in ferramentas:
        funcao = ferramenta["function"]
        alternativas.append(
            {
                "type": "object",
                "properties": {
                    "nome": {"const": funcao["name"]},
                    "argumentos": funcao["parameters"],
                },
                "required": ["nome", "argumentos"],
                "additionalProperties": False,
            }
        )
    alternativas.append(
        {
            "type": "object",
            "properties": {
                "tipo": {"enum": ["esclarecer", "fora_escopo", "sem_evidencias"]},
                "evidencias": {
                    "type": "array",
                    "maxItems": 0,
                    "items": {"type": "string"},
                },
            },
            "required": ["tipo", "evidencias"],
            "additionalProperties": False,
        }
    )
    return {"oneOf": alternativas}


def instrucoes_selecao(ferramentas: list[dict[str, object]]) -> str:
    descricoes = [
        {
            "nome": f["function"]["name"],
            "descricao": f["function"]["description"],
            "campos": list(f["function"]["parameters"]["properties"]),
        }
        for f in ferramentas
    ]
    return (
        "\nETAPA DE SELEÇÃO: consulte as fontes antes de finalizar. "
        "Se há nome ou identificador, não peça esclarecimento para consultá-lo. "
        "Para solicitar ferramenta neste transporte, retorne somente "
        '{"nome":"nome_da_ferramenta","argumentos":{}}. '
        "Sem ferramenta pertinente, finalize com tipo e evidencias vazias. "
        "Ferramentas: "
        + json.dumps(descricoes, ensure_ascii=False, separators=(",", ":"))
    )


def interpretar_selecao(
    turno: TurnoModelo, ferramentas: list[dict[str, object]]
) -> TurnoModelo:
    try:
        if turno.chamadas:
            raise ValueError
        dados = json.loads(turno.conteudo)
        if isinstance(dados, dict) and "nome" in dados:
            selecao = SelecaoFerramenta.model_validate(dados)
            nomes = {f["function"]["name"] for f in ferramentas}
            if selecao.nome not in nomes:
                raise ValueError
            # O executor continua validando o esquema específico e os limites.
            return TurnoModelo(
                "", (ChamadaFerramenta(selecao.nome, selecao.argumentos),)
            )
        finalizacao = FinalizacaoModelo.model_validate(dados)
        if finalizacao.tipo == "responder" or finalizacao.evidencias:
            raise ValueError
        return turno
    except (ValueError, TypeError, ValidationError):
        raise ErroModelo("resposta_invalida") from None
