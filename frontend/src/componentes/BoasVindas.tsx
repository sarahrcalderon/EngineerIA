import { BookOpen, Guitar, Layers } from 'lucide-react';
import { AvatarAssistente } from './AvatarAssistente';

const sugestoes = [
  {
    icone: Layers,
    titulo: 'Explore as categorias',
    pergunta: 'Quais categorias estão cadastradas?',
  },
  {
    icone: Guitar,
    titulo: 'Encontre seu instrumento',
    pergunta: 'Quero consultar o preço de um instrumento.',
  },
  {
    icone: BookOpen,
    titulo: 'Conheça as políticas',
    pergunta: 'O que as políticas dizem sobre trocas?',
  },
];

export function BoasVindas({
  aoEscolher,
}: {
  aoEscolher?: (pergunta: string) => void;
}) {
  return (
    <div className="boas-vindas">
      <article
        className="mensagem mensagem-assistente"
        aria-label="Mensagem de boas-vindas"
      >
        <AvatarAssistente />
        <div className="conteudo-mensagem">
          <span className="autor-mensagem">Empório da Música</span>
          <p>
            Olá! Bem-vindo à Empório da Música. Como posso ajudar você hoje?
          </p>
          <p className="ajuda-inicial">
            Posso consultar instrumentos, categorias e políticas autorizadas da
            loja.
          </p>
        </div>
      </article>
      {aoEscolher && (
        <div className="sugestoes" aria-label="Sugestões de perguntas">
          {sugestoes.map(({ icone: Icone, titulo, pergunta }) => (
            <button
              key={titulo}
              type="button"
              onClick={() => aoEscolher(pergunta)}
            >
              <Icone size={16} aria-hidden="true" />
              {titulo}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
