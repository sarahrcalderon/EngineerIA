import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from emporio_ia.aplicacao.documentos import IndexadorPoliticas, ServicoRecuperacao
from emporio_ia.configuracao import RAIZ_PROJETO, ConfiguracaoAplicacao
from emporio_ia.dominio.documentos import ErroDocumento
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos
from emporio_ia.principal import criar_aplicacao


def executar_cli(
    pdf: Path, indice: Path, terminal: Path
) -> subprocess.CompletedProcess[str]:
    ambiente = os.environ.copy()
    ambiente["PYTHONPATH"] = str(RAIZ_PROJETO / "backend" / "src")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "emporio_ia.indexar_politicas",
            "--pdf",
            str(pdf),
            "--indice",
            str(indice),
        ],
        cwd=terminal,
        env=ambiente,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_so_imprime_resumo_fora_da_raiz(
    pdf_sintetico: Path, tmp_path: Path
) -> None:
    destino = tmp_path / "indice-cli.sqlite3"
    resultado = executar_cli(pdf_sintetico, destino, tmp_path)
    assert resultado.returncode == 0
    assert resultado.stderr == ""
    resumo = json.loads(resultado.stdout)
    assert resumo["paginas"] == 3
    assert resumo["trechos"] > 0
    assert resumo["alterado"] is True
    assert "17 dias" not in resultado.stdout
    assert str(tmp_path) not in resultado.stdout
    assert (
        json.loads(executar_cli(pdf_sintetico, destino, tmp_path).stdout)["alterado"]
        is False
    )


def test_cli_erro_sem_conteudo_ou_traceback(tmp_path: Path) -> None:
    caminho = tmp_path / "corrompido.pdf"
    caminho.write_bytes(b"%PDF-1.7\nconteudo-confidencial-sintetico")
    resultado = executar_cli(caminho, tmp_path / "indice.sqlite3", tmp_path)
    assert resultado.returncode == 1
    assert resultado.stdout == ""
    assert "conteudo-confidencial" not in resultado.stderr
    assert "Traceback" not in resultado.stderr
    assert str(tmp_path) not in resultado.stderr


def test_extracao_indexacao_busca_sem_logs(
    indexador: IndexadorPoliticas,
    indice: RepositorioTrechos,
    pdf_sintetico: Path,
    caplog,
    capsys,
) -> None:
    indexador.indexar(pdf_sintetico)
    resultado = ServicoRecuperacao(indice).recuperar_politicas("prazo troca")
    assert resultado
    assert "17 dias" not in repr(resultado)
    assert "Trocas" not in repr(resultado)
    assert caplog.text == ""
    capturado = capsys.readouterr()
    assert capturado.out == capturado.err == ""


def test_indice_ausente_nao_e_criado_na_busca(tmp_path: Path) -> None:
    caminho = tmp_path / "ausente.sqlite3"
    servico = ServicoRecuperacao(RepositorioTrechos(BancoSQLite(caminho)))
    with pytest.raises(ErroDocumento, match="indisponível"):
        servico.recuperar_politicas("prazo troca")
    assert not caminho.exists()


def test_api_nao_expoe_documentos_ou_indice() -> None:
    with TestClient(criar_aplicacao()) as cliente:
        assert set(cliente.get("/openapi.json").json()["paths"]) == {
            "/api/saude",
            "/api/atendimento/mensagens",
            "/api/atendimento/disponibilidade",
        }
        for caminho in (
            "/api/politicas",
            "/api/documentos",
            "/api/trechos",
            "/data/politicas.pdf",
            "/.local/politicas.sqlite3",
        ):
            assert cliente.get(caminho).status_code == 404


def test_fontes_e_indice_sao_ignorados() -> None:
    if not shutil.which("git") or not (RAIZ_PROJETO / ".git").exists():
        pytest.skip("Verificação de Git exige checkout e executável Git.")
    resultado = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={RAIZ_PROJETO.as_posix()}",
            "check-ignore",
            "data/politicas.pdf",
            ".local/politicas.sqlite3",
            ".local/politicas.sqlite3-journal",
        ],
        cwd=RAIZ_PROJETO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado.returncode == 0
    assert len(resultado.stdout.splitlines()) == 3


def test_indice_operacional_preservado_apos_cli(
    banco_importado, pdf_sintetico: Path, tmp_path: Path
) -> None:
    antes = hashlib.sha256(banco_importado.caminho.read_bytes()).hexdigest()
    resultado = executar_cli(pdf_sintetico, banco_importado.caminho, tmp_path)
    assert resultado.returncode == 1
    assert hashlib.sha256(banco_importado.caminho.read_bytes()).hexdigest() == antes


def test_configuracao_documental_independe_do_terminal(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    configuracao = ConfiguracaoAplicacao()
    assert (
        configuracao.caminho_pdf_politicas
        == RAIZ_PROJETO / "data" / "políticas_da_loja.pdf"
    )
    assert (
        configuracao.caminho_indice_politicas
        == RAIZ_PROJETO / ".local" / "politicas.sqlite3"
    )


def test_cli_configuracao_invalida_nao_expoe_ambiente(
    pdf_sintetico: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("EMPORIO_ORIGENS_CORS", "valor-privado-sintetico")
    resultado = executar_cli(pdf_sintetico, tmp_path / "indice.sqlite3", tmp_path)
    assert resultado.returncode == 1
    assert "Configuração documental inválida" in resultado.stderr
    assert "valor-privado" not in resultado.stderr
    assert "Traceback" not in resultado.stderr
