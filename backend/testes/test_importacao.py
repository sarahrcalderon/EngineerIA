import csv
import hashlib
from pathlib import Path

import pytest
from conftest import DadosSinteticos, gravar_csvs

from emporio_ia.dominio.excecoes import ErroImportacao, ErroPersistencia
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.importacao import ImportadorDados


def test_importacao_valida(
    importador: ImportadorDados, diretorio_csv: Path, banco: BancoSQLite
) -> None:
    assert importador.importar(diretorio_csv) == {
        "categorias": 2,
        "clientes": 2,
        "produtos": 4,
        "pedidos": 2,
        "itens_pedido": 2,
        "promocoes": 2,
    }
    with banco.conectar() as conexao:
        assert conexao.execute("PRAGMA foreign_key_check").fetchall() == []
        assert (
            conexao.execute("SELECT typeof(preco_centavos) FROM produtos").fetchone()[0]
            == "integer"
        )
        assert conexao.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 2


@pytest.mark.parametrize("conteudo", ["", "category_id,name,description\n"])
def test_arquivo_vazio(
    importador: ImportadorDados, diretorio_csv: Path, conteudo: str
) -> None:
    (diretorio_csv / "categories.csv").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ErroImportacao):
        importador.importar(diretorio_csv)


@pytest.mark.parametrize(
    "cabecalho",
    [
        "id,name,description",
        "category_id,name,name",
        "category_id,name,description,extra",
    ],
)
def test_cabecalhos_incorretos(
    importador: ImportadorDados, diretorio_csv: Path, cabecalho: str
) -> None:
    (diretorio_csv / "categories.csv").write_text(
        cabecalho + "\n901,Teste,Sintético\n", encoding="utf-8"
    )
    with pytest.raises(ErroImportacao, match="cabeçalhos"):
        importador.importar(diretorio_csv)


@pytest.mark.parametrize(
    "registro", ["901,Sintético\n", "901,Sintético,Sintético,extra\n"]
)
def test_quantidade_campos_invalida(
    importador: ImportadorDados, diretorio_csv: Path, registro: str
) -> None:
    (diretorio_csv / "categories.csv").write_text(
        "category_id,name,description\n" + registro, encoding="utf-8"
    )
    with pytest.raises(ErroImportacao, match="quantidade de campos"):
        importador.importar(diretorio_csv)


@pytest.mark.parametrize(
    ("arquivo", "coluna", "valor"),
    [
        ("categories.csv", "name", " "),
        ("customers.csv", "email", ""),
        ("products.csv", "price_brl", "1.001"),
        ("products.csv", "stock_quantity", "-1"),
        ("products.csv", "created_at", "2025-02-30"),
        ("order_items.csv", "quantity", "0"),
        ("orders.csv", "total_brl", "-10"),
        ("promotions.csv", "is_active", "true"),
        ("promotions.csv", "discount_percent", "100.01"),
    ],
)
def test_rejeita_campos_invalidos(
    importador: ImportadorDados,
    diretorio_csv: Path,
    dados_sinteticos: DadosSinteticos,
    arquivo: str,
    coluna: str,
    valor: str,
) -> None:
    dados_sinteticos[arquivo][0][coluna] = valor
    gravar_csvs(diretorio_csv, dados_sinteticos)
    with pytest.raises(ErroImportacao, match=coluna):
        importador.importar(diretorio_csv)


@pytest.mark.parametrize(
    "arquivo",
    [
        "categories.csv",
        "customers.csv",
        "products.csv",
        "orders.csv",
        "order_items.csv",
        "promotions.csv",
    ],
)
def test_duplicatas(
    importador: ImportadorDados,
    diretorio_csv: Path,
    dados_sinteticos: DadosSinteticos,
    arquivo: str,
) -> None:
    dados_sinteticos[arquivo].append(dados_sinteticos[arquivo][0].copy())
    gravar_csvs(diretorio_csv, dados_sinteticos)
    with pytest.raises(ErroImportacao, match="duplicada"):
        importador.importar(diretorio_csv)


