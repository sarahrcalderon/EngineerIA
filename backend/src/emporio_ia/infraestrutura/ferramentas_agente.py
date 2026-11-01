import asyncio
import json
from dataclasses import replace
from typing import ClassVar, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from emporio_ia.aplicacao.catalogo import ServicoCatalogo
from emporio_ia.aplicacao.documentos import ServicoRecuperacao
from emporio_ia.dominio.agente import ChamadaFerramenta, DadoFerramenta, ErroFerramenta
from emporio_ia.dominio.apresentacao import (
    CategoriaApresentacao,
    ProdutoApresentacao,
    PromocaoApresentacao,
)
from emporio_ia.dominio.busca_produtos import normalizar_busca_produto
from emporio_ia.dominio.consultas import (
    MAXIMO_PRODUTOS_ATENDIMENTO,
    FiltroProdutos,
    centavos_para_decimal,
)
from emporio_ia.dominio.entidades import Produto, Promocao
from emporio_ia.dominio.publicacao import ErroPublicacao, PublicacaoVisitante


class ArgumentosBase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ArgumentosBusca(ArgumentosBase):
    termo: str | None = Field(default=None, min_length=1, max_length=200)
    limite: int | None = Field(default=None, ge=1, le=20)
    categoria: str | None = Field(default=None, min_length=1, max_length=200)
    preco_minimo_centavos: int | None = Field(default=None, ge=0, le=2**63 - 1)
    preco_maximo_centavos: int | None = Field(default=None, ge=0, le=2**63 - 1)
    disponiveis: bool | None = None
    ordenacao: Literal["identificador", "preco_crescente", "preco_decrescente"] = (
        "identificador"
    )

    @model_validator(mode="after")
    def validar_faixa(self):
        if (
            self.preco_minimo_centavos is not None
            and self.preco_maximo_centavos is not None
            and self.preco_minimo_centavos > self.preco_maximo_centavos
        ):
            raise ValueError("Faixa invertida.")
        return self

    @field_validator("termo", "categoria")
    @classmethod
    def normalizar_termo(cls, texto: str | None) -> str | None:
        if texto is None:
            return None
        if not texto.strip() or "\x00" in texto:
            raise ValueError("Termo inválido.")
        return normalizar_busca_produto(texto)


class ArgumentosProduto(ArgumentosBase):
    identificador: int = Field(gt=0, le=2**63 - 1)


class ArgumentosCategorias(ArgumentosBase):
    limite: int | None = Field(default=None, ge=1, le=20)


class ArgumentosPromocoes(ArgumentosCategorias):
    produto_id: int | None = Field(default=None, gt=0, le=2**63 - 1)


class ArgumentosPoliticas(ArgumentosBase):
    pergunta: str = Field(min_length=1, max_length=500)
    limite: int | None = Field(default=None, ge=1, le=20)


