"""Configurações obtidas do ambiente, sem leitura dos dados operacionais."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_PROJETO = Path(__file__).resolve().parents[3]


class ConfiguracaoAplicacao(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EMPORIO_", frozen=True, hide_input_in_errors=True
    )

    ambiente: Literal["desenvolvimento", "teste", "producao"] = "desenvolvimento"
    origens_cors: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    nome_servico: str = "Emporio IA"
    versao: str = "0.1.0"
    diretorio_dados: Path = RAIZ_PROJETO / "data"
    caminho_banco: Path = RAIZ_PROJETO / ".local" / "emporio.sqlite3"
    caminho_pdf_politicas: Path = RAIZ_PROJETO / "data" / "políticas_da_loja.pdf"
    caminho_indice_politicas: Path = RAIZ_PROJETO / ".local" / "politicas.sqlite3"
    tamanho_maximo_trecho: int = Field(default=1200, ge=200, le=10000)
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_modelo: str = "qwen3:4b"
    ollama_timeout: float = Field(default=60, gt=0, le=300)
    ollama_temperatura: float = Field(default=0, ge=0, le=1)
    ollama_tokens: int = Field(default=512, ge=64, le=4096)
    ollama_contexto_tokens: int = Field(default=8192, ge=2048, le=32768)
    agente_maximo_etapas: int = Field(default=4, ge=1, le=10)
    agente_maximo_chamadas: int = Field(default=6, ge=1, le=20)
    agente_maximo_resultados: int = Field(default=3, ge=1, le=10)
    agente_maximo_pergunta: int = Field(default=1000, ge=50, le=4000)
    agente_contexto_bytes: int = Field(default=6000, ge=1000, le=28000)
    agente_resposta_bytes: int = Field(default=65536, ge=1024, le=262144)
    agente_timeout_ferramenta: float = Field(default=10, gt=0, le=60)
    agente_timeout_total: float = Field(default=120, gt=0, le=600)
    caminho_publicacao: Path = RAIZ_PROJETO / ".local" / "publicacao.json"
    atendimento_requisicoes_minuto: int = Field(default=20, ge=1, le=120)
    atendimento_concorrencia: int = Field(default=1, ge=1, le=4)
    atendimento_corpo_bytes: int = Field(default=8192, ge=1024, le=32768)
    atendimento_leitura_timeout: float = Field(default=10, gt=0, le=30)
    atendimento_disponibilidade_timeout: float = Field(default=5, gt=0, le=15)

    @field_validator("ollama_url")
    @classmethod
    def validar_ollama_local(cls, valor: str) -> str:
        from urllib.parse import urlsplit

        partes = urlsplit(valor)
        if (
            partes.scheme != "http"
            or partes.hostname not in {"127.0.0.1", "::1", "localhost"}
            or partes.username
            or partes.password
            or partes.query
            or partes.fragment
            or partes.path not in {"", "/"}
        ):
            raise ValueError(
                "Ollama deve usar HTTP em loopback, sem credenciais ou caminho."
            )
        porta = partes.port or 11434
        host = "[::1]" if partes.hostname == "::1" else "127.0.0.1"
        return f"http://{host}:{porta}"

    @field_validator("ollama_modelo")
    @classmethod
    def validar_modelo_local(cls, valor: str) -> str:
        import re

        if (
            not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}", valor)
            or "cloud" in valor.lower()
        ):
            raise ValueError("Nome de modelo local inválido.")
        return valor

    @field_validator(
        "diretorio_dados",
        "caminho_banco",
        "caminho_pdf_politicas",
        "caminho_indice_politicas",
        "caminho_publicacao",
    )
    @classmethod
    def resolver_caminho(cls, caminho: Path) -> Path:
        if not caminho.is_absolute():
            caminho = RAIZ_PROJETO / caminho
        return caminho.resolve()

    @field_validator("caminho_publicacao")
    @classmethod
    def validar_local_publicacao(cls, caminho: Path) -> Path:
        if caminho.suffix.lower() != ".json" or (
            caminho.is_relative_to(RAIZ_PROJETO)
            and not caminho.is_relative_to(RAIZ_PROJETO / ".local")
        ):
            raise ValueError("A publicação deve usar JSON em armazenamento privado.")
        return caminho

    @field_validator("caminho_banco", "caminho_indice_politicas")
    @classmethod
    def validar_banco(cls, caminho: Path) -> Path:
        if caminho.suffix.lower() not in {".sqlite", ".sqlite3", ".db"}:
            raise ValueError("O banco deve ter extensão .sqlite, .sqlite3 ou .db.")
        return caminho

    @model_validator(mode="after")
    def separar_bancos(self) -> "ConfiguracaoAplicacao":
        if (
            self.agente_contexto_bytes + self.ollama_tokens + 1024
            > self.ollama_contexto_tokens
        ):
            raise ValueError(
                "Limite de contexto incompatível com o orçamento do modelo."
            )
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
