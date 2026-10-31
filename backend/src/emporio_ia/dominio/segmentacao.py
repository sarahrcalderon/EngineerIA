import hashlib
import json
import re
import unicodedata

from emporio_ia.dominio.documentos import (
    DocumentoPoliticas,
    ErroDocumento,
    TrechoDocumento,
)

VERSAO_SEGMENTACAO = "paragrafos-frases-v1"


def normalizar_texto_documental(texto: str) -> str:
    linhas = [
        re.sub(r"[^\S\n]+", " ", linha).strip()
        for linha in unicodedata.normalize("NFC", texto).splitlines()
    ]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


def identificar_titulo(linha: str) -> bool:
    if not 3 <= len(linha) <= 100 or linha.endswith((".", "?", "!", ";")):
        return False
    numerado = re.match(r"^\d+(?:\.\d+)*[.)]\s+[^\W\d_]", linha)
    return bool(
        numerado or (linha.isupper() and any(letra.isalpha() for letra in linha))
    )


def localizar_unidades(texto: str, maximo: int) -> list[tuple[int, int, str | None]]:
    """Manter offsets no texto normalizado; títulos isolam os grupos seguintes."""
    blocos: list[tuple[int, int, str | None]] = []
    for paragrafo in re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", texto):
        inicio = paragrafo.start()
        inicio_bloco: int | None = None
        fim_bloco = inicio
        for linha in paragrafo.group().splitlines(keepends=True):
            conteudo = linha.rstrip("\n")
            fim = inicio + len(conteudo)
            if identificar_titulo(conteudo):
                if inicio_bloco is not None:
                    blocos.append((inicio_bloco, fim_bloco, None))
                    inicio_bloco = None
                blocos.append((inicio, fim, conteudo))
            else:
                if inicio_bloco is None:
                    inicio_bloco = inicio
                fim_bloco = fim
            inicio += len(linha)
        if inicio_bloco is not None:
            blocos.append((inicio_bloco, fim_bloco, None))
    unidades: list[tuple[int, int, str | None]] = []
    for inicio, fim, titulo in blocos:
        if fim - inicio <= maximo:
            unidades.append((inicio, fim, titulo))
            continue
        cursor = inicio
        # Não separar pontos decimais; a quebra exige espaço após pontuação.
        for separador in re.finditer(r"(?<=[.!?])\s+(?=\w)", texto[inicio:fim]):
            unidades.append((cursor, inicio + separador.start(), None))
            cursor = inicio + separador.end()
        unidades.append((cursor, fim, None))
    if any(fim - inicio > maximo for inicio, fim, _ in unidades):
        raise ErroDocumento(
            "Unidade textual excede o limite; aumente o tamanho máximo do trecho."
        )
    return unidades


def criar_trecho(
    documento_id: str,
    pagina: int,
    texto: str,
    ordem: int,
    inicio: int,
    fim: int,
    secao: str | None,
) -> TrechoDocumento:
    conteudo = texto[inicio:fim]
    resumo = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
    origem = json.dumps([documento_id, pagina, inicio, fim, resumo], ensure_ascii=False)
    identificador = hashlib.sha256(origem.encode("utf-8")).hexdigest()
    return TrechoDocumento(
        identificador, documento_id, pagina, secao, conteudo, ordem, inicio, fim, resumo
    )


def dividir_em_trechos(
    documento: DocumentoPoliticas, tamanho_maximo: int = 1200
) -> tuple[TrechoDocumento, ...]:
    if type(tamanho_maximo) is not int or not 200 <= tamanho_maximo <= 10000:
        raise ErroDocumento(
            "Tamanho de trecho deve estar entre 200 e 10000 caracteres."
        )
    trechos: list[TrechoDocumento] = []
    secao: str | None = None
    for pagina in documento.paginas:
        inicio_grupo: int | None = None
        fim_grupo = 0
        for inicio, fim, titulo in localizar_unidades(pagina.texto, tamanho_maximo):
            # Respeitar parágrafos em vez de misturar regras independentes.
            novo_paragrafo = "\n\n" in pagina.texto[fim_grupo:inicio]
            if inicio_grupo is not None and (
                titulo is not None
                or (novo_paragrafo and pagina.texto[inicio_grupo:fim_grupo] != secao)
                or fim - inicio_grupo > tamanho_maximo
            ):
                trechos.append(
                    criar_trecho(
                        documento.identificador,
                        pagina.numero,
                        pagina.texto,
                        len(trechos),
                        inicio_grupo,
                        fim_grupo,
                        secao,
                    )
                )
                inicio_grupo = None
            if titulo is not None:
                secao = titulo
            if inicio_grupo is None:
                inicio_grupo = inicio
            fim_grupo = fim
        if inicio_grupo is not None:
            trechos.append(
                criar_trecho(
                    documento.identificador,
                    pagina.numero,
                    pagina.texto,
                    len(trechos),
                    inicio_grupo,
                    fim_grupo,
                    secao,
                )
            )
    if not trechos:
        raise ErroDocumento("Documento sem texto extraível; OCR não está habilitado.")
    return tuple(trechos)
