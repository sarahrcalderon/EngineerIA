from dataclasses import dataclass
from decimal import Decimal

from emporio_ia.dominio.excecoes import ErroValidacao
from emporio_ia.dominio.validacao import LIMITE_INTEIRO

MAXIMO_PRODUTOS_ATENDIMENTO = 20


def validar_numero_consulta(numero: int, *, minimo: int = 1) -> None:
    if type(numero) is not int or not minimo <= numero <= LIMITE_INTEIRO:
        raise ErroValidacao("Parâmetro inteiro fora do intervalo permitido.")


@dataclass(frozen=True, slots=True)
class FiltroProdutos:
    nome: str | None = None
    categoria_id: int | None = None
    preco_minimo_centavos: int | None = None
    preco_maximo_centavos: int | None = None
    disponiveis: bool | None = None
    limite: int = 50
    deslocamento: int = 0
    categoria: str | None = None
    ordenacao: str = "identificador"
    identificadores: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        if self.ordenacao not in {
            "identificador",
            "preco_crescente",
            "preco_decrescente",
        }:
            raise ErroValidacao("Ordenação inválida.")
        if self.identificadores is not None:
            if (
                not isinstance(self.identificadores, tuple)
                or len(self.identificadores) > 500
            ):
                raise ErroValidacao("Seleção de publicação inválida.")
            for identificador in self.identificadores:
                validar_numero_consulta(identificador)
        if self.categoria is not None and (
            not isinstance(self.categoria, str)
            or not self.categoria.strip()
            or len(self.categoria) > 200
            or "\x00" in self.categoria
        ):
            raise ErroValidacao("Categoria inválida.")
        validar_numero_consulta(self.limite)
        validar_numero_consulta(self.deslocamento, minimo=0)
        if self.limite > 200:
            raise ErroValidacao("A consulta permite no máximo 200 produtos por página.")
        if self.categoria_id is not None:
            validar_numero_consulta(self.categoria_id)
        for preco in (self.preco_minimo_centavos, self.preco_maximo_centavos):
            if preco is not None:
                validar_numero_consulta(preco, minimo=0)
        if (
            self.preco_minimo_centavos is not None
            and self.preco_maximo_centavos is not None
            and self.preco_minimo_centavos > self.preco_maximo_centavos
        ):
            raise ErroValidacao("Faixa de preço invertida.")
        if self.nome is not None and (
            not isinstance(self.nome, str)
            or not self.nome.strip()
            or len(self.nome) > 200
            or "\x00" in self.nome
        ):
            raise ErroValidacao("Nome de busca inválido.")
        if self.disponiveis is not None and type(self.disponiveis) is not bool:
            raise ErroValidacao("Filtro de disponibilidade inválido.")


@dataclass(frozen=True, slots=True)
class EstoqueProduto:
    quantidade: int
    estado: str
    disponivel: bool


def centavos_para_decimal(centavos: int) -> Decimal:
    validar_numero_consulta(centavos, minimo=0)
    # Construção exata, independente da precisão global do contexto Decimal.
    return Decimal(f"{centavos // 100}.{centavos % 100:02d}")
