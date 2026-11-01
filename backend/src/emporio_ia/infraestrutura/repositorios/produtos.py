from datetime import date
from sqlite3 import Row

from emporio_ia.dominio.busca_produtos import normalizar_busca_produto
from emporio_ia.dominio.consultas import FiltroProdutos, validar_numero_consulta
from emporio_ia.dominio.entidades import Produto
from emporio_ia.infraestrutura.banco import BancoSQLite

COLUNAS_PRODUTO = """identificador, preco_centavos, nome, categoria_id, descricao,
    quantidade_estoque, estado, especificacoes, criado_em"""


def converter_produto(linha: Row) -> Produto:
    return Produto(
        identificador=linha["identificador"],
        preco_centavos=linha["preco_centavos"],
        nome=linha["nome"],
        categoria_id=linha["categoria_id"],
        descricao=linha["descricao"],
        quantidade_estoque=linha["quantidade_estoque"],
        estado=linha["estado"],
        especificacoes=linha["especificacoes"],
        criado_em=date.fromisoformat(linha["criado_em"]),
    )


class RepositorioProdutos:
    def __init__(self, banco: BancoSQLite) -> None:
        self.banco = banco

    def buscar_por_identificador(self, identificador: int) -> Produto | None:
        validar_numero_consulta(identificador)
        with self.banco.conectar() as conexao:
            linha = conexao.execute(
                f"SELECT {COLUNAS_PRODUTO} FROM produtos WHERE identificador = ?",
                (identificador,),
            ).fetchone()
        return converter_produto(linha) if linha is not None else None

    def buscar_produtos(self, filtros: FiltroProdutos) -> list[Produto]:
        condicoes: list[str] = []
        parametros: list[str | int] = []
        if filtros.nome is not None:
            # instr faz busca literal, inclusive para %, _ e tentativas de SQL.
            condicoes.append(
                "(instr(normalizar_produto(nome_busca), ?) > 0 OR EXISTS "
                "(SELECT 1 FROM categorias c WHERE c.identificador = "
                "produtos.categoria_id "
                "AND instr(normalizar_produto(c.nome), ?) > 0))"
            )
            parametros.extend([normalizar_busca_produto(filtros.nome)] * 2)
        for valor, condicao in (
            (filtros.categoria_id, "categoria_id = ?"),
            (filtros.preco_minimo_centavos, "preco_centavos >= ?"),
            (filtros.preco_maximo_centavos, "preco_centavos <= ?"),
        ):
            if valor is not None:
                condicoes.append(condicao)
                parametros.append(valor)
        if filtros.disponiveis is not None:
            disponibilidade = "(estado = 'active' AND quantidade_estoque > 0)"
            condicoes.append(
                disponibilidade if filtros.disponiveis else f"NOT {disponibilidade}"
            )
        clausula = " AND ".join(condicoes) if condicoes else "1 = 1"
        parametros.extend((filtros.limite, filtros.deslocamento))
        # Apenas fragmentos constantes compõem o SQL; todos os valores são parâmetros.
        with self.banco.conectar() as conexao:
            conexao.create_function(
                "normalizar_produto", 1, normalizar_busca_produto, deterministic=True
            )
            linhas = conexao.execute(
                f"SELECT {COLUNAS_PRODUTO} FROM produtos WHERE {clausula} "
                "ORDER BY identificador LIMIT ? OFFSET ?",
                parametros,
            ).fetchall()
        return [converter_produto(linha) for linha in linhas]