@pytest.mark.parametrize(
    ("arquivo", "coluna"),
    [
        ("products.csv", "category_id"),
        ("orders.csv", "customer_id"),
        ("order_items.csv", "order_id"),
        ("order_items.csv", "product_id"),
        ("promotions.csv", "product_id"),
    ],
)
def test_relacionamentos_invalidos(
    importador: ImportadorDados,
    diretorio_csv: Path,
    dados_sinteticos: DadosSinteticos,
    arquivo: str,
    coluna: str,
) -> None:
    dados_sinteticos[arquivo][0][coluna] = "999999"
    gravar_csvs(diretorio_csv, dados_sinteticos)
    with pytest.raises(ErroImportacao, match="integridade"):
        importador.importar(diretorio_csv)


def test_rollback_apos_escritas_parciais(
    banco_importado: BancoSQLite, diretorio_csv: Path, dados_sinteticos: DadosSinteticos
) -> None:
    dados_sinteticos["categories.csv"][0]["name"] = "Alteração não confirmada"
    dados_sinteticos["products.csv"][0]["price_brl"] = "999.99"
    dados_sinteticos["promotions.csv"][-1]["product_id"] = "999999"
    gravar_csvs(diretorio_csv, dados_sinteticos)
    with pytest.raises(ErroImportacao):
        ImportadorDados(banco_importado).importar(diretorio_csv)
    with banco_importado.conectar() as conexao:
        assert (
            conexao.execute(
                "SELECT nome FROM categorias WHERE identificador = 901"
            ).fetchone()[0]
            == "Cordas de teste"
        )
        assert (
            conexao.execute(
                "SELECT preco_centavos FROM produtos WHERE identificador = 201"
            ).fetchone()[0]
            == 1010
        )
        assert conexao.execute("SELECT COUNT(*) FROM promocoes").fetchone()[0] == 2


def test_reimportacao_idempotente_e_atualizacao(
    banco_importado: BancoSQLite, diretorio_csv: Path, dados_sinteticos: DadosSinteticos
) -> None:
    importador = ImportadorDados(banco_importado)
    primeiro = importador.importar(diretorio_csv)
    assert importador.importar(diretorio_csv) == primeiro
    dados_sinteticos["products.csv"][0]["price_brl"] = "11.11"
    dados_sinteticos["products.csv"] = dados_sinteticos["products.csv"][:-1]
    gravar_csvs(diretorio_csv, dados_sinteticos)
    assert importador.importar(diretorio_csv)["produtos"] == 3
    with banco_importado.conectar() as conexao:
        assert (
            conexao.execute(
                "SELECT preco_centavos FROM produtos WHERE identificador = 201"
            ).fetchone()[0]
            == 1111
        )
        assert (
            conexao.execute(
                "SELECT COUNT(*) FROM produtos WHERE identificador = 204"
            ).fetchone()[0]
            == 0
        )


def test_falha_inicial_desfaz_inclusive_esquema(
    importador: ImportadorDados,
    banco: BancoSQLite,
    diretorio_csv: Path,
    dados_sinteticos: DadosSinteticos,
) -> None:
    dados_sinteticos["promotions.csv"][0]["product_id"] = "999999"
    gravar_csvs(diretorio_csv, dados_sinteticos)
    with pytest.raises(ErroImportacao):
        importador.importar(diretorio_csv)
    with banco.conectar() as conexao:
        assert (
            conexao.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
            ).fetchone()[0]
            == 0
        )
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 0


def test_fk_ativa_e_leitura_nao_permite_escrita(banco_importado: BancoSQLite) -> None:
    for escrita in (False, True):
        with banco_importado.conectar(escrita=escrita) as conexao:
            assert conexao.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    with pytest.raises(ErroPersistencia):
        with banco_importado.conectar() as conexao:
            conexao.execute("DELETE FROM clientes")
    with pytest.raises(ErroPersistencia):
        with banco_importado.conectar(escrita=True) as conexao:
            conexao.execute("UPDATE produtos SET categoria_id = 999999")
    with pytest.raises(ErroPersistencia):
        with banco_importado.conectar(escrita=True) as conexao:
            conexao.execute("UPDATE produtos SET preco_centavos = -1")


