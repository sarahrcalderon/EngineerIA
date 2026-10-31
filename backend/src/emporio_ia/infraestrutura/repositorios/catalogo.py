from emporio_ia.dominio.consultas import validar_numero_consulta
from emporio_ia.dominio.entidades import Categoria, Promocao
from emporio_ia.infraestrutura.banco import BancoSQLite


class RepositorioCategorias:
    def __init__(self, banco: BancoSQLite) -> None:
        self.banco = banco

    def listar_categorias(self) -> list[Categoria]:
        with self.banco.conectar() as conexao:
            linhas = conexao.execute(
                "SELECT identificador, nome, descricao FROM categorias "
                "ORDER BY identificador"
            ).fetchall()
        return [Categoria(**dict(linha)) for linha in linhas]

    def buscar_por_identificador(self, identificador: int) -> Categoria | None:
        validar_numero_consulta(identificador)
        with self.banco.conectar() as conexao:
            linha = conexao.execute(
                "SELECT identificador, nome, descricao FROM categorias "
                "WHERE identificador = ?",
                (identificador,),
            ).fetchone()
        return Categoria(**dict(linha)) if linha is not None else None


class RepositorioPromocoes:
    def __init__(self, banco: BancoSQLite) -> None:
        self.banco = banco

    def consultar_promocoes(
        self, produto_id: int | None = None, ativas: bool | None = None
    ) -> list[Promocao]:
        if produto_id is not None:
            validar_numero_consulta(produto_id)
        with self.banco.conectar() as conexao:
            linhas = conexao.execute(
                """SELECT identificador, produto_id, desconto_pontos_base,
                          descricao, ativa
                   FROM promocoes
                   WHERE (? IS NULL OR produto_id = ?) AND (? IS NULL OR ativa = ?)
                   ORDER BY identificador""",
                (produto_id, produto_id, ativas, ativas),
            ).fetchall()
        return [
            Promocao(
                identificador=linha["identificador"],
                produto_id=linha["produto_id"],
                desconto_pontos_base=linha["desconto_pontos_base"],
                descricao=linha["descricao"],
                ativa=bool(linha["ativa"]),
            )
            for linha in linhas
        ]
