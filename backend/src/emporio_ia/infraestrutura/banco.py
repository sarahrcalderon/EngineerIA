import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from emporio_ia.dominio.excecoes import ErroPersistencia


class BancoSQLite:
    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho.resolve()

    @contextmanager
    def conectar(self, *, escrita: bool = False) -> Iterator[sqlite3.Connection]:
        conexao: sqlite3.Connection | None = None
        try:
            if escrita:
                self.caminho.parent.mkdir(parents=True, exist_ok=True)
            modo = "rwc" if escrita else "ro"
            conexao = sqlite3.connect(
                f"{self.caminho.as_uri()}?mode={modo}",
                uri=True,
                autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL,
                isolation_level=None,
                timeout=10,
            )
            conexao.row_factory = sqlite3.Row
            conexao.execute("PRAGMA foreign_keys = ON")
            if not escrita:
                conexao.execute("PRAGMA query_only = ON")
            conexao.execute("BEGIN IMMEDIATE" if escrita else "BEGIN")
            yield conexao
            conexao.commit()
        except (sqlite3.Error, OSError):
            if conexao is not None:
                conexao.rollback()
            raise ErroPersistencia(
                "Falha ao acessar o banco operacional local."
            ) from None
        except BaseException:
            if conexao is not None:
                conexao.rollback()
            raise
        finally:
            if conexao is not None:
                conexao.close()
