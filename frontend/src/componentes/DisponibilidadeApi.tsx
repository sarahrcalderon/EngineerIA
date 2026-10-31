import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { consultarSaude } from '../servicos/saude';

type EstadoConexao = 'verificando' | 'disponivel' | 'indisponivel';

const textos: Record<EstadoConexao, string> = {
  verificando: 'Verificando conexão',
  disponivel: 'API disponível',
  indisponivel: 'API indisponível',
};

export function DisponibilidadeApi() {
  const [estado, definirEstado] = useState<EstadoConexao>('verificando');
  const [tentativa, definirTentativa] = useState(0);

  useEffect(() => {
    const controle = new AbortController();

    consultarSaude(controle.signal)
      .then(() => {
        if (!controle.signal.aborted) definirEstado('disponivel');
      })
      .catch(() => {
        if (!controle.signal.aborted) definirEstado('indisponivel');
      });

    return () => controle.abort();
  }, [tentativa]);

  function verificarNovamente() {
    definirEstado('verificando');
    definirTentativa((valor) => valor + 1);
  }

  return (
    <div className="conexao">
      <span
        role="status"
        aria-live="polite"
        className={`estado estado-${estado}`}
      >
        <span className="ponto" aria-hidden="true" />
        {textos[estado]}
      </span>
      {estado === 'indisponivel' && (
        <button
          type="button"
          onClick={verificarNovamente}
          className="botao-repetir"
        >
          <RefreshCw size={16} aria-hidden="true" />
          Tentar novamente
        </button>
      )}
    </div>
  );
}
