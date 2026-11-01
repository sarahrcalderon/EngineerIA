import { useEffect, useRef, useState } from 'react';
import { enviarPergunta, mensagemErro } from '../servicos/atendimento';
import type { MensagemConversa } from '../tipos/atendimento';

export function useConversa() {
  const [mensagens, definirMensagens] = useState<MensagemConversa[]>([]);
  const [aguardando, definirAguardando] = useState(false);
  const [erro, definirErro] = useState<{
    texto: string;
    pergunta: string;
  } | null>(null);
  const controle = useRef<AbortController | null>(null);
  const ocupado = useRef(false);
  const sequencia = useRef(0);
  const identificador = useRef(0);
  useEffect(
    () => () => {
      sequencia.current += 1;
      controle.current?.abort();
    },
    [],
  );

  async function enviar(pergunta: string, repetir = false) {
    if (ocupado.current || !pergunta.trim() || pergunta.length > 1000) return;
    ocupado.current = true;
    const tentativa = ++sequencia.current;
    const cancelamento = new AbortController();
    controle.current = cancelamento;
    definirAguardando(true);
    definirErro(null);
    if (!repetir) {
      const nova: MensagemConversa = {
        identificador: ++identificador.current,
        papel: 'usuario',
        texto: pergunta.trim(),
        referencias: [],
        horario: new Date().toISOString(),
      };
      definirMensagens((atuais) => [...atuais.slice(-48), nova]);
    }
    try {
      const resposta = await enviarPergunta(
        pergunta.trim(),
        cancelamento.signal,
      );
      if (tentativa !== sequencia.current || cancelamento.signal.aborted)
        return;
      const nova: MensagemConversa = {
        identificador: ++identificador.current,
        papel: 'assistente',
        texto: resposta.resposta,
        referencias: resposta.referencias,
        produtos: resposta.produtos,
        complemento: resposta.complemento,
        horario: new Date().toISOString(),
      };
      definirMensagens((atuais) => [...atuais, nova]);
    } catch (falha) {
      if (tentativa !== sequencia.current) return;
      definirErro({
        texto: cancelamento.signal.aborted
          ? 'Consulta interrompida. Você pode tentar novamente.'
          : mensagemErro(falha),
        pergunta,
      });
    } finally {
      if (tentativa === sequencia.current) {
        ocupado.current = false;
        definirAguardando(false);
        controle.current = null;
      }
    }
  }

  function novaConversa() {
    sequencia.current += 1;
    controle.current?.abort();
    controle.current = null;
    ocupado.current = false;
    definirMensagens([]);
    definirErro(null);
    definirAguardando(false);
  }
  return {
    mensagens,
    aguardando,
    erro,
    enviar,
    novaConversa,
    interromper: () => controle.current?.abort(),
  };
}
