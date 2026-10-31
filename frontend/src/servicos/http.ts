export class ErroHttp extends Error {
  constructor(
    public status: number,
    public codigo: string,
  ) {
    super('Não foi possível concluir a comunicação com a API.');
  }
}

interface OpcoesHttp {
  sinal?: AbortSignal;
  corpo?: object;
  timeout?: number;
}

export async function requisitarJson(
  caminho: string,
  opcoes: OpcoesHttp = {},
): Promise<unknown> {
  const base = import.meta.env.VITE_API_URL;

  if (!base) {
    throw new Error('Configure VITE_API_URL para conectar à API.');
  }

  const endereco = new URL(base);
  if (
    endereco.protocol !== 'http:' ||
    !['localhost', '127.0.0.1', '[::1]'].includes(endereco.hostname) ||
    endereco.username ||
    endereco.password ||
    endereco.search ||
    endereco.hash ||
    endereco.pathname !== '/'
  )
    throw new ErroHttp(0, 'configuracao');
  const tempo = AbortSignal.timeout(opcoes.timeout ?? 5000);
  const resposta = await fetch(`${endereco.origin}${caminho}`, {
    method: opcoes.corpo ? 'POST' : 'GET',
    headers: {
      Accept: 'application/json',
      ...(opcoes.corpo ? { 'Content-Type': 'application/json' } : {}),
    },
    credentials: 'omit',
    ...(opcoes.corpo ? { body: JSON.stringify(opcoes.corpo) } : {}),
    signal: opcoes.sinal ? AbortSignal.any([opcoes.sinal, tempo]) : tempo,
  });

  if (!resposta.ok) {
    let codigo = 'http';
    try {
      const erro: unknown = await resposta.json();
      if (
        typeof erro === 'object' &&
        erro !== null &&
        'codigo' in erro &&
        typeof erro.codigo === 'string'
      )
        codigo = erro.codigo;
    } catch {
      /* Detalhes internos de erros HTTP nunca são apresentados. */
    }
    throw new ErroHttp(resposta.status, codigo);
  }

  try {
    return await resposta.json();
  } catch {
    throw new ErroHttp(502, 'resposta_invalida');
  }
}

export async function obterJson(
  caminho: string,
  sinal?: AbortSignal,
): Promise<unknown> {
  return requisitarJson(caminho, { sinal });
}
