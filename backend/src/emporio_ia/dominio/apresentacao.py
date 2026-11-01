"""Projeções comerciais; não incluem descrições, IDs ou dados pessoais."""

import json
from dataclasses import dataclass


def preco_brl(centavos: int) -> str:
    inteiro, fracao = divmod(centavos, 100)
    milhares = f"{inteiro:,}".replace(",", ".")
    return f"R$ {milhares},{fracao:02d}"


@dataclass(frozen=True, slots=True)
class ProdutoApresentacao:
    nome: str
    preco_centavos: int
    disponivel: bool
    categoria: str | None

    def texto_original(self) -> str:
        preco = f"{self.preco_centavos // 100},{self.preco_centavos % 100:02d}"
        estado = "disponível" if self.disponivel else "indisponível"
        texto = (
            f"Produto cadastrado: {json.dumps(self.nome, ensure_ascii=False)}. "
            f"Preço cadastrado: R$ {preco}. Disponibilidade: {estado}."
        )
        if self.categoria is not None:
            texto += f" Categoria: {json.dumps(self.categoria, ensure_ascii=False)}."
        return texto

    def texto_cliente(self) -> str:
        estado = "Disponível" if self.disponivel else "Indisponível no momento"
        categoria = f" · {self.categoria}" if self.categoria else ""
        return f"{self.nome}\n{preco_brl(self.preco_centavos)}\n{estado}{categoria}"


@dataclass(frozen=True, slots=True)
class CategoriaApresentacao:
    nome: str

    def texto_original(self) -> str:
        return f"Categoria cadastrada: {json.dumps(self.nome, ensure_ascii=False)}."

    def texto_cliente(self) -> str:
        return self.nome


@dataclass(frozen=True, slots=True)
class PromocaoApresentacao:
    produto_id: int
    desconto_pontos_base: int
    ativa: bool

    def percentual(self) -> str:
        return (
            f"{self.desconto_pontos_base // 100},{self.desconto_pontos_base % 100:02d}%"
        )

    def texto_original(self) -> str:
        indicador = "ativo" if self.ativa else "inativo"
        return (
            f"Promoção cadastrada para produto {self.produto_id}: "
            f"desconto registrado {self.percentual()}. "
            f"Indicador no cadastro: {indicador}. "
            "Vigência temporal não confirmada; sem datas na origem."
        )

    def texto_cliente(self) -> str:
        estado = "ativa" if self.ativa else "inativa"
        return (
            f"Desconto de {self.percentual()} para o produto {self.produto_id}. "
            f"A promoção está marcada como {estado}. "
            "Vigência temporal não confirmada: não há datas informadas. "
            "Não é possível confirmar que o desconto esteja valendo hoje."
        )
