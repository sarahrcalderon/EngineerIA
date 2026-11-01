import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';

const resposta = {
  estado: 'fundamentada',
  resposta: 'Resposta fictícia confirmada.',
  referencias: [
    { tipo: 'politica', titulo: 'Políticas fictícias — página 3', pagina: 3 },
  ],
  requisicao_id: '00000000-0000-4000-8000-000000000001',
};
type RespostaSimulada = {
  ok: boolean;
  status?: number;
  json: () => Promise<unknown>;
};

function prepararApi(
  enviar: (opcoes?: RequestInit) => Promise<RespostaSimulada> = async () => ({
    ok: true,
    status: 200,
    json: async () => resposta,
  }),
) {
  const consulta = vi.fn(async (endereco: string, opcoes?: RequestInit) => {
    if (endereco.endsWith('/api/saude'))
      return {
        ok: true,
        json: async () => ({
          estado: 'disponivel',
          servico: 'Emporio IA',
          versao: '0.1.0',
        }),
      };
    if (endereco.endsWith('/disponibilidade'))
      return {
        ok: true,
        json: async () => ({
          api: 'disponivel',
          modelo: 'indisponivel',
          limite_mensagem: 1000,
        }),
      };
    return enviar(opcoes);
  });
  vi.stubGlobal('fetch', consulta);
  return consulta;
}
function digitar(texto: string) {
  fireEvent.change(screen.getByRole('textbox', { name: 'Sua pergunta' }), {
    target: { value: texto },
  });
}
function envios(consulta: ReturnType<typeof prepararApi>) {
  return consulta.mock.calls.filter(([endereco]) =>
    endereco.endsWith('/mensagens'),
  );
}

