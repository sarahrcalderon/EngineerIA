import { ArrowDown, BookOpen } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import type { MensagemConversa } from '../tipos/atendimento';
import { BoasVindas } from './BoasVindas';
export function AreaMensagens({
  mensagens,
  aguardando,
  aoEscolher,
}: {
  mensagens: MensagemConversa[];
  aguardando: boolean;
  aoEscolher?: (pergunta: string) => void;
}) {
  const area = useRef<HTMLDivElement>(null);
  const final = useRef<HTMLDivElement>(null);
  const proximoFinal = useRef(true);
  const [mostrarAtalho, definirMostrarAtalho] = useState(false);
  function rolar() {
    final.current?.scrollIntoView?.({
      behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
        ? 'instant'
        : 'smooth',
      block: 'end',
    });
  }
  useEffect(() => {
    if (proximoFinal.current) rolar();
    else definirMostrarAtalho(true);
  }, [mensagens, aguardando]);
  return (
    <div
      className="regiao-mensagens"
      tabIndex={0}
      role="region"
      aria-label="Mensagens do atendimento"
      ref={area}
      onScroll={() => {
        const elemento = area.current;
        if (elemento) {
          proximoFinal.current =
            elemento.scrollHeight - elemento.scrollTop - elemento.clientHeight <
            100;
          if (proximoFinal.current) definirMostrarAtalho(false);
        }
      }}
    >
      <div
        className="lista-mensagens"
        role="log"
        aria-label="Histórico da conversa"
        aria-live="polite"
        aria-relevant="additions text"
      >
        <BoasVindas
          aoEscolher={mensagens.length === 0 ? aoEscolher : undefined}
        />
        {mensagens.map((mensagem) => (
          <article
            className={`mensagem mensagem-${mensagem.papel}`}
            key={mensagem.identificador}
            aria-label={
              mensagem.papel === 'usuario'
                ? 'Sua mensagem'
                : 'Resposta do assistente'
            }
          >
            {mensagem.papel === 'assistente' && (
              <div className="avatar-assistente">
                <span className="logotipo-emporio" aria-hidden="true" />
              </div>
            )}
            <div className="conteudo-mensagem">
              <span className="autor-mensagem">
                {mensagem.papel === 'usuario' ? 'Você' : 'Empório da Música'}
              </span>
              <p>{mensagem.texto}</p>
              {mensagem.referencias.length > 0 && (
                <ul className="referencias" aria-label="Fontes verificadas">
                  {mensagem.referencias.map((referencia, indice) => (
                    <li key={`${referencia.titulo}-${indice}`}>
                      <BookOpen size={15} aria-hidden="true" />
                      <span>Fonte: {referencia.titulo}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </article>
        ))}
        {aguardando && (
          <div className="processamento" role="status">
            <span className="bolinhas" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            <span>Consultando as fontes autorizadas…</span>
          </div>
        )}
        <div ref={final} />
      </div>
      {mostrarAtalho && (
        <button
          type="button"
          className="atalho-recente"
          onClick={() => {
            proximoFinal.current = true;
            definirMostrarAtalho(false);
            rolar();
          }}
        >
          <ArrowDown size={16} aria-hidden="true" />
          Ver mensagens recentes
        </button>
      )}
    </div>
  );
}
