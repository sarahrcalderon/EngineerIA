import csv
from collections.abc import Iterator
from datetime import date
from pathlib import Path

from emporio_ia.dominio.excecoes import ErroImportacao, ErroValidacao
from emporio_ia.infraestrutura.formatos_csv import FormatoCsv, ValorConvertido

type RegistroConvertido = tuple[str | int | None, ...]


def localizar_arquivo(diretorio: Path, nome: str) -> Path:
    # Correspondência por sufixo conhecido, nunca escolher silenciosamente entre dois.
    candidatos = [
        caminho
        for caminho in diretorio.iterdir()
        if caminho.is_file()
        and (caminho.name == nome or caminho.name.endswith(f" - {nome}"))
    ]
    if len(candidatos) != 1:
        raise ErroImportacao(f"{nome}: arquivo ausente ou nome ambíguo.")
    return candidatos[0]


def serializar_valor(valor: ValorConvertido) -> str | int | None:
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, bool):
        return int(valor)
    return valor


def ler_registros(caminho: Path, formato: FormatoCsv) -> Iterator[RegistroConvertido]:
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=",", strict=True)
        cabecalhos = leitor.fieldnames
        esperados = [campo.cabecalho for campo in formato.campos]
        if (
            cabecalhos is None
            or len(cabecalhos) != len(esperados)
            or set(cabecalhos) != set(esperados)
        ):
            raise ErroImportacao(f"{formato.nome_arquivo}: cabeçalhos incompatíveis.")

        chaves: set[tuple[str | int | None, ...]] = set()
        for linha in leitor:
            contexto = f"{formato.nome_arquivo}, linha {leitor.line_num}"
            if None in linha or any(valor is None for valor in linha.values()):
                raise ErroImportacao(f"{contexto}: quantidade de campos inválida.")
            valores: list[str | int | None] = []
            for campo in formato.campos:
                try:
                    valores.append(
                        serializar_valor(campo.converter(linha[campo.cabecalho]))
                    )
                except ErroValidacao as erro:
                    raise ErroImportacao(
                        f"{contexto}, coluna {campo.cabecalho}: {erro}"
                    ) from None
            registro = tuple(valores)
            chave = tuple(registro[posicao] for posicao in formato.posicoes_chave)
            if chave in chaves:
                raise ErroImportacao(f"{contexto}: chave duplicada.")
            chaves.add(chave)
            yield registro

        if not chaves:
            raise ErroImportacao(f"{formato.nome_arquivo}: conjunto sem registros.")
