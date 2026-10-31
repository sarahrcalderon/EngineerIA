import { Moon, Plus, RefreshCw, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';
import { consultarDisponibilidade } from '../servicos/atendimento';
import { useTema } from '../hooks/useTema';
import { DisponibilidadeApi } from './DisponibilidadeApi';

interface Propriedades {
  aoNovaConversa: () => void;
  aoObterLimite: (limite: number) => void;
}

export function CabecalhoAtendimento({
  aoNovaConversa,
  aoObterLimite,
}: Propriedades) {
  const { tema, alternarTema } = useTema();
  const [modelo, definirModelo] = useState<
    'verificando' | 'acessivel' | 'indisponivel' | 'nao_verificado'
  >('verificando');
  const [tentativa, definirTentativa] = useState(0);
  useEffect(() => {
    const controle = new AbortController();
    consultarDisponibilidade(controle.signal)
      .then((resposta) => {
        if (!controle.signal.aborted) {
          definirModelo(resposta.modelo);
          aoObterLimite(resposta.limite_mensagem);
        }
      })
      .catch(() => {
        if (!controle.signal.aborted) definirModelo('nao_verificado');
      });
    return () => controle.abort();
  }, [tentativa, aoObterLimite]);
  return (
    <header className="cabecalho-atendimento">
      <div className="titulo-cabecalho">
        <span className="avatar-cabecalho" aria-hidden="true">
          <span className="logotipo-emporio" />
        </span>
        <div>
          <h1>Atendimento do Empório</h1>
          <p>Empório da Música · Em validação</p>
        </div>
      </div>
      <div className="acoes-cabecalho">
        <div className="conexoes">
          <DisponibilidadeApi />
          <span className={`estado estado-${modelo}`} role="status">
            <span className="ponto" aria-hidden="true" />
            {modelo === 'verificando'
              ? 'Verificando atendimento'
              : modelo === 'acessivel'
                ? 'Conexão local verificada'
                : modelo === 'indisponivel'
                  ? 'Atendimento indisponível'
                  : 'Atendimento não verificado'}
          </span>
        </div>
        <button
          className="botao-icone atualizar-conexao"
          type="button"
          title="Verificar atendimento"
          aria-label="Verificar atendimento novamente"
          onClick={() => {
            definirModelo('verificando');
            definirTentativa((valor) => valor + 1);
          }}
        >
          <RefreshCw size={18} aria-hidden="true" />
        </button>
        <button
          className="botao-icone"
          type="button"
          aria-label={`Ativar tema ${tema === 'claro' ? 'escuro' : 'claro'}`}
          onClick={alternarTema}
        >
          {tema === 'claro' ? (
            <Moon size={20} aria-hidden="true" />
          ) : (
            <Sun size={20} aria-hidden="true" />
          )}
        </button>
        <button
          className="botao-nova"
          type="button"
          aria-label="Nova conversa"
          onClick={aoNovaConversa}
        >
          <Plus size={22} aria-hidden="true" />
          <span>Nova conversa</span>
        </button>
      </div>
    </header>
  );
}
