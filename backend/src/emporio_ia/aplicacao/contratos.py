from typing import Protocol

from emporio_ia.dominio.consultas import FiltroProdutos
from emporio_ia.dominio.entidades import Categoria, ConsultaPedido, Produto, Promocao


class ContratoProdutos(Protocol):
    def buscar_por_identificador(self, identificador: int) -> Produto | None: ...

    def buscar_produtos(self, filtros: FiltroProdutos) -> list[Produto]: ...


class ContratoCategorias(Protocol):
    def listar_categorias(self) -> list[Categoria]: ...

    def buscar_por_identificador(self, identificador: int) -> Categoria | None: ...


class ContratoPromocoes(Protocol):
    def consultar_promocoes(
        self, produto_id: int | None, ativas: bool | None
    ) -> list[Promocao]: ...


class ContratoPedidos(Protocol):
    def consultar_pedido(
        self, identificador: int, cliente_id: int
    ) -> ConsultaPedido | None: ...
