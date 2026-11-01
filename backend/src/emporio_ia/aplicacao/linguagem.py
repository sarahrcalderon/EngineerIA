"""Atos sociais e recuperação limitada de consultas comerciais explícitas."""

import re

from emporio_ia.aplicacao.consulta_catalogo import interpretar_consulta_catalogo
from emporio_ia.aplicacao.fundamentacao import FinalizacaoModelo
from emporio_ia.dominio.agente import ChamadaFerramenta
from emporio_ia.dominio.busca_produtos import normalizar_busca_produto
from emporio_ia.dominio.validacao import chave_busca


def resposta_social(pergunta: str) -> str | None:
    if not isinstance(pergunta, str) or len(pergunta) > 100:
        return None
    if any(ord(letra) < 32 and letra not in "\n\t" for letra in pergunta):
        return None
    texto = " ".join(re.sub(r"[^\w\s]", " ", chave_busca(pergunta)).split())
    if texto in {
        "oi",
        "ola",
        "bom dia",
        "boa tarde",
        "boa noite",
        "tudo bem",
        "e ai",
        "oi tudo bem",
        "ola tudo bem",
        "bom dia tudo bem",
    }:
        return (
            "Olá! Seja bem-vindo à Empório da Música! 🎵 Como posso ajudar você hoje? "
            "Posso ajudar com instrumentos, preços, disponibilidade "
            "e informações da loja."
        )
    if texto in {"obrigado", "obrigada", "muito obrigado", "muito obrigada", "valeu"}:
        return "Por nada! Estou por aqui se precisar de mais alguma informação."
    if texto in {
        "ate mais",
        "ate logo",
        "tchau",
        "obrigado ate mais",
        "obrigada ate mais",
    }:
        return "Até mais! Obrigado pela visita à Empório da Música. 🎵"
    return None


TERMOS_CONVERSA = frozenset(
    "ola oi bom dia boa tarde noite gostaria quero queria "
    "saber valores valor preco precos "
    "qual quais quanto custa custam os as o a um uma uns umas do da dos das de e por "
    "para sobre voces voce vendem vende vender tem tenho temos ha existe existem "
    "produto produtos instrumento instrumentos catalogo modelo modelos comprar "
    "disponivel disponiveis disponibilidade estoque alguma algum me informar diga "
    "por favor posso tambem politica politicas troca trocas trocar devolucao devolver "
    "garantia entrega pagamento promocao promocoes desconto "
    "descontos funciona funcionam".split()
)


def consultas_de_recuperacao(
    pergunta: str, fontes: set[str]
) -> list[ChamadaFerramenta]:
    texto = chave_busca(pergunta)
    palavras = re.findall(r"[^\W_]+", texto)
    consultas = []
    if "catalogo" in fontes:
        estruturada = interpretar_consulta_catalogo(pergunta)
        identificador = re.search(r"\bproduto\s+(\d+)\b", texto)
        if estruturada is not None:
            consultas.append(ChamadaFerramenta("buscar_produtos", estruturada))
        elif identificador:
            consultas.append(
                ChamadaFerramenta(
                    "consultar_produto", {"identificador": int(identificador[1])}
                )
            )
        else:
            # Assuntos documentais não pertencem à consulta de produto.
            parte = re.split(r"\be\s+(?:qual|como|a politica|a garantia)\b", texto)[0]
            termos = [
                p for p in re.findall(r"[^\W_]+", parte) if p not in TERMOS_CONVERSA
            ]
            termo = normalizar_busca_produto(" ".join(termos))
            consultas.append(
                ChamadaFerramenta("buscar_produtos", {"termo": termo} if termo else {})
            )
    if "politicas" in fontes:
        assuntos = {
            "troca": "troca",
            "trocas": "troca",
            "trocar": "troca",
            "devolucao": "devolucao",
            "devolucoes": "devolucao",
            "devolver": "devolucao",
            "garantia": "garantia",
            "garantias": "garantia",
            "entrega": "entrega",
            "entregas": "entrega",
            "frete": "frete",
            "pagamento": "pagamento",
            "pagamentos": "pagamento",
        }
        termos = list(dict.fromkeys(assuntos[p] for p in palavras if p in assuntos))
        if termos:
            consultas.append(
                ChamadaFerramenta("buscar_politicas", {"pergunta": " ".join(termos)})
            )
    if "promocoes" in fontes:
        consultas.append(ChamadaFerramenta("consultar_promocoes", {}))
    if "categorias" in fontes:
        consultas.append(ChamadaFerramenta("consultar_categorias", {}))
    return consultas


def permite_recuperacao(conteudo: str) -> bool:
    try:
        escolha = FinalizacaoModelo.model_validate_json(conteudo)
        return escolha.tipo != "responder" and not escolha.evidencias
    except ValueError:
        return False
