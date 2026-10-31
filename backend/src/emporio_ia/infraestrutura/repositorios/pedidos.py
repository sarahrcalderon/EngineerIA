from datetime import date

from emporio_ia.dominio.consultas import validar_numero_consulta
from emporio_ia.dominio.entidades import ConsultaPedido, ItemPedido
from emporio_ia.infraestrutura.banco import BancoSQLite


class RepositorioPedidos:
    def __init__(self, banco: BancoSQLite) -> None:
        self.banco = banco

    def consultar_pedido(
        self, identificador: int, cliente_id: int
    ) -> ConsultaPedido | None:
        validar_numero_consulta(identificador)
        validar_numero_consulta(cliente_id)
        # Mesmo snapshot de leitura para o cabeçalho e seus itens.
        with self.banco.conectar() as conexao:
            pedido = conexao.execute(
                """SELECT identificador, estado, data_pedido, total_centavos,
                          codigo_rastreamento, entrega_estimada
                   FROM pedidos WHERE identificador = ? AND cliente_id = ?""",
                (identificador, cliente_id),
            ).fetchone()
            if pedido is None:
                return None
            itens = conexao.execute(
                """SELECT pedido_id, quantidade, produto_id FROM itens_pedido
                   WHERE pedido_id = ? ORDER BY produto_id""",
                (identificador,),
            ).fetchall()
        return ConsultaPedido(
            identificador=pedido["identificador"],
            estado=pedido["estado"],
            data_pedido=date.fromisoformat(pedido["data_pedido"]),
            total_centavos=pedido["total_centavos"],
            codigo_rastreamento=pedido["codigo_rastreamento"],
            entrega_estimada=(
                date.fromisoformat(pedido["entrega_estimada"])
                if pedido["entrega_estimada"] is not None
                else None
            ),
            itens=tuple(ItemPedido(**dict(item)) for item in itens),
        )
