"""Configurações obtidas do ambiente, sem leitura dos dados operacionais."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_PROJETO = Path(__file__).resolve().parents[3]


class ConfiguracaoAplicacao(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMPORIO_", frozen=True)

    ambiente: Literal["desenvolvimento", "teste", "producao"] = "desenvolvimento"
    origens_cors: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    nome_servico: str = "Emporio IA"
    versao: str = "0.1.0"
    diretorio_dados: Path = RAIZ_PROJETO / "data"
    caminho_banco: Path = RAIZ_PROJETO / ".local" / "emporio.sqlite3"
    caminho_pdf_politicas: Path = RAIZ_PROJETO / "data" / "políticas_da_loja.pdf"
    caminho_indice_politicas: Path = RAIZ_PROJETO / ".local" / "politicas.sqlite3"
    tamanho_maximo_trecho: int = Field(default=1200, ge=200, le=10000)

    @field_validator(
        "diretorio_dados",
        "caminho_banco",
        "caminho_pdf_politicas",
        "caminho_indice_politicas",
    )
    @classmethod
    def resolver_caminho(cls, caminho: Path) -> Path:
        if not caminho.is_absolute():
            caminho = RAIZ_PROJETO / caminho
        return caminho.resolve()

    @field_validator("caminho_banco", "caminho_indice_politicas")
    @classmethod
    def validar_banco(cls, caminho: Path) -> Path:
        if caminho.suffix.lower() not in {".sqlite", ".sqlite3", ".db"}:
            raise ValueError("O banco deve ter extensão .sqlite, .sqlite3 ou .db.")
        return caminho

    @model_validator(mode="after")
    def separar_bancos(self) -> "ConfiguracaoAplicacao":
        if self.caminho_banco == self.caminho_indice_politicas:
            raise ValueError(
                "Índice documental e banco operacional devem ser distintos."
            )
        if self.caminho_pdf_politicas.suffix.lower() != ".pdf":
            raise ValueError("O documento de políticas deve ser um PDF.")
        return self

    @field_validator("origens_cors")
    @classmethod
    def validar_origens(cls, origens: list[str]) -> list[str]:
        from urllib.parse import urlsplit

        for origem in origens:
            partes = urlsplit(origem)
            if (
                partes.scheme not in {"http", "https"}
                or not partes.hostname
                or partes.username
                or partes.password
                or partes.path
                or partes.query
                or partes.fragment
                or "*" in origem
            ):
                raise ValueError("CORS exige origens HTTP explícitas, sem caminho.")
        return origens


@lru_cache
def obter_configuracao() -> ConfiguracaoAplicacao:
    return ConfiguracaoAplicacao()
