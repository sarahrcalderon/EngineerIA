import {
  ArrowDown,
  BookOpen,
  Guitar,
  PackageSearch,
  ShieldCheck,
} from 'lucide-react';
import { DisponibilidadeApi } from './componentes/DisponibilidadeApi';

const funcionalidades = [
  {
    icone: Guitar,
    titulo: 'Encontre seu instrumento',
    descricao: 'Consulta de produtos, preços e disponibilidade.',
  },
  {
    icone: PackageSearch,
    titulo: 'Acompanhe seus pedidos',
    descricao: 'Informações de pedidos com controles de privacidade.',
  },
  {
    icone: BookOpen,
    titulo: 'Tire suas dúvidas',
    descricao: 'Respostas baseadas nas políticas da loja.',
  },
];

export default function App() {
  return (
    <>
      <a className="pular-conteudo" href="#conteudo">
        Pular para o conteúdo
      </a>
      <header className="cabecalho mx-auto flex max-w-6xl items-center justify-between gap-6 px-6">
        <a href="#" className="marca" aria-label="Empório da Música, início">
          <span className="logotipo-emporio" aria-hidden="true" />
          <span>
            EMPÓRIO<span className="marca-subtitulo">DA MÚSICA</span>
          </span>
        </a>
        <span className="localidade">Campo Grande · MS</span>
      </header>
      <main id="conteudo" className="mx-auto max-w-6xl px-6">
        <section className="apresentacao" aria-labelledby="titulo">
          <div>
            <p className="sobretitulo">MÚSICA CONECTA. A GENTE APROXIMA.</p>
            <h1 id="titulo">
              Empório <br />
              da <span>Música</span>
              <span className="ponto-titulo">.</span>
            </h1>
            <p className="subtitulo">
              Seu assistente virtual para encontrar instrumentos, consultar
              informações e tirar dúvidas.
            </p>
            <a className="link-funcionalidades" href="#possibilidades">
              Conheça o que vem por aí{' '}
              <ArrowDown size={18} aria-hidden="true" />
            </a>
          </div>
          <aside
            className="cartao-assistente"
            aria-labelledby="assistente-titulo"
          >
            <div className="icone-assistente">
              <span className="logotipo-emporio" aria-hidden="true" />
            </div>
            <p className="sobretitulo">UM NOVO TOM NO ATENDIMENTO</p>
            <h2 id="assistente-titulo">
              Boas conversas
              <br />
              começam por aqui.
            </h2>
            <p>
              Estamos preparando um assistente para ajudar você a encontrar as
              informações de que precisa.
            </p>
            <div className="nota-fase">Em desenvolvimento · Fase 1</div>
            <DisponibilidadeApi />
          </aside>
        </section>
        <section
          id="possibilidades"
          className="possibilidades"
          aria-labelledby="possibilidades-titulo"
        >
          <div className="secao-titulo">
            <h2 id="possibilidades-titulo">Mais perto da sua próxima nota.</h2>
            <span>NAS PRÓXIMAS ETAPAS</span>
          </div>
          <div className="grade-funcionalidades">
            {funcionalidades.map(
              ({ icone: Icone, titulo, descricao }, indice) => (
                <article className="funcionalidade" key={titulo}>
                  <div className="flex items-center justify-between">
                    <Icone size={26} aria-hidden="true" />
                    <span className="numero">0{indice + 1}</span>
                  </div>
                  <h3>{titulo}</h3>
                  <p>{descricao}</p>
                  <span className="em-breve">Em breve</span>
                </article>
              ),
            )}
          </div>
        </section>
        <p className="nota-privacidade">
          <ShieldCheck size={18} aria-hidden="true" />
          Nesta etapa, apenas a conexão com a API está disponível. Nenhum dado
          de cliente é consultado.
        </p>
      </main>
      <footer className="rodape mx-auto flex max-w-6xl flex-wrap justify-between gap-3 px-6">
        <span>Empório da Música</span>
        <span>engineerIA · Fundação do projeto</span>
      </footer>
    </>
  );
}
