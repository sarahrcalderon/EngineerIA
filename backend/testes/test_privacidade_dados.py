import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest
from conftest import DadosSinteticos, gravar_csvs
from fastapi.testclient import TestClient

from emporio_ia.aplicacao.pedidos import ServicoPedidos
from emporio_ia.configuracao import RAIZ_PROJETO, ConfiguracaoAplicacao
from emporio_ia.dominio.entidades import Cliente
from emporio_ia.dominio.excecoes import ErroImportacao
from emporio_ia.infraestrutura.importacao import ImportadorDados
from emporio_ia.principal import criar_aplicacao


def test_importador_nao_registra_dados_pessoais(
    importador: ImportadorDados, diretorio_csv: Path, caplog, capsys
) -> None:
    importador.importar(diretorio_csv)
    assert caplog.text == ""
    capturado = capsys.readouterr()
    assert capturado.out == ""
    assert capturado.err == ""


def test_erros_nao_expoem_valores_ou_caminhos(
    importador: ImportadorDados, diretorio_csv: Path, dados_sinteticos: DadosSinteticos
) -> None:
    sentinela = "pessoa-secreta@example.invalid"
    dados_sinteticos["customers.csv"][0]["customer_id"] = sentinela
    gravar_csvs(diretorio_csv, dados_sinteticos)
    with pytest.raises(ErroImportacao) as erro:
        importador.importar(diretorio_csv)
    assert sentinela not in str(erro.value)
    assert str(diretorio_csv) not in str(erro.value)
    assert "customer_id" in str(erro.value)


def test_consulta_pedido_minimiza_dados(pedidos: ServicoPedidos) -> None:
    consulta = pedidos.consultar_pedido(702, cliente_id=802)
    campos = asdict(consulta)
    assert set(campos) == {
        "identificador",
        "estado",
        "data_pedido",
        "total_centavos",
        "codigo_rastreamento",
        "entrega_estimada",
        "itens",
    }
    assert "RASTREAMENTO-SINTETICO" not in repr(consulta)
    cliente = Cliente(
        801,
        "Pessoa Sintética",
        "telefone sintético",
        "alfa@example.invalid",
        "Cidade fictícia",
    )
    assert "alfa@example.invalid" not in repr(cliente)


def test_api_continua_sem_rotas_operacionais(
    diretorio_csv: Path, banco_importado
) -> None:
    configuracao = ConfiguracaoAplicacao(
        diretorio_dados=diretorio_csv, caminho_banco=banco_importado.caminho
    )
    with TestClient(criar_aplicacao(configuracao)) as cliente:
        assert set(cliente.get("/openapi.json").json()["paths"]) == {"/api/saude"}
        for caminho in (
            "/api/clientes",
            "/api/pedidos/701",
            "/api/produtos",
            "/api/promocoes",
            "/data/customers.csv",
        ):
            resposta = cliente.get(caminho)
            assert resposta.status_code == 404
            assert resposta.json() == {"detalhe": "Recurso não encontrado."}
        assert cliente.get("/api/saude").status_code == 200


def test_configuracao_independe_do_diretorio_atual(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    configuracao = ConfiguracaoAplicacao()
    assert configuracao.diretorio_dados == RAIZ_PROJETO / "data"
    assert configuracao.caminho_banco == RAIZ_PROJETO / ".local" / "emporio.sqlite3"
    relativa = ConfiguracaoAplicacao(
        diretorio_dados=Path("dados-alternativos"),
        caminho_banco=Path(".local/alternativo.db"),
    )
    assert relativa.caminho_banco == RAIZ_PROJETO / ".local" / "alternativo.db"


def executar_cli(
    diretorio_csv: Path, destino: Path, terminal: Path
) -> subprocess.CompletedProcess[str]:
    ambiente = os.environ.copy()
    ambiente["PYTHONPATH"] = str(RAIZ_PROJETO / "backend" / "src")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "emporio_ia.importar",
            "--diretorio-dados",
            str(diretorio_csv),
            "--banco",
            str(destino),
        ],
        cwd=terminal,
        env=ambiente,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_em_outro_diretorio_so_emite_resumo(
    diretorio_csv: Path, tmp_path: Path
) -> None:
    resultado = executar_cli(diretorio_csv, tmp_path / "cli.sqlite3", tmp_path)
    assert resultado.returncode == 0
    assert resultado.stderr == ""
    assert json.loads(resultado.stdout)["registros"]["produtos"] == 4
    assert "example.invalid" not in resultado.stdout
    assert str(tmp_path) not in resultado.stdout


def test_cli_falha_sem_traceback_ou_dados(
    diretorio_csv: Path, tmp_path: Path, dados_sinteticos: DadosSinteticos
) -> None:
    dados_sinteticos["products.csv"][0]["price_brl"] = "segredo-sintetico"
    gravar_csvs(diretorio_csv, dados_sinteticos)
    resultado = executar_cli(diretorio_csv, tmp_path / "falha.sqlite3", tmp_path)
    assert resultado.returncode == 1
    assert resultado.stdout == ""
    assert "segredo-sintetico" not in resultado.stderr
    assert "Traceback" not in resultado.stderr
    assert str(tmp_path) not in resultado.stderr
