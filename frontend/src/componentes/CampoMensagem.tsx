import { Send, Square } from 'lucide-react';
import {
  useImperativeHandle,
  useLayoutEffect,
  useRef,
  type RefObject,
} from 'react';
interface Propriedades {
  texto: string;
  aoDigitar: (texto: string) => void;
  aoEnviar: () => void;
  aoInterromper: () => void;
  aguardando: boolean;
  limite: number;
  referencia: RefObject<HTMLTextAreaElement | null>;
  erroConsulta?: boolean;
}
export function CampoMensagem({
  texto,
  aoDigitar,
  aoEnviar,
  aoInterromper,
  aguardando,
  limite,
  referencia,
  erroConsulta = false,
}: Propriedades) {
  const excessiva = texto.length > limite;
  const campoLocal = useRef<HTMLTextAreaElement>(null);
  useImperativeHandle(referencia, () => campoLocal.current!, []);
  useLayoutEffect(() => {
    const campo = campoLocal.current;
    if (!campo) return;
    campo.style.height = 'auto';
    campo.style.height = `${Math.min(campo.scrollHeight, 144)}px`;
  }, [texto]);
  return (
    <div className="rodape-conversa">
      <form
        className={`campo-mensagem ${excessiva ? 'campo-invalido' : ''}`}
        onSubmit={(evento) => {
          evento.preventDefault();
          if (texto.trim() && !excessiva && !aguardando) aoEnviar();
        }}
      >
        <label className="sr-only" htmlFor="mensagem">
          Sua pergunta
        </label>
        <textarea
          id="mensagem"
          ref={campoLocal}
          value={texto}
          onChange={(evento) => aoDigitar(evento.target.value)}
          placeholder="Digite sua mensagem…"
          rows={1}
          maxLength={limite}
          aria-invalid={excessiva}
          aria-describedby={`orientacao-mensagem limite-mensagem${erroConsulta ? ' erro-consulta' : ''}`}
          onKeyDown={(evento) => {
            if (
              evento.key === 'Enter' &&
              !evento.shiftKey &&
              !evento.nativeEvent.isComposing
            ) {
              evento.preventDefault();
              if (!aguardando && texto.trim() && !excessiva) aoEnviar();
            }
          }}
        />
        <div className="acoes-campo">
          <span id="limite-mensagem" className={excessiva ? 'texto-erro' : ''}>
            {excessiva
              ? `Use até ${limite} caracteres.`
              : `${texto.length}/${limite}`}
          </span>
          {aguardando ? (
            <button
              className="botao-enviar"
              type="button"
              aria-label="Interromper consulta"
              onClick={aoInterromper}
            >
              <Square size={18} aria-hidden="true" />
            </button>
          ) : (
            <button
              className="botao-enviar"
              type="submit"
              aria-label="Enviar pergunta"
              disabled={!texto.trim() || excessiva}
            >
              <Send size={20} aria-hidden="true" />
              <span>Enviar</span>
            </button>
          )}
        </div>
      </form>
      <p id="orientacao-mensagem">
        Enter para enviar · Shift + Enter para uma nova linha
      </p>
      <p className="limite-contexto">
        Cada pergunta é independente. As mensagens ficam apenas nesta aba.
      </p>
    </div>
  );
}