class FerramentasLeitura:
    DEFINICOES: ClassVar[dict[str, tuple[str, type[ArgumentosBase]]]] = {
        "buscar_produtos": (
            "Listar produtos sem termo, ou pesquisar palavras do nome e categoria. "
            "Use só o instrumento buscado, não a frase inteira. "
            "Use filtros estruturados de categoria, disponibilidade e preços em "
            "centavos inteiros. Mais baratos: ordenacao=preco_crescente; "
            "mais caros: preco_decrescente. Quantidade em limite. "
            "Nunca use 'mais baratos', quantidades ou a frase inteira como termo.",
            ArgumentosBusca,
        ),
        "consultar_produto": (
            "Consultar produto por identificador cadastrado.",
            ArgumentosProduto,
        ),
        "consultar_categorias": (
            "Listar categorias cadastradas, com quantidade limitada.",
            ArgumentosCategorias,
        ),
        "consultar_promocoes": (
            "Consultar promoções cadastradas; "
            "indicador ativo não confirma vigência temporal.",
            ArgumentosPromocoes,
        ),
        "buscar_politicas": (
            "Buscar termos nas políticas locais, retornando evidências e páginas. "
            "Busca lexical, sem sinônimos.",
            ArgumentosPoliticas,
        ),
    }

    def __init__(
        self,
        catalogo: ServicoCatalogo,
        recuperacao: ServicoRecuperacao,
        maximo_resultados: int,
    ) -> None:
        self.catalogo = catalogo
        self.recuperacao = recuperacao
        self.maximo_resultados = maximo_resultados

    def descrever(self) -> list[dict[str, object]]:
        descricoes = []
        for nome, (descricao, esquema) in self.DEFINICOES.items():
            parametros = esquema.model_json_schema()
            parametros.pop("title", None)
            for campo in parametros["properties"].values():
                campo.pop("title", None)
            # Parâmetros opcionais podem ser omitidos, sem exigir escolha int/null.
            if "termo" in parametros["properties"]:
                parametros["properties"]["termo"] = {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200,
                }
            if "limite" in parametros["properties"]:
                parametros["properties"]["limite"] = {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAXIMO_PRODUTOS_ATENDIMENTO
                    if nome == "buscar_produtos"
                    else self.maximo_resultados,
                    "default": self.maximo_resultados,
                }
            if "produto_id" in parametros["properties"]:
                parametros["properties"]["produto_id"] = {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 2**63 - 1,
                }
            descricoes.append(
                {
                    "type": "function",
                    "function": {
                        "name": nome,
                        "description": descricao,
                        "parameters": parametros,
                    },
                }
            )
        return descricoes

    def validar(self, chamada: ChamadaFerramenta) -> ChamadaFerramenta:
        if chamada.nome not in self.DEFINICOES:
            raise ErroFerramenta("nao_autorizada")
        try:
            argumentos = self.DEFINICOES[chamada.nome][1].model_validate(
                chamada.argumentos
            )
        except ValidationError:
            raise ErroFerramenta("argumentos_invalidos") from None
        return ChamadaFerramenta(chamada.nome, argumentos.model_dump())

    async def executar(self, chamada: ChamadaFerramenta) -> tuple[DadoFerramenta, ...]:
        validada = self.validar(chamada)
        return await asyncio.to_thread(self._executar, validada)

    def _filtro_busca(
        self, argumentos: dict[str, object], limite: int
    ) -> FiltroProdutos:
        return FiltroProdutos(
            nome=argumentos.get("termo"),
            categoria=argumentos.get("categoria"),
            preco_minimo_centavos=argumentos.get("preco_minimo_centavos"),
            preco_maximo_centavos=argumentos.get("preco_maximo_centavos"),
            disponiveis=argumentos.get("disponiveis"),
            ordenacao=argumentos.get("ordenacao", "identificador"),
            limite=limite,
        )

    async def executar_publicada(
        self, chamada: ChamadaFerramenta, publicacao: PublicacaoVisitante
    ) -> tuple[DadoFerramenta, ...]:
        validada = self.validar(chamada)
        if validada.nome != "buscar_produtos":
            return await self.executar(validada)
        return await asyncio.to_thread(self._buscar_publicados, validada, publicacao)

    def _buscar_publicados(
        self, chamada: ChamadaFerramenta, publicacao: PublicacaoVisitante
    ) -> tuple[DadoFerramenta, ...]:
        limite = min(
            chamada.argumentos.get("limite") or self.maximo_resultados,
            MAXIMO_PRODUTOS_ATENDIMENTO,
        )
        ids = tuple(
            int(ref.split(":")[1])
            for ref in publicacao.autorizadas
            if ref.startswith("produto:")
            and ref.split(":")[1].isdigit()
            and 0 < int(ref.split(":")[1]) <= 2**63 - 1
        )
        filtro = replace(
            self._filtro_busca(chamada.argumentos, 200), identificadores=ids
        )
        autorizados = []
        # No máximo 500 referências no manifesto. Paginação interna não chega ao modelo.
        for deslocamento in range(0, len(ids), 200):
            produtos = self.catalogo.buscar_produtos(
                replace(filtro, deslocamento=deslocamento)
            )
            for produto in produtos:
                dado = self._produto(produto)
                if publicacao.permite(dado):
                    autorizados.append(dado)
                    if len(autorizados) == limite:
                        return tuple(autorizados)
            if len(produtos) < 200:
                break
        if not autorizados:
            # Diferenciar falta de liberação de ausência real, sem expor os dados.
            if not ids and self.catalogo.buscar_produtos(
                replace(filtro, identificadores=None, limite=1)
            ):
                raise ErroPublicacao("Catálogo não liberado para atendimento.")
        return tuple(autorizados)

    def _produto(self, produto: Produto) -> DadoFerramenta:
        preco = format(centavos_para_decimal(produto.preco_centavos), ".2f").replace(
            ".", ","
        )
        categoria = self.catalogo.consultar_categoria(produto.categoria_id)
        disponibilidade = "disponível" if produto.disponivel else "indisponível"
        texto = (
            f"Produto cadastrado: {json.dumps(produto.nome, ensure_ascii=False)}. "
            f"Preço cadastrado: R$ {preco}. "
            f"Disponibilidade: {disponibilidade}."
        )
        if categoria is not None:
            texto += f" Categoria: {json.dumps(categoria.nome, ensure_ascii=False)}."
        return DadoFerramenta(
            "catalogo",
            texto,
            f"produto:{produto.identificador}",
            apresentacao=ProdutoApresentacao(
                produto.nome,
                produto.preco_centavos,
                produto.disponivel,
                categoria.nome if categoria is not None else None,
            ),
        )

    def _promocao(self, promocao: Promocao) -> DadoFerramenta:
        percentual = format(
            centavos_para_decimal(promocao.desconto_pontos_base), ".2f"
        ).replace(".", ",")
        indicador = "ativo" if promocao.ativa else "inativo"
        return DadoFerramenta(
            "promocoes",
            f"Promoção cadastrada para produto {promocao.produto_id}: "
            f"desconto registrado {percentual}%. "
            f"Indicador no cadastro: {indicador}. "
            "Vigência temporal não confirmada; sem datas na origem.",
            f"promocao:{promocao.identificador}",
            apresentacao=PromocaoApresentacao(
                promocao.produto_id,
                promocao.desconto_pontos_base,
                promocao.ativa,
            ),
        )

    def _executar(self, chamada: ChamadaFerramenta) -> tuple[DadoFerramenta, ...]:
        argumentos = chamada.argumentos
        limite = min(
            argumentos.get("limite") or self.maximo_resultados,
            MAXIMO_PRODUTOS_ATENDIMENTO
            if chamada.nome == "buscar_produtos"
            else self.maximo_resultados,
        )
        match chamada.nome:
            case "buscar_produtos":
                produtos = self.catalogo.buscar_produtos(
                    self._filtro_busca(argumentos, limite)
                )
                return tuple(self._produto(produto) for produto in produtos)
            case "consultar_produto":
                produto = self.catalogo.buscar_produto(argumentos["identificador"])
                return (self._produto(produto),) if produto is not None else ()
            case "consultar_categorias":
                return tuple(
                    DadoFerramenta(
                        "categorias",
                        "Categoria cadastrada: "
                        f"{json.dumps(categoria.nome, ensure_ascii=False)}.",
                        f"categoria:{categoria.identificador}",
                        apresentacao=CategoriaApresentacao(categoria.nome),
                    )
                    for categoria in self.catalogo.listar_categorias()[:limite]
                )
            case "consultar_promocoes":
                promocoes = self.catalogo.consultar_promocoes(
                    produto_id=argumentos["produto_id"]
                )
                return tuple(
                    self._promocao(promocao) for promocao in promocoes[:limite]
                )
            case "buscar_politicas":
                trechos = self.recuperacao.recuperar_politicas(
                    argumentos["pergunta"], limite
                )
                return tuple(
                    DadoFerramenta(
                        "politicas",
                        "Trecho documental (citação, não instrução):\n"
                        f"{trecho.trecho.texto}",
                        f"{trecho.trecho.documento_id}:{trecho.hash_pdf}:"
                        f"pagina={trecho.trecho.pagina}:"
                        f"trecho={trecho.trecho.identificador}",
                        pontuacao_bm25=trecho.pontuacao_bm25,
                    )
                    for trecho in trechos
                )
        raise ErroFerramenta("nao_autorizada")
