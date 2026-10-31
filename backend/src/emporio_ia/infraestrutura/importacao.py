import csv
import sqlite3
from pathlib import Path

from emporio_ia.dominio.excecoes import ErroImportacao, ErroPersistencia
from emporio_ia.dominio.validacao import chave_busca
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.esquema import (
    INSTRUCOES_ESQUEMA,
    INSTRUCOES_LIMPEZA,
    VERSAO_ESQUEMA,
)
from emporio_ia.infraestrutura.formatos_csv import FORMATOS
from emporio_ia.infraestrutura.leitura_csv import ler_registros, localizar_arquivo


class ImportadorDados:
    """Substitui somente o snapshot operacional, em uma transação indivisível."""

    def __init__(self, banco: BancoSQLite) -> None:
        self.banco = banco

    def importar(self, diretorio: Path) -> dict[str, int]:
        try:
            caminhos = {
                formato.nome_arquivo: localizar_arquivo(diretorio, formato.nome_arquivo)
                for formato in FORMATOS
            }
            resumo: dict[str, int] = {}
            with self.banco.conectar(escrita=True) as conexao:
                versao = conexao.execute("PRAGMA user_version").fetchone()[0]
                if versao not in {0, VERSAO_ESQUEMA}:
                    raise ErroImportacao(
                        "Versão do banco incompatível com o importador."
                    )
                if (
                    versao == 0
                    and conexao.execute(
                        "SELECT 1 FROM sqlite_master WHERE type = 'table' LIMIT 1"
                    ).fetchone()
                ):
                    raise ErroImportacao(
                        "Banco sem versão reconhecida; use um arquivo dedicado."
                    )
                for instrucao in INSTRUCOES_ESQUEMA:
                    conexao.execute(instrucao)
                for instrucao in INSTRUCOES_LIMPEZA:
                    conexao.execute(instrucao)
                for formato in FORMATOS:
                    quantidade = 0
                    for registro in ler_registros(
                        caminhos[formato.nome_arquivo], formato
                    ):
                        if formato.nome_conjunto == "produtos":
                            registro = (*registro, chave_busca(str(registro[2])))
                        try:
                            conexao.execute(formato.inserir_sql, registro)
                        except sqlite3.IntegrityError:
                            raise ErroImportacao(
                                f"{formato.nome_arquivo}: violação de integridade; "
                                "verifique chaves, referências e restrições."
                            ) from None
                        quantidade += 1
                    resumo[formato.nome_conjunto] = quantidade
                if conexao.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise ErroImportacao(
                        "Relacionamentos inconsistentes na importação."
                    )
                conexao.execute("PRAGMA user_version = 1")
            return resumo
        except ErroImportacao:
            raise
        except (OSError, UnicodeError, csv.Error):
            raise ErroImportacao("Falha ao ler os CSVs operacionais locais.") from None
        except ErroPersistencia:
            raise ErroImportacao("Falha no banco; importação não confirmada.") from None
