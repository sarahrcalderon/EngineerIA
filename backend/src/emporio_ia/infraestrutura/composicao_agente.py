from emporio_ia.aplicacao.catalogo import ServicoCatalogo
from emporio_ia.aplicacao.documentos import ServicoRecuperacao
from emporio_ia.configuracao import ConfiguracaoAplicacao
from emporio_ia.infraestrutura.banco import BancoSQLite
from emporio_ia.infraestrutura.documentos.repositorio import RepositorioTrechos
from emporio_ia.infraestrutura.ferramentas_agente import FerramentasLeitura
from emporio_ia.infraestrutura.repositorios.catalogo import (
    RepositorioCategorias,
    RepositorioPromocoes,
)
from emporio_ia.infraestrutura.repositorios.produtos import RepositorioProdutos


def criar_ferramentas(configuracao: ConfiguracaoAplicacao) -> FerramentasLeitura:
    banco = BancoSQLite(configuracao.caminho_banco)
    catalogo = ServicoCatalogo(
        RepositorioProdutos(banco),
        RepositorioCategorias(banco),
        RepositorioPromocoes(banco),
    )
    recuperacao = ServicoRecuperacao(
        RepositorioTrechos(BancoSQLite(configuracao.caminho_indice_politicas))
    )
    return FerramentasLeitura(
        catalogo, recuperacao, configuracao.agente_maximo_resultados
    )
