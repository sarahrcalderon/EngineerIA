from servidor_homologacao import criar_contexto_ficticio


def test_servidor_de_homologacao_isola_fontes_configuradas(tmp_path, monkeypatch):
    sentinela = tmp_path / "nao-utilizar.sqlite3"
    sentinela.write_bytes(b"arquivo-sentinela-sintetico")
    for variavel in ("EMPORIO_CAMINHO_BANCO", "EMPORIO_CAMINHO_INDICE_POLITICAS"):
        monkeypatch.setenv(variavel, str(sentinela))
    monkeypatch.setenv(
        "EMPORIO_CAMINHO_PUBLICACAO", str(tmp_path / "nao-autorizar.json")
    )
    base = tmp_path / "contexto-ficticio"
    configuracao = criar_contexto_ficticio(base)
    for caminho in (
        configuracao.caminho_banco,
        configuracao.caminho_indice_politicas,
        configuracao.caminho_publicacao,
    ):
        assert caminho.is_relative_to(base) and caminho.is_file()
    assert sentinela.read_bytes() == b"arquivo-sentinela-sintetico"
    assert not (tmp_path / "nao-autorizar.json").exists()
