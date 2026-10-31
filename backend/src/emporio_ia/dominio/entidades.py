from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class Categoria:
    identificador: int
    nome: str
    descricao: str


@dataclass(frozen=True, slots=True)
class Produto:
    identificador: int
    preco_centavos: int
    nome: str
    categoria_id: int
    descricao: str
    quantidade_estoque: int
    estado: str
    especificacoes: str
    criado_em: date

    @property
    def disponivel(self) -> bool:
        return self.estado == "active" and self.quantidade_estoque > 0


@dataclass(frozen=True, slots=True)
class Promocao:
    identificador: int
    produto_id: int
    desconto_pontos_base: int
    descricao: str
    ativa: bool
    # A origem não fornece início/fim; o indicador ativo não comprova vigência.
    validade_temporal: str = field(default="indisponivel", init=False)


@dataclass(frozen=True, slots=True, repr=False)
class Cliente:
    identificador: int
    nome: str
    telefone: str
    email: str
    cidade: str


@dataclass(frozen=True, slots=True, repr=False)
class Pedido:
    identificador: int
    cliente_id: int
    data_pedido: date
    estado: str
    total_centavos: int
    meio_pagamento: str
    codigo_rastreamento: str | None
    entrega_estimada: date | None
    observacoes: str | None


@dataclass(frozen=True, slots=True, repr=False)
class ItemPedido:
    pedido_id: int
    quantidade: int
    produto_id: int


@dataclass(frozen=True, slots=True, repr=False)
class ConsultaPedido:
    identificador: int
    estado: str
    data_pedido: date
    total_centavos: int
    codigo_rastreamento: str | None
    entrega_estimada: date | None
    itens: tuple[ItemPedido, ...]
