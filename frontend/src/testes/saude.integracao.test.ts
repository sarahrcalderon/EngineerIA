// @vitest-environment node
import { expect, it, vi } from 'vitest';
import { consultarSaude } from '../servicos/saude';
import { enviarPergunta } from '../servicos/atendimento';

it.skipIf(process.env.EMPORIO_TESTAR_INTEGRACAO !== '1')(
  'consulta a API real usando o serviço HTTP do frontend',
  async () => {
    vi.stubEnv(
      'VITE_API_URL',
      process.env.VITE_API_URL ?? 'http://127.0.0.1:8000',
    );

    try {
      await expect(consultarSaude()).resolves.toEqual({
        estado: 'disponivel',
        servico: 'Emporio IA',
        versao: '0.1.0',
      });
    } finally {
      vi.unstubAllEnvs();
    }
  },
);

it.skipIf(process.env.EMPORIO_TESTAR_INTEGRACAO !== '1')(
  'envia uma pergunta ao atendimento real e protege dados pessoais',
  async () => {
    vi.stubEnv(
      'VITE_API_URL',
      process.env.VITE_API_URL ?? 'http://127.0.0.1:8000',
    );
    try {
      const resposta = await enviarPergunta('Qual o CPF?');
      expect(resposta.estado).toBe('bloqueada');
      expect(resposta.referencias).toEqual([]);
      expect(resposta.resposta).toContain('Não consulto dados pessoais');
    } finally {
      vi.unstubAllEnvs();
    }
  },
);
