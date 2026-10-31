from datetime import date
from decimal import Decimal

import pytest

from emporio_ia.aplicacao.catalogo import ServicoCatalogo
from emporio_ia.aplicacao.pedidos import ServicoPedidos
from emporio_ia.dominio.consultas import FiltroProdutos
from emporio_ia.dominio.excecoes import ErroPersistencia, ErroValidacao
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.repositorios.produtos import RepositorioProdutos


def test_busca_por_identificador(catalogo: ServicoCatalogo) -> None:
    produto = catalogo.buscar_produto(201)
    assert produto is not None
    assert produto.nome == "Cordas Órbita Sintética"
    assert produto.criado_em == date(2025, 1, 2)
    assert produto.preco_centavos == 1010


def test_busca_nome_sem_acento_ou_caixa(catalogo: ServicoCatalogo) -> None:
    assert [
        produto.identificador for produto in catalogo.buscar_por_nome("ORBITA")
    ] == [201]
    assert [
        produto.identificador for produto in catalogo.buscar_por_nome(" laboratório ")
    ] == [202]


def test_filtros_categoria_preco_e_paginacao(catalogo: ServicoCatalogo) -> None:
    assert [
        produto.identificador
        for produto in catalogo.buscar_produtos(FiltroProdutos(categoria_id=901))
    ] == [201, 203]
    filtros = FiltroProdutos(preco_minimo_centavos=1010, preco_maximo_centavos=2020)
    assert [produto.identificador for produto in catalogo.buscar_produtos(filtros)] == [
        201,
        202,
    ]
    assert [
        produto.identificador
        for produto in catalogo.buscar_produtos(
            FiltroProdutos(limite=1, deslocamento=1)
        )
    ] == [202]
    assert catalogo.buscar_produtos(FiltroProdutos(preco_maximo_centavos=0)) == []


def test_preco_decimal_e_estoque(catalogo: ServicoCatalogo) -> None:
    assert catalogo.consultar_preco(201) == Decimal("10.10")
    assert catalogo.consultar_preco(204) == Decimal("0.10")
    estoque = catalogo.consultar_estoque(201)
    assert estoque is not None
    assert estoque.quantidade == 3
    assert estoque.disponivel is True
    for identificador in (202, 203, 204):
        assert catalogo.consultar_estoque(identificador).disponivel is False
    assert [
        produto.identificador
        for produto in catalogo.buscar_produtos(FiltroProdutos(disponiveis=True))
    ] == [201]
    assert [
        produto.identificador
        for produto in catalogo.buscar_produtos(FiltroProdutos(disponiveis=False))
    ] == [202, 203, 204]


def test_categorias(catalogo: ServicoCatalogo) -> None:
    assert [categoria.identificador for categoria in catalogo.listar_categorias()] == [
        901,
        902,
    ]
    assert catalogo.consultar_categoria(901).nome == "Cordas de teste"
    assert catalogo.consultar_categoria(999999) is None


def test_promocoes_ativas_inativas_sem_vigencia_inventada(
    catalogo: ServicoCatalogo,
) -> None:
    assert len(catalogo.consultar_promocoes()) == 2
    ativas = catalogo.consultar_promocoes(ativas=True)
    assert [promocao.identificador for promocao in ativas] == [601]
    assert ativas[0].desconto_pontos_base == 1250
    assert ativas[0].validade_temporal == "indisponivel"
    assert [
        promocao.identificador
        for promocao in catalogo.consultar_promocoes(ativas=False)
    ] == [602]
    assert [
        promocao.identificador
        for promocao in catalogo.consultar_promocoes(produto_id=201)
    ] == [601]
    assert catalogo.consultar_promocoes(produto_id=999999) == []


def test_inexistente_diferente_de_estoque_zero(catalogo: ServicoCatalogo) -> None:
    assert catalogo.buscar_produto(999999) is None
    assert catalogo.consultar_preco(999999) is None
    assert catalogo.consultar_estoque(999999) is None
    assert catalogo.buscar_por_nome("NÃO EXISTE") == []
    assert catalogo.consultar_estoque(202).quantidade == 0


@pytest.mark.parametrize(
    "nome", ["' OR 1=1 --", "'; DROP TABLE produtos; --", "_' OR ''='"]
)
def test_consultas_parametrizadas(catalogo: ServicoCatalogo, nome: str) -> None:
    assert catalogo.buscar_por_nome(nome) == []
    assert len(catalogo.buscar_produtos()) == 4


def test_caracteres_like_sao_literais(catalogo: ServicoCatalogo) -> None:
    assert [produto.identificador for produto in catalogo.buscar_por_nome("%_")] == [
        203
    ]


def test_pedidos_internos_itens_e_entrega(pedidos: ServicoPedidos) -> None:
    primeiro = pedidos.consultar_pedido(701, cliente_id=801)
    assert primeiro is not None
    assert primeiro.estado == "pending"
    assert primeiro.total_centavos == 2020
    assert primeiro.codigo_rastreamento is None
    assert primeiro.entrega_estimada is None
    assert [(item.produto_id, item.quantidade) for item in primeiro.itens] == [(201, 2)]
    segundo = pedidos.consultar_pedido(702, cliente_id=802)
    assert segundo.codigo_rastreamento == "RASTREAMENTO-SINTETICO"
    assert segundo.entrega_estimada == date(2025, 2, 12)


def test_pedido_de_outro_cliente_nao_e_retornado(pedidos: ServicoPedidos) -> None:
    assert pedidos.consultar_pedido(701, cliente_id=802) is None
    assert pedidos.consultar_pedido(999999, cliente_id=801) is None


def test_rejeita_identificador_sql(
    catalogo: ServicoCatalogo, pedidos: ServicoPedidos
) -> None:
    with pytest.raises(ErroValidacao):
        catalogo.buscar_produto("201 OR 1=1")
    with pytest.raises(ErroValidacao):
        pedidos.consultar_pedido(701, cliente_id="801 OR 1=1")


def test_banco_ausente_nao_e_criado_pela_leitura(tmp_path) -> None:
    caminho = tmp_path / "inexistente.sqlite3"
    repositorio = RepositorioProdutos(BancoSQLite(caminho))
    with pytest.raises(ErroPersistencia):
        repositorio.buscar_por_identificador(201)
    assert not caminho.exists()