describe('página de atendimento', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://127.0.0.1:8000');
    localStorage.clear();
    delete document.documentElement.dataset.tema;
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('apresenta identidade, sugestões e estados reais separados', async () => {
    prepararApi();
    render(<App />);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Atendimento do Empório',
    );
    expect(await screen.findByText('API disponível')).toBeVisible();
    expect(await screen.findByText('Atendimento indisponível')).toBeVisible();
    expect(
      screen.getByRole('button', { name: /Explore as categorias/ }),
    ).toBeVisible();
    expect(screen.getByText(/Cada pergunta é independente/)).toBeVisible();
  });

  it('sugestão preenche o campo sem enviar automaticamente', async () => {
    const consulta = prepararApi();
    render(<App />);
    fireEvent.click(
      screen.getByRole('button', { name: /Explore as categorias/ }),
    );
    expect(screen.getByRole('textbox')).toHaveValue(
      'Quais categorias estão cadastradas?',
    );
    expect(screen.getByRole('textbox')).toHaveFocus();
    expect(envios(consulta)).toHaveLength(0);
  });

  it('bloqueia pergunta vazia ou excessiva', () => {
    const consulta = prepararApi();
    render(<App />);
    expect(
      screen.getByRole('button', { name: 'Enviar pergunta' }),
    ).toBeDisabled();
    digitar('   ');
    expect(
      screen.getByRole('button', { name: 'Enviar pergunta' }),
    ).toBeDisabled();
    digitar('x'.repeat(1001));
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
    expect(
      screen.getByRole('button', { name: 'Enviar pergunta' }),
    ).toBeDisabled();
    expect(envios(consulta)).toHaveLength(0);
  });

  it('envia com Enter e apresenta referências fornecidas pela API', async () => {
    const consulta = prepararApi();
    render(<App />);
    digitar('Pergunta fictícia');
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    expect(
      await screen.findByText('Resposta fictícia confirmada.'),
    ).toBeVisible();
    expect(
      screen.getByText('Fonte: Políticas fictícias — página 3'),
    ).toBeVisible();
    expect(envios(consulta)).toHaveLength(1);
    expect(
      screen.getByRole('log', { name: 'Histórico da conversa' }),
    ).toBeVisible();
  });

  it('Shift + Enter e composição de texto não enviam', () => {
    const consulta = prepararApi();
    render(<App />);
    digitar('Primeira linha');
    fireEvent.keyDown(screen.getByRole('textbox'), {
      key: 'Enter',
      shiftKey: true,
    });
    fireEvent.keyDown(screen.getByRole('textbox'), {
      key: 'Enter',
      isComposing: true,
    });
    expect(envios(consulta)).toHaveLength(0);
  });

  it('carregamento é honesto e bloqueia envios duplicados', async () => {
    prepararApi(() => new Promise(() => {}));
    render(<App />);
    digitar('Teste');
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    expect(
      await screen.findByText('Consultando as fontes autorizadas…'),
    ).toBeVisible();
    expect(
      screen.getByRole('button', { name: 'Interromper consulta' }),
    ).toBeVisible();
    expect(screen.getAllByLabelText('Sua mensagem')).toHaveLength(1);
  });

  it.each([
    [503, 'modelo_indisponivel', /modelo local está indisponível/],
    [429, 'ocupado', /Há muitas consultas/],
    [504, 'timeout', /demorou além do limite/],
    [422, 'http', /Confira o conteúdo/],
    [502, 'resposta_modelo_invalida', /resposta inválida do modelo/],
    [502, 'geracao_interrompida', /limite de geração/],
  ])('trata erro HTTP %s sem stack trace', async (status, codigo, esperado) => {
    prepararApi(
      async () =>
        ({ ok: false, status, json: async () => ({ codigo }) }) as never,
    );
    render(<App />);
    digitar('Teste');
    fireEvent.click(screen.getByRole('button', { name: 'Enviar pergunta' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(esperado);
    expect(screen.getAllByLabelText('Sua mensagem')).toHaveLength(1);
  });

  it('trata falha de rede e resposta inválida', async () => {
    prepararApi(async () => {
      throw new TypeError('detalhe interno');
    });
    render(<App />);
    digitar('Teste');
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'A API não respondeu',
    );
    expect(screen.queryByText('detalhe interno')).not.toBeInTheDocument();
  });

  it('mantém foco no campo após envio por botão e erro', async () => {
    prepararApi(async () => {
      throw new TypeError('falha sintética');
    });
    render(<App />);
    digitar('Consulta fictícia');
    const enviar = screen.getByRole('button', { name: 'Enviar pergunta' });
    enviar.focus();
    fireEvent.click(enviar);
    await screen.findByRole('alert');
    expect(screen.getByRole('textbox')).toHaveFocus();
  });

  it('permite interromper a requisição via AbortController', async () => {
    const consulta = prepararApi(
      (opcoes) =>
        new Promise((_resolver, rejeitar) => {
          opcoes?.signal?.addEventListener('abort', () =>
            rejeitar(new DOMException('cancelada', 'AbortError')),
          );
        }),
    );
    render(<App />);
    digitar('Teste');
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    fireEvent.click(
      await screen.findByRole('button', { name: 'Interromper consulta' }),
    );
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Consulta interrompida',
    );
    expect(envios(consulta)[0][1]?.signal?.aborted).toBe(true);
  });

  it('nova conversa limpa memória e retorna o foco ao campo', async () => {
    prepararApi();
    render(<App />);
    digitar('Teste');
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    await screen.findByText('Resposta fictícia confirmada.');
    fireEvent.click(
      screen.getAllByRole('button', { name: 'Nova conversa' })[0],
    );
    expect(
      screen.queryByText('Resposta fictícia confirmada.'),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveValue('');
    expect(screen.getByRole('textbox')).toHaveFocus();
  });

  it('não persiste mensagens e guarda somente a preferência visual', async () => {
    prepararApi();
    const gravar = vi.spyOn(Storage.prototype, 'setItem');
    render(<App />);
    digitar('Pergunta em memória');
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    await screen.findByText('Resposta fictícia confirmada.');
    expect(gravar).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Ativar tema escuro' }));
    await waitFor(() =>
      expect(document.documentElement.dataset.tema).toBe('escuro'),
    );
    expect(localStorage.getItem('emporio-tema')).toBe('escuro');
    expect(gravar).toHaveBeenCalledWith('emporio-tema', 'escuro');
  });

  it('respeita preferência visual salva', () => {
    localStorage.setItem('emporio-tema', 'escuro');
    prepararApi();
    render(<App />);
    expect(
      screen.getByRole('button', { name: 'Ativar tema claro' }),
    ).toBeVisible();
    expect(document.documentElement.dataset.tema).toBe('escuro');
  });

  it('HTML não é interpretado como código', async () => {
    prepararApi(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        ...resposta,
        resposta: '<img src=x onerror=alert(1)>',
      }),
    }));
    render(<App />);
    digitar('Teste');
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    expect(
      await screen.findByText('<img src=x onerror=alert(1)>'),
    ).toBeVisible();
    expect(document.querySelector('img[src="x"]')).toBeNull();
  });
});
