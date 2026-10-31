class ErroDados(Exception):
    """Erro seguro para apresentação, sem valores dos registros ou caminhos."""


class ErroImportacao(ErroDados):
    """A importação não pode ser concluída com integridade."""


class ErroPersistencia(ErroDados):
    """Falha sanitizada de acesso à persistência local."""


class ErroValidacao(ErroDados):
    """Valor fora do contrato operacional."""
