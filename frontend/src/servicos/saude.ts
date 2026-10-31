import type { RespostaSaude } from '../tipos/api';
import { obterJson } from './http';

export async function consultarSaude(
  sinal?: AbortSignal,
): Promise<RespostaSaude> {
  const resposta = await obterJson('/api/saude', sinal);

  if (
    typeof resposta !== 'object' ||
    resposta === null ||
    !('estado' in resposta) ||
    resposta.estado !== 'disponivel' ||
    !('servico' in resposta) ||
    typeof resposta.servico !== 'string' ||
    !('versao' in resposta) ||
    typeof resposta.versao !== 'string'
  ) {
    throw new Error('Resposta de saúde inválida.');
  }

  return {
    estado: resposta.estado,
    servico: resposta.servico,
    versao: resposta.versao,
  };
}
