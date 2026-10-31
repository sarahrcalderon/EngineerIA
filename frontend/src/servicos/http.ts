export async function obterJson(
  caminho: string,
  sinal?: AbortSignal,
): Promise<unknown> {
  const base = import.meta.env.VITE_API_URL;

  if (!base) {
    throw new Error('Configure VITE_API_URL para conectar à API.');
  }

  const resposta = await fetch(`${base.replace(/\/$/, '')}${caminho}`, {
    headers: { Accept: 'application/json' },
    signal: sinal
      ? AbortSignal.any([sinal, AbortSignal.timeout(5000)])
      : AbortSignal.timeout(5000),
  });

  if (!resposta.ok) {
    throw new Error('Não foi possível consultar o serviço.');
  }

  return resposta.json();
}
