import { useRef, useState } from 'react';
import { AreaMensagens } from './componentes/AreaMensagens';
import { CabecalhoAtendimento } from './componentes/CabecalhoAtendimento';
import { CampoMensagem } from './componentes/CampoMensagem';
import { useConversa } from './hooks/useConversa';
import { useAlturaVisivel } from './hooks/useAlturaVisivel';

export default function App() {
  const conversa = useConversa();
  useAlturaVisivel();
  const [texto, definirTexto] = useState('');
  const [limite, definirLimite] = useState(1000);
  const campo = useRef<HTMLTextAreaElement>(null);
  function novaConversa() {
    conversa.novaConversa();
    definirTexto('');
    campo.current?.focus();
  }
  function enviar() {
    if (texto.length > limite) return;
    void conversa.enviar(texto);
    definirTexto('');
    campo.current?.focus();
  }
  return (
    <div className="aplicacao-atendimento">
      <a className="pular-conteudo" href="#conteudo">
        Pular para o conteúdo
      </a>
      <div className="identidade-loja">
        <a href="#conteudo" className="marca">
          <span className="logotipo-emporio" aria-hidden="true" />
          <span>Empório da Música</span>
        </a>
        <span className="assinatura-loja">Em sintonia com você.</span>
      </div>
      <main id="conteudo" className="pagina-atendimento" tabIndex={-1}>
        <CabecalhoAtendimento
          aoNovaConversa={novaConversa}
          aoObterLimite={definirLimite}
        />
        <div className="corpo-atendimento">
          <AreaMensagens
            mensagens={conversa.mensagens}
            aguardando={conversa.aguardando}
            aoEscolher={(pergunta) => {
              definirTexto(pergunta);
              campo.current?.focus();
            }}
          />
        </div>
        {conversa.erro && (
          <div id="erro-consulta" className="erro-consulta" role="alert">
            <p>{conversa.erro.texto}</p>
            <button
              type="button"
              disabled={conversa.aguardando}
              onClick={() => {
                if (conversa.erro)
                  void conversa.enviar(conversa.erro.pergunta, true);
                campo.current?.focus();
              }}
            >
              Tentar novamente
            </button>
          </div>
        )}
        <CampoMensagem
          texto={texto}
          aoDigitar={definirTexto}
          aoEnviar={enviar}
          aoInterromper={() => {
            conversa.interromper();
            campo.current?.focus();
          }}
          aguardando={conversa.aguardando}
          limite={limite}
          referencia={campo}
          erroConsulta={Boolean(conversa.erro)}
        />
      </main>
    </div>
  );
}
