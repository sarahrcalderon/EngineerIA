from emporio_ia.aplicacao.contratos import ContratoPedidos
from emporio_ia.dominio.consultas import validar_numero_consulta
from emporio_ia.dominio.entidades import ConsultaPedido


class ServicoPedidos:
    """Uso interno confiável. Não autentica nem concede permissão de acesso.

    O chamador deverá obter o cliente de um contexto autorizado antes de expor
    este caso de uso no futuro. Informar um identificador não autentica ninguém.
    A API desta fase não recebe nem encaminha esses parâmetros.
    """

    def __init__(self, pedidos: ContratoPedidos) -> None:
        self.pedidos = pedidos

    def consultar_pedido(
        self, identificador: int, *, cliente_id: int
    ) -> ConsultaPedido | None:
        validar_numero_consulta(identificador)
        validar_numero_consulta(cliente_id)
        return self.pedidos.consultar_pedido(identificador, cliente_id)