def test_opcionais_ausentes_sao_null(banco_importado: BancoSQLite) -> None:
    with banco_importado.conectar() as conexao:
        linha = conexao.execute(
            "SELECT codigo_rastreamento, entrega_estimada, observacoes "
            "FROM pedidos WHERE identificador = 701"
        ).fetchone()
    assert tuple(linha) == (None, None, None)


def test_reconhece_prefixo_sem_modificar_fontes(
    importador: ImportadorDados, diretorio_csv: Path
) -> None:
    hashes = {}
    for caminho in list(diretorio_csv.iterdir()):
        destino = caminho.with_name(f"prefixo sintético - {caminho.name}")
        caminho.rename(destino)
        hashes[destino] = hashlib.sha256(destino.read_bytes()).hexdigest()
    importador.importar(diretorio_csv)
    assert {
        caminho: hashlib.sha256(caminho.read_bytes()).hexdigest()
        for caminho in diretorio_csv.iterdir()
    } == hashes


def test_nome_ambiguo_nao_escolhe_fonte(
    importador: ImportadorDados, diretorio_csv: Path
) -> None:
    (diretorio_csv / "outra fonte - categories.csv").write_text("", encoding="utf-8")
    with pytest.raises(ErroImportacao, match="ambíguo"):
        importador.importar(diretorio_csv)


def test_arquivo_ausente(importador: ImportadorDados, diretorio_csv: Path) -> None:
    (diretorio_csv / "categories.csv").rename(diretorio_csv / "indisponivel.txt")
    with pytest.raises(ErroImportacao, match="ausente"):
        importador.importar(diretorio_csv)


def test_ordem_cabecalhos_nao_e_obrigatoria(
    importador: ImportadorDados, diretorio_csv: Path
) -> None:
    caminho = diretorio_csv / "categories.csv"
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        registros = list(leitor)
        campos = list(reversed(leitor.fieldnames))
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(registros)
    assert importador.importar(diretorio_csv)["categorias"] == 2


def test_interrupcao_desfaz_todas_as_escritas(
    banco_importado: BancoSQLite, diretorio_csv: Path, monkeypatch
) -> None:
    from emporio_ia.infraestrutura import importacao

    leitura_original = importacao.ler_registros

    def interromper_promocoes(caminho, formato):
        for registro in leitura_original(caminho, formato):
            yield registro
            if formato.nome_conjunto == "promocoes":
                raise KeyboardInterrupt

    monkeypatch.setattr(importacao, "ler_registros", interromper_promocoes)
    with pytest.raises(KeyboardInterrupt):
        ImportadorDados(banco_importado).importar(diretorio_csv)
    with banco_importado.conectar() as conexao:
        assert conexao.execute("SELECT COUNT(*) FROM promocoes").fetchone()[0] == 2
        assert conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 4


def test_banco_desconhecido_nao_e_substituido(
    banco: BancoSQLite, importador: ImportadorDados, diretorio_csv: Path
) -> None:
    with banco.conectar(escrita=True) as conexao:
        conexao.execute("CREATE TABLE legado (valor TEXT)")
        conexao.execute("INSERT INTO legado VALUES (?)", ("preservar",))
    with pytest.raises(ErroImportacao, match="versão reconhecida"):
        importador.importar(diretorio_csv)
    with banco.conectar() as conexao:
        assert conexao.execute("SELECT valor FROM legado").fetchone()[0] == "preservar"


def test_versao_futura_nao_e_rebaixada(
    banco_importado: BancoSQLite, diretorio_csv: Path
) -> None:
    with banco_importado.conectar(escrita=True) as conexao:
        conexao.execute("PRAGMA user_version = 99")
    with pytest.raises(ErroImportacao, match="incompatível"):
        ImportadorDados(banco_importado).importar(diretorio_csv)
    with banco_importado.conectar() as conexao:
        assert conexao.execute("PRAGMA user_version").fetchone()[0] == 99
        assert conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 4
