import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  consultarDisponibilidade,
  enviarPergunta,
  mensagemErro,
} from '../servicos/atendimento';
import { ErroHttp } from '../servicos/http';

const respostaValida = {
  estado: 'sem_evidencias',
  resposta: 'Sem evidência fictícia.',
  referencias: [],
  requisicao_id: '00000000-0000-4000-8000-000000000001',
};

describe('transporte de atendimento', () => {
  beforeEach(() => vi.stubEnv('VITE_API_URL', 'http://127.0.0.1:8000'));
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('envia somente a mensagem para FastAPI sem credenciais', async () => {
    const consulta = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => respostaValida });
    vi.stubGlobal('fetch', consulta);
    await enviarPergunta('Pergunta fictícia');
    expect(consulta).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/atendimento/mensagens',
      expect.objectContaining({
        method: 'POST',
        credentials: 'omit',
        body: JSON.stringify({ mensagem: 'Pergunta fictícia' }),
      }),
    );
  });

  it('aceita saudação social sem referências comerciais', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          ...respostaValida,
          estado: 'social',
          resposta: 'Olá!',
        }),
      }),
    );
    expect((await enviarPergunta('Olá')).estado).toBe('social');
  });

  it.each([
    {},
    { ...respostaValida, estado: 'inventado' },
    { ...respostaValida, resposta: '' },
    {
      ...respostaValida,
      referencias: [{ tipo: 'politica', titulo: 'Fonte', pagina: null }],
    },
    {
      ...respostaValida,
      referencias: [{ tipo: 'politica', titulo: 'Fonte', pagina: 999 }],
    },
    { ...respostaValida, requisicao_id: 123 },
  ])('recusa contrato inválido', async (resposta) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: async () => resposta }),
    );
    await expect(enviarPergunta('Teste')).rejects.toBeInstanceOf(ErroHttp);
  });

  it('não envia perguntas para URL externa', async () => {
    vi.stubEnv('VITE_API_URL', 'https://externo.example');
    const consulta = vi.fn();
    vi.stubGlobal('fetch', consulta);
    await expect(enviarPergunta('Teste')).rejects.toBeInstanceOf(ErroHttp);
    expect(consulta).not.toHaveBeenCalled();
  });

  it('separa saúde da API e disponibilidade do modelo', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          api: 'disponivel',
          modelo: 'indisponivel',
          limite_mensagem: 1000,
        }),
      }),
    );
    expect((await consultarDisponibilidade()).modelo).toBe('indisponivel');
  });

  it.each([
    [
      new ErroHttp(503, 'modelo_indisponivel'),
      'modelo local está indisponível',
    ],
    [new ErroHttp(429, 'ocupado'), 'Aguarde'],
    [new ErroHttp(504, 'timeout'), 'limite'],
    [new DOMException('demora', 'TimeoutError'), 'limite'],
    [new ErroHttp(422, 'http'), 'tamanho'],
    [new ErroHttp(502, 'resposta_invalida'), 'inválida'],
  ])('traduz erros sem expor detalhes', (erro, esperado) => {
    expect(mensagemErro(erro)).toContain(esperado);
  });
});
