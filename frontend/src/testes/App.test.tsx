import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';

const saude = { estado: 'disponivel', servico: 'Emporio IA', versao: '0.1.0' };

describe('página inicial', () => {
  beforeEach(() => vi.stubEnv('VITE_API_URL', 'http://localhost:8000'));
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('apresenta carregamento e disponibilidade após consultar a API', async () => {
    const consulta = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => saude });
    vi.stubGlobal('fetch', consulta);
    render(<App />);
    expect(screen.getByRole('status')).toHaveTextContent('Verificando conexão');
    expect(await screen.findByText('API disponível')).toBeVisible();
    expect(consulta).toHaveBeenCalledWith(
      'http://localhost:8000/api/saude',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(
      'Empório da Música',
    );
  });

  it('permite tentar novamente após erro de rede', async () => {
    const consulta = vi
      .fn()
      .mockRejectedValueOnce(new Error('rede'))
      .mockResolvedValueOnce({ ok: true, json: async () => saude });
    vi.stubGlobal('fetch', consulta);
    render(<App />);
    expect(await screen.findByText('API indisponível')).toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }));
    expect(await screen.findByText('API disponível')).toBeVisible();
  });

  it.each([
    { ok: false, json: async () => saude },
    { ok: true, json: async () => ({ estado: 'desconhecido' }) },
  ])(
    'trata respostas HTTP e contratos inválidos como indisponíveis',
    async (resposta) => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue(resposta));
      render(<App />);
      expect(await screen.findByText('API indisponível')).toBeVisible();
    },
  );

  it('trata ausência de configuração sem tentar uma URL implícita', async () => {
    vi.stubEnv('VITE_API_URL', '');
    const consulta = vi.fn();
    vi.stubGlobal('fetch', consulta);
    render(<App />);
    expect(await screen.findByText('API indisponível')).toBeVisible();
    expect(consulta).not.toHaveBeenCalled();
  });
});
