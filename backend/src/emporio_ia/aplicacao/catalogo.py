from decimal import Decimal

from emporio_ia.aplicacao.contratos import (
    ContratoCategorias,
    ContratoProdutos,
    ContratoPromocoes,
)
from emporio_ia.dominio.consultas import (
    EstoqueProduto,
    FiltroProdutos,
    centavos_para_decimal,
    validar_numero_consulta,
)
from emporio_ia.dominio.entidades import Categoria, Produto, Promocao
from emporio_ia.dominio.excecoes import ErroValidacao


class ServicoCatalogo:
    def __init__(
        self,
        produtos: ContratoProdutos,
        categorias: ContratoCategorias,
        promocoes: ContratoPromocoes,
    ) -> None:
        self.produtos = produtos
        self.categorias = categorias
        self.promocoes = promocoes

    def buscar_produto(self, identificador: int) -> Produto | None:
        validar_numero_consulta(identificador)
        return self.produtos.buscar_por_identificador(identificador)

    def buscar_produtos(self, filtros: FiltroProdutos | None = None) -> list[Produto]:
        return self.produtos.buscar_produtos(filtros or FiltroProdutos())

    def buscar_por_nome(self, nome: str) -> list[Produto]:
        return self.buscar_produtos(FiltroProdutos(nome=nome))

    def consultar_preco(self, identificador: int) -> Decimal | None:
        produto = self.buscar_produto(identificador)
        return centavos_para_decimal(produto.preco_centavos) if produto else None

    def consultar_estoque(self, identificador: int) -> EstoqueProduto | None:
        produto = self.buscar_produto(identificador)
        if produto is None:
            return None
        return EstoqueProduto(
            quantidade=produto.quantidade_estoque,
            estado=produto.estado,
            disponivel=produto.disponivel,
        )

    def listar_categorias(self) -> list[Categoria]:
        return self.categorias.listar_categorias()

    def consultar_categoria(self, identificador: int) -> Categoria | None:
        validar_numero_consulta(identificador)
        return self.categorias.buscar_por_identificador(identificador)

    def consultar_promocoes(
        self, *, produto_id: int | None = None, ativas: bool | None = None
    ) -> list[Promocao]:
        if produto_id is not None:
            validar_numero_consulta(produto_id)
        if ativas is not None and type(ativas) is not bool:
            raise ErroValidacao("Filtro de promoção inválido.")
        return self.promocoes.consultar_promocoes(produto_id, ativas)
