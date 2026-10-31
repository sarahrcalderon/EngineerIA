import re
import unicodedata

from emporio_ia.dominio.excecoes import ErroValidacao

VERSAO_BUSCA = "lexical-plurais-v1"

TERMOS_COMUNS = frozenset(
    "a ao aos aquela aquele as ate com como da das de do dos e ela ele em entre "
    "era essa esse esta este eu ha isso isto ja lhe me meu minha na nao nas no nos "
    "o os ou para pela pelo por qual quais quando quanto que quem se sem seu sua "
    "sobre tem tenho um uma umas uns voce voces posso pode poderia gostaria saber "
    "funciona funciona informacao informacoes politica politicas loja sao ser sera "
    "eh so onde porque favor preciso gostaria".split()
)


def normalizar_plural(termo: str) -> str:
    if len(termo) > 4:
        for sufixo, substituto in (("oes", "ao"), ("aes", "ao"), ("ais", "al")):
            if termo.endswith(sufixo):
                return termo[: -len(sufixo)] + substituto
        if termo.endswith("s") and not termo.endswith(("ss", "us", "is")):
            return termo[:-1]
    return termo


def extrair_termos(texto: str) -> tuple[str, ...]:
    decomposto = unicodedata.normalize("NFKD", texto).casefold()
    normalizado = "".join(
        letra for letra in decomposto if not unicodedata.combining(letra)
    )
    termos = (
        normalizar_plural(termo)
        for termo in re.findall(r"[^\W_]+", normalizado)
        if termo not in TERMOS_COMUNS and (len(termo) >= 3 or termo.isdecimal())
    )
    return tuple(termos)


def preparar_pergunta(pergunta: str) -> tuple[str, ...]:
    if not isinstance(pergunta, str) or not pergunta.strip():
        raise ErroValidacao("A pergunta deve conter texto.")
    if len(pergunta) > 500 or "\x00" in pergunta:
        raise ErroValidacao("Pergunta inválida ou acima de 500 caracteres.")
    termos = tuple(dict.fromkeys(extrair_termos(pergunta)))
    if not any(any(letra.isalpha() for letra in termo) for termo in termos):
        return ()
    if len(termos) > 32:
        raise ErroValidacao("A pergunta excede 32 termos de busca.")
    return termos
