import { ArrowDown, BookOpen } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import type { MensagemConversa } from '../tipos/atendimento';
import { BoasVindas } from './BoasVindas';
import { AvatarAssistente } from './AvatarAssistente';
import { ProdutosResposta } from './ProdutosResposta';
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
  if (mensagens.length === 0 && !aguardando && mostrarAtalho) {
    definirMostrarAtalho(false);
  }
  function rolar() {
    final.current?.scrollIntoView?.({
      behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
        ? 'instant'
        : 'smooth',
      block: 'end',
    });
  }
  useEffect(() => {
    if (mensagens.length === 0 && !aguardando) {
      proximoFinal.current = true;
    }
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
        {mensagens.map((mensagem, indice) => (
          <article
            className={`mensagem mensagem-${mensagem.papel}`}
            key={mensagem.identificador}
            aria-label={
              mensagem.papel === 'usuario'
                ? 'Sua mensagem'
                : 'Resposta do assistente'
            }
          >
            {mensagem.papel === 'assistente' &&
              (indice > 0 && mensagens[indice - 1].papel === 'assistente' ? (
                <span className="espaco-avatar" aria-hidden="true" />
              ) : (
                <AvatarAssistente />
              ))}
            <div className="conteudo-mensagem">
              <span className="autor-mensagem">
                {mensagem.papel === 'usuario' ? 'Você' : 'Empório da Música'}
              </span>
              {mensagem.horario && (
                <time className="horario-mensagem" dateTime={mensagem.horario}>
                  {new Intl.DateTimeFormat('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit',
                  }).format(new Date(mensagem.horario))}
                </time>
              )}
              {mensagem.produtos?.length ? (
                <>
                  {mensagem.introducao && <p>{mensagem.introducao}</p>}
                  <ProdutosResposta produtos={mensagem.produtos} />
                  {mensagem.complemento && (
                    <p className="complemento-resposta">
                      {mensagem.complemento}
                    </p>
                  )}
                </>
              ) : (
                <p>{mensagem.texto}</p>
              )}
              {mensagem.referencias.length > 0 && (
                <details className="fontes-consultadas">
                  <summary>Fontes consultadas</summary>
                  <ul className="referencias" aria-label="Fontes verificadas">
                    {mensagem.referencias.map((referencia, indice) => (
                      <li key={`${referencia.titulo}-${indice}`}>
                        <BookOpen size={15} aria-hidden="true" />
                        <span>{referencia.titulo}</span>
                      </li>
                    ))}
                  </ul>
                </details>
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
            <span>Estou consultando as informações para você…</span>
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
