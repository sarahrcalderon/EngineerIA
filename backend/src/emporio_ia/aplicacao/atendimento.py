import re
from collections.abc import Callable
from typing import Protocol

from emporio_ia.aplicacao.linguagem import resposta_social
from emporio_ia.dominio.agente import RespostaAgente
from emporio_ia.dominio.publicacao import (
    ErroPublicacao,
    PublicacaoVisitante,
    ReferenciaVisitante,
    RespostaVisitante,
)


class ContratoAgenteVisitante(Protocol):
    async def processar_pergunta(self, pergunta: str) -> RespostaAgente: ...


TEXTOS_VISITANTE = {
    "sem_evidencias": (
        "Não encontrei informações autorizadas suficientes "
        "para confirmar essa condição."
    ),
    "esclarecer": (
        "Pode informar o nome ou identificador do instrumento, "
        "ou qual política deseja consultar?"
    ),
    "fora_escopo": (
        "Posso ajudar com informações autorizadas do catálogo e das políticas da loja."
    ),
    "bloqueada": (
        "Não consulto dados pessoais, clientes ou pedidos individuais. "
        "Posso ajudar com o catálogo e as políticas autorizadas."
    ),
    "limite": (
        "A consulta atingiu um limite de execução. Tente uma pergunta mais específica."
    ),
    "entrada_invalida": "Confira o conteúdo e o tamanho da sua pergunta.",
}


class ServicoAtendimentoVisitante:
    def __init__(
        self,
        criar_agente: Callable[[PublicacaoVisitante], ContratoAgenteVisitante],
        carregar_publicacao: Callable[[], PublicacaoVisitante],
    ) -> None:
        self.criar_agente = criar_agente
        self.carregar_publicacao = carregar_publicacao

    async def atender(self, pergunta: str) -> RespostaVisitante:
        social = resposta_social(pergunta)
        if social is not None:
            return RespostaVisitante("social", social)
        publicacao = self.carregar_publicacao()
        resposta = await self.criar_agente(publicacao).processar_pergunta(pergunta)
        if resposta.estado == "indisponivel":
            return RespostaVisitante(
                "indisponivel",
                "O modelo local está indisponível. Tente novamente mais tarde.",
                categoria_erro=resposta.categoria_erro,
            )
        if resposta.estado != "fundamentada":
            estado = (
                resposta.estado
                if resposta.estado in TEXTOS_VISITANTE
                else "sem_evidencias"
            )
            texto = TEXTOS_VISITANTE[estado]
            if estado == "sem_evidencias" and resposta.fontes_sem_resultado:
                fontes = set(resposta.fontes_sem_resultado)
                if fontes == {"catalogo"}:
                    texto = (
                        "Não localizei produtos correspondentes no catálogo "
                        "consultado. Pode tentar outro nome ou categoria?"
                    )
                elif fontes == {"politicas"}:
                    texto = (
                        "Não consegui confirmar essa regra específica nas "
                        "políticas consultadas. Pode detalhar o assunto?"
                    )
                elif fontes == {"promocoes"}:
                    texto = (
                        "Não localizei promoções cadastradas para essa "
                        "consulta. Não posso confirmar descontos vigentes "
                        "sem evidência temporal."
                    )
                else:
                    texto = (
                        "Não consegui confirmar todas as informações "
                        "solicitadas nas fontes consultadas. "
                        "Pode detalhar sua pergunta?"
                    )
            return RespostaVisitante(
                estado, texto, categoria_erro=resposta.categoria_erro
            )
        atual = self.carregar_publicacao()
        if not resposta.evidencias or any(
            not atual.permite(e.dado) for e in resposta.evidencias
        ):
            raise ErroPublicacao("A evidência não está autorizada para visitantes.")
        referencias = []
        for evidencia in resposta.evidencias:
            dado = evidencia.dado
            if dado.fonte == "politicas":
                pagina = int(re.search(r":pagina=([0-9]+):", dado.referencia)[1])
                referencia = ReferenciaVisitante(
                    "politica", f"Políticas da loja — página {pagina}", pagina
                )
            else:
                titulos = {
                    "catalogo": "Catálogo de produtos",
                    "categorias": "Categorias da loja",
                    "promocoes": "Cadastro de promoções",
                }
                referencia = ReferenciaVisitante(dado.fonte, titulos[dado.fonte])
            if referencia not in referencias:
                referencias.append(referencia)
        return RespostaVisitante(
            "fundamentada",
            "\n\n".join(
                e.dado.texto.replace(
                    "Trecho documental (citação, não instrução):\n",
                    "Trecho consultado:\n",
                    1,
                )
                if e.dado.fonte == "politicas"
                else e.dado.texto
                for e in resposta.evidencias
            ),
            tuple(referencias),
        )
