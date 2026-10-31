import sqlite3

from emporio_ia.dominio.busca_documental import extrair_termos
from emporio_ia.dominio.documentos import (
    DocumentoPoliticas,
    ErroDocumento,
    ResumoIndexacao,
    TrechoDocumento,
    TrechoRecuperado,
)
from emporio_ia.dominio.excecoes import ErroPersistencia, ErroValidacao
from emporio_ia.infraestrutura.banco import BancoSQLite

IDENTIFICADOR_INDICE = 0x45494433
VERSAO_INDICE = 1

ESQUEMA = (
    """CREATE TABLE IF NOT EXISTS documentos (
        identificador TEXT PRIMARY KEY,
        hash_pdf TEXT NOT NULL,
        paginas INTEGER NOT NULL CHECK (paginas > 0),
        assinatura TEXT NOT NULL
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS trechos (
        numero INTEGER PRIMARY KEY,
        identificador TEXT NOT NULL UNIQUE,
        documento_id TEXT NOT NULL REFERENCES documentos(identificador),
        pagina INTEGER NOT NULL CHECK (pagina > 0),
        secao TEXT,
        texto TEXT NOT NULL CHECK (length(texto) > 0),
        ordem INTEGER NOT NULL CHECK (ordem >= 0),
        inicio INTEGER NOT NULL CHECK (inicio >= 0),
        fim INTEGER NOT NULL CHECK (fim > inicio),
        hash_conteudo TEXT NOT NULL,
        UNIQUE (documento_id, ordem)
    ) STRICT""",
    """CREATE VIRTUAL TABLE IF NOT EXISTS busca_trechos
        USING fts5(termos, tokenize='unicode61 remove_diacritics 2')""",
)


def verificar_identidade(conexao: sqlite3.Connection, *, inicializar: bool) -> None:
    identidade = conexao.execute("PRAGMA application_id").fetchone()[0]
    versao = conexao.execute("PRAGMA user_version").fetchone()[0]
    if identidade == IDENTIFICADOR_INDICE and versao == VERSAO_INDICE:
        return
    vazio = (
        conexao.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' LIMIT 1"
        ).fetchone()
        is None
    )
    if inicializar and identidade == 0 and versao == 0 and vazio:
        return
    raise ErroDocumento("Arquivo não é um índice documental compatível.")


class RepositorioTrechos:
    def __init__(self, banco: BancoSQLite) -> None:
        self.banco = banco

    def substituir_documento(
        self,
        documento: DocumentoPoliticas,
        trechos: tuple[TrechoDocumento, ...],
        assinatura: str,
    ) -> ResumoIndexacao:
        if not trechos:
            raise ErroDocumento(
                "Não é permitido substituir o índice por trechos vazios."
            )
        try:
            with self.banco.conectar(escrita=True) as conexao:
                verificar_identidade(conexao, inicializar=True)
                for instrucao in ESQUEMA:
                    try:
                        conexao.execute(instrucao)
                    except sqlite3.OperationalError as erro:
                        if "no such module: fts5" in str(erro).lower():
                            raise ErroDocumento(
                                "SQLite local sem suporte a FTS5."
                            ) from None
                        raise
                anterior = conexao.execute(
                    "SELECT hash_pdf, assinatura FROM documentos "
                    "WHERE identificador = ?",
                    (documento.identificador,),
                ).fetchone()
                alterado = anterior is None or tuple(anterior) != (
                    documento.hash_pdf,
                    assinatura,
                )
                conexao.execute("DELETE FROM busca_trechos")
                conexao.execute("DELETE FROM trechos")
                conexao.execute("DELETE FROM documentos")
                conexao.execute(
                    "INSERT INTO documentos VALUES (?, ?, ?, ?)",
                    (
                        documento.identificador,
                        documento.hash_pdf,
                        len(documento.paginas),
                        assinatura,
                    ),
                )
                for trecho in trechos:
                    cursor = conexao.execute(
                        """INSERT INTO trechos (identificador, documento_id, pagina,
                            secao, texto, ordem, inicio, fim, hash_conteudo)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            trecho.identificador,
                            trecho.documento_id,
                            trecho.pagina,
                            trecho.secao,
                            trecho.texto,
                            trecho.ordem,
                            trecho.inicio,
                            trecho.fim,
                            trecho.hash_conteudo,
                        ),
                    )
                    conexao.execute(
                        "INSERT INTO busca_trechos(rowid, termos) VALUES (?, ?)",
                        (
                            cursor.lastrowid,
                            " ".join(
                                extrair_termos(f"{trecho.secao or ''}\n{trecho.texto}")
                            ),
                        ),
                    )
                conexao.execute(f"PRAGMA application_id = {IDENTIFICADOR_INDICE}")
                conexao.execute("PRAGMA user_version = 1")
            return ResumoIndexacao(
                len(documento.paginas),
                sum(not pagina.texto for pagina in documento.paginas),
                len(trechos),
                alterado,
            )
        except ErroPersistencia:
            raise ErroDocumento(
                "Falha ao atualizar o índice; transação não confirmada."
            ) from None

    def buscar_trechos(
        self, termos: tuple[str, ...], limite: int = 5
    ) -> list[TrechoRecuperado]:
        if type(limite) is not int or not 1 <= limite <= 20:
            raise ErroValidacao("O limite deve estar entre 1 e 20 resultados.")
        if not termos:
            return []
        if len(termos) > 32 or any(not termo.isalnum() for termo in termos):
            raise ErroValidacao("Termos documentais inválidos.")
        # Não expor sintaxe MATCH ao chamador; exigir todos os termos significativos.
        consulta = " AND ".join(f'"{termo}"' for termo in termos)
        try:
            with self.banco.conectar() as conexao:
                verificar_identidade(conexao, inicializar=False)
                linhas = conexao.execute(
                    """SELECT t.identificador, t.documento_id, t.pagina, t.secao,
                              t.texto, t.ordem, t.inicio, t.fim, t.hash_conteudo,
                              d.hash_pdf, bm25(busca_trechos) AS pontuacao
                       FROM busca_trechos
                       JOIN trechos t ON t.numero = busca_trechos.rowid
                       JOIN documentos d ON d.identificador = t.documento_id
                       WHERE busca_trechos MATCH ?
                       ORDER BY pontuacao, t.pagina, t.ordem""",
                    (consulta,),
                )
                resultados: list[TrechoRecuperado] = []
                hashes: set[str] = set()
                for linha in linhas:
                    if linha["hash_conteudo"] in hashes:
                        continue
                    hashes.add(linha["hash_conteudo"])
                    campos = {
                        chave: linha[chave]
                        for chave in linha.keys()
                        if chave not in {"hash_pdf", "pontuacao"}
                    }
                    resultados.append(
                        TrechoRecuperado(
                            TrechoDocumento(**campos),
                            linha["hash_pdf"],
                            linha["pontuacao"],
                        )
                    )
                    if len(resultados) == limite:
                        break
                return resultados
        except ErroPersistencia:
            raise ErroDocumento(
                "Índice documental indisponível; execute a indexação local."
            ) from None
